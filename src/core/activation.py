"""Gestion des activations Adobe (anonymes) avec rotation transparente.

Chaque activation = un sous-dossier dans %LOCALAPPDATA%\\Convertepub\\activations\\
qui contient les fichiers attendus par libadobe (device.xml, activation.xml,
devicesalt) et un metadata.json (date, compteur d'usages, statut).

L'API publique :
    get_or_create_current() → ActivationSlot
    mark_full(slot)
    rotate() → nouvelle ActivationSlot active

Au moment d'utiliser libadobe, on appelle `slot.activate()` qui exécute
`libadobe.update_account_path(...)` pour rediriger les fichiers vers ce slot.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.core.adept import libadobe, libadobeAccount

log = logging.getLogger(__name__)

# ADE 3.0.1 — version par défaut utilisée pour les activations anonymes.
# Index 2 dans VAR_VER_SUPP_CONFIG_NAMES. Présent dans VAR_VER_ALLOWED_BUILD_IDS_AUTHORIZE.
ADE_VERSION_INDEX = 2

METADATA_FILE = "metadata.json"
DEVICE_FILES = ("device.xml", "activation.xml", "devicesalt")


class ActivationError(Exception):
    pass


@dataclass
class ActivationMetadata:
    slot_id: str
    created_at: str  # ISO 8601 UTC
    is_full: bool = False
    last_used_at: str | None = None
    use_count: int = 0

    @classmethod
    def fresh(cls, slot_id: str) -> ActivationMetadata:
        return cls(
            slot_id=slot_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class ActivationSlot:
    def __init__(self, directory: Path, metadata: ActivationMetadata):
        self.directory = directory
        self.metadata = metadata

    @property
    def slot_id(self) -> str:
        return self.metadata.slot_id

    @property
    def is_full(self) -> bool:
        return self.metadata.is_full

    @property
    def is_provisioned(self) -> bool:
        return all((self.directory / f).is_file() for f in DEVICE_FILES)

    def activate(self) -> None:
        """Redirige libadobe vers les fichiers de ce slot."""
        libadobe.update_account_path(str(self.directory))

    def save_metadata(self) -> None:
        (self.directory / METADATA_FILE).write_text(
            json.dumps(asdict(self.metadata), indent=2),
            encoding="utf-8",
        )

    def record_use(self) -> None:
        self.metadata.use_count += 1
        self.metadata.last_used_at = datetime.now(timezone.utc).isoformat()
        self.save_metadata()


def _list_slots() -> list[ActivationSlot]:
    root = config.activations_dir()
    slots: list[ActivationSlot] = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        meta_path = entry / METADATA_FILE
        if not meta_path.is_file():
            continue
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            metadata = ActivationMetadata(**data)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            log.warning("Activation %s : metadata illisible (%s), ignorée", entry.name, exc)
            continue
        slots.append(ActivationSlot(entry, metadata))
    return slots


def _next_slot_id() -> str:
    existing = _list_slots()
    next_index = len(existing) + 1
    return f"anon_{next_index:03d}_{int(time.time())}"


def _provision_anonymous(slot: ActivationSlot) -> None:
    """Exécute la dance d'activation Adobe en mode anonyme.

    Les fonctions de libadobe lisent/écrivent les chemins globaux configurés
    via update_account_path. On les active sur ce slot avant chaque étape.
    """
    slot.activate()

    libadobe.createDeviceKeyFile()

    if not libadobeAccount.createDeviceFile(True, ADE_VERSION_INDEX):
        raise ActivationError("createDeviceFile a échoué")

    success, resp = libadobeAccount.createUser(ADE_VERSION_INDEX, None)
    if not success:
        raise ActivationError(f"createUser a échoué : {resp}")

    success, resp = libadobeAccount.signIn("anonymous", "", "")
    if not success:
        raise ActivationError(f"signIn anonyme a échoué : {resp}")

    success, resp = libadobeAccount.activateDevice(ADE_VERSION_INDEX, None)
    if not success:
        raise ActivationError(f"activateDevice a échoué : {resp}")


def create_anonymous_activation() -> ActivationSlot:
    """Crée un nouveau slot anonyme prêt à fulfiller des ACSMs."""
    slot_id = _next_slot_id()
    directory = config.activations_dir() / slot_id
    directory.mkdir(parents=True, exist_ok=False)

    metadata = ActivationMetadata.fresh(slot_id)
    slot = ActivationSlot(directory, metadata)
    slot.save_metadata()

    log.info("Création d'une nouvelle activation anonyme : %s", slot_id)
    try:
        _provision_anonymous(slot)
    except Exception:
        log.exception("Activation anonyme %s : provisioning échoué, nettoyage", slot_id)
        # On ne supprime pas le dossier : il peut contenir des artefacts utiles
        # pour debug. On marque juste le slot comme inutilisable.
        metadata.is_full = True
        slot.save_metadata()
        raise

    if not slot.is_provisioned:
        raise ActivationError(
            f"Activation {slot_id} : fichiers device manquants après provisioning"
        )

    log.info("Activation anonyme %s opérationnelle", slot_id)
    return slot


def get_or_create_current() -> ActivationSlot:
    """Renvoie l'activation utilisable la plus récente ; en crée une si besoin."""
    available = [s for s in _list_slots() if not s.is_full and s.is_provisioned]
    if available:
        # On prend la plus récente (sorted par nom = ordre de création)
        slot = available[-1]
        slot.activate()
        log.debug("Activation existante réutilisée : %s", slot.slot_id)
        return slot
    return create_anonymous_activation()


def mark_full(slot: ActivationSlot) -> None:
    """Marque un slot comme épuisé. Le prochain get_or_create en créera un nouveau."""
    log.info("Activation %s marquée comme pleine", slot.slot_id)
    slot.metadata.is_full = True
    slot.save_metadata()


def rotate() -> ActivationSlot:
    """Marque l'activation courante comme pleine et en crée une nouvelle."""
    current = next(
        (s for s in _list_slots() if not s.is_full and s.is_provisioned),
        None,
    )
    if current is not None:
        mark_full(current)
    return create_anonymous_activation()


# Codes d'erreur Adobe qui signalent une saturation du DEVICE (et non du token).
# Ces erreurs peuvent être résolues en rotant l'activation côté client.
# Liste affinée par observation du serveur ACS Adobe/TEA.
QUOTA_ERROR_MARKERS = (
    "E_ACT_DEVICE_LIMIT_REACHED",
    "E_ADEPT_REQUEST_EXPIRED",
)

# Codes d'erreur indiquant que le TOKEN ACSM a déjà été consommé.
# Aucune rotation ne peut résoudre ça — l'utilisateur doit réexporter un
# nouvel ACSM depuis son espace Fnac/Furet.
# Important : E_LIC_LICENSE_SIGN_ERROR n'est PAS un token consommé, c'est
# une erreur de signature côté serveur — soit l'activation locale est cassée,
# soit l'horloge système est décalée, soit le backend crypto (oscrypto) a
# généré une mauvaise signature (ex: PyInstaller mal configuré).
TOKEN_CONSUMED_MARKERS = (
    "E_LIC_ALREADY_FULFILLED_BY_ANOTHER_USER",
)

# Codes d'erreur de signature : pas un token consommé, mais un problème
# local (activation cassée, horloge décalée, backend crypto défaillant).
# On tente une rotation pour repartir d'une activation propre avant d'abandonner.
SIGNATURE_ERROR_MARKERS = (
    "E_LIC_LICENSE_SIGN_ERROR",
)


def is_quota_error(reply_data: str | None) -> bool:
    if not reply_data:
        return False
    return any(marker in reply_data for marker in QUOTA_ERROR_MARKERS)


def is_token_consumed_error(reply_data: str | None) -> bool:
    if not reply_data:
        return False
    return any(marker in reply_data for marker in TOKEN_CONSUMED_MARKERS)


def is_signature_error(reply_data: str | None) -> bool:
    if not reply_data:
        return False
    return any(marker in reply_data for marker in SIGNATURE_ERROR_MARKERS)
