"""Orchestration du pipeline ACSM → EPUB sans DRM.

Étapes :
    1. parse_acsm — extrait les métadonnées et vérifie l'expiration
    2. fulfill — appelle le serveur Adobe, télécharge l'EPUB DRM
    3. dedrm — déchiffre l'EPUB avec la clé privée du device

En cas d'erreur de quota Adobe, le converter rotate automatiquement
l'activation et retente le fulfillment une fois.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from lxml import etree

from src.core import activation as activation_mod
from src.core.acsm_parser import AcsmMetadata, parse_acsm
from src.core.adept import libadobe, libadobeAccount, libadobeFulfill
from src.core.adept import ineptepub

log = logging.getLogger(__name__)


class ConversionStep(Enum):
    PARSING = "parsing"
    ACTIVATING = "activating"
    FULFILLING = "fulfilling"
    DOWNLOADING = "downloading"
    DECRYPTING = "decrypting"
    DONE = "done"


ProgressCallback = Callable[[ConversionStep, str], None]


class ConversionError(Exception):
    """Erreur générique de conversion."""


class TokenExpiredError(ConversionError):
    """Le fichier ACSM est trop vieux (token Adobe expiré)."""


class TokenAlreadyConsumedError(ConversionError):
    """Le token ACSM a déjà été utilisé pour télécharger ce livre.

    Le serveur Adobe/TEA refuse de re-fulfiller le même token, même depuis
    une autre activation. L'utilisateur doit réexporter un nouvel ACSM
    depuis son espace Fnac/Furet.
    """


class FulfillmentError(ConversionError):
    """Le serveur Adobe a refusé le fulfillment."""


class DownloadError(ConversionError):
    """Le téléchargement de l'EPUB DRM a échoué."""


class DecryptionError(ConversionError):
    """Le retrait du DRM a échoué."""


@dataclass(frozen=True)
class ConversionResult:
    metadata: AcsmMetadata
    output_path: Path


_NSMAP_ADEPT = "http://ns.adobe.com/adept"


def _ns(tag: str) -> str:
    return f"{{{_NSMAP_ADEPT}}}{tag}"


def convert(
    acsm_path: Path,
    output_dir: Path,
    on_progress: ProgressCallback | None = None,
) -> ConversionResult:
    """Convertit un .acsm en .epub sans DRM dans output_dir."""

    def progress(step: ConversionStep, detail: str = "") -> None:
        log.info("[%s] %s", step.value, detail or "")
        if on_progress is not None:
            on_progress(step, detail)

    output_dir.mkdir(parents=True, exist_ok=True)

    # === Étape 1 : parser l'ACSM ===
    progress(ConversionStep.PARSING, acsm_path.name)
    metadata = parse_acsm(acsm_path)
    if metadata.is_expired:
        raise TokenExpiredError(
            f"Le fichier ACSM a expiré le {metadata.expiration:%Y-%m-%d %H:%M %Z}. "
            "Réexporte le fichier depuis ton compte Fnac/Furet."
        )
    if not metadata.is_epub:
        raise ConversionError(
            f"Format non supporté : {metadata.format}. Seuls les EPUBs sont gérés."
        )

    output_path = output_dir / metadata.suggested_filename(".epub")

    with tempfile.TemporaryDirectory(prefix="convertepub_") as tmp_str:
        tmp_dir = Path(tmp_str)
        drm_epub = tmp_dir / "_drm.epub"

        # === Étape 2 + 3 : activation + fulfillment (avec rotation au besoin) ===
        reply_data = _fulfill_with_rotation(acsm_path, progress)

        # === Étape 4 : extraire download_url et rights.xml du reply ===
        download_url, rights_xml = _parse_fulfill_response(reply_data)

        # === Étape 5 : télécharger l'EPUB DRM ===
        progress(ConversionStep.DOWNLOADING, "")
        rc = libadobe.sendHTTPRequest_DL2FILE(download_url, str(drm_epub))
        if rc != 200 or not drm_epub.is_file():
            raise DownloadError(f"Téléchargement échoué (HTTP {rc})")

        # Adobe envoie l'EPUB chiffré ; on doit lui adjoindre rights.xml dans
        # META-INF/ pour que ineptepub puisse retrouver la clé de session.
        _embed_rights_xml(drm_epub, rights_xml)

        # === Étape 6 : retrait du DRM ===
        progress(ConversionStep.DECRYPTING, "")
        userkey = libadobeAccount.exportAccountEncryptionKeyBytes()
        if not userkey:
            raise DecryptionError("Clé d'activation introuvable dans activation.xml")

        rc = ineptepub.decryptBook(userkey, str(drm_epub), str(output_path))
        if rc != 0 or not output_path.is_file():
            raise DecryptionError(
                "Le déchiffrement de l'EPUB a échoué (clé device incompatible ?)"
            )

    progress(ConversionStep.DONE, str(output_path))
    return ConversionResult(metadata=metadata, output_path=output_path)


def _fulfill_with_rotation(
    acsm_path: Path,
    progress: Callable[[ConversionStep, str], None],
) -> str:
    """Fulfillment avec rotation transparente si l'activation est saturée."""
    progress(ConversionStep.ACTIVATING, "")
    slot = activation_mod.get_or_create_current()

    progress(ConversionStep.FULFILLING, slot.slot_id)
    success, reply_data = libadobeFulfill.fulfill(str(acsm_path))
    slot.record_use()

    if success:
        return reply_data

    # Token déjà consommé : aucune rotation ne peut aider, on échoue net.
    if activation_mod.is_token_consumed_error(reply_data):
        raise TokenAlreadyConsumedError(
            "Ce fichier ACSM a déjà été utilisé pour télécharger le livre. "
            "Réexporte un nouveau .acsm depuis ton espace Fnac/Furet."
        )

    # Erreur côté device (saturation) → rotation + retry une fois.
    if activation_mod.is_quota_error(reply_data):
        log.warning("Erreur de quota device, rotation de l'activation : %s", reply_data)
        progress(ConversionStep.ACTIVATING, "rotation")
        slot = activation_mod.rotate()

        progress(ConversionStep.FULFILLING, slot.slot_id + " (retry)")
        success, reply_data = libadobeFulfill.fulfill(str(acsm_path))
        slot.record_use()
        if success:
            return reply_data
        if activation_mod.is_token_consumed_error(reply_data):
            raise TokenAlreadyConsumedError(
                "Adobe a renvoyé une erreur de licence après rotation. "
                "Réexporte un nouveau .acsm depuis ton espace Fnac/Furet."
            )

    raise FulfillmentError(_humanize_fulfill_error(reply_data))


def _parse_fulfill_response(reply_data: str) -> tuple[str, str]:
    """Renvoie (download_url, rights_xml) depuis la réponse XML d'Adobe."""
    try:
        root = etree.fromstring(reply_data.encode("utf-8") if isinstance(reply_data, str) else reply_data)
    except etree.XMLSyntaxError as exc:
        raise FulfillmentError(f"Réponse Adobe illisible : {exc}") from exc

    info = root.find(f"./{_ns('fulfillmentResult')}/{_ns('resourceItemInfo')}")
    if info is None:
        raise FulfillmentError("Réponse Adobe sans resourceItemInfo")

    src_node = info.find(_ns("src"))
    license_node = info.find(_ns("licenseToken"))
    if src_node is None or license_node is None or not src_node.text:
        raise FulfillmentError("Réponse Adobe sans URL de téléchargement ou licenseToken")

    rights_xml = libadobeFulfill.buildRights(license_node)
    if not rights_xml:
        raise FulfillmentError("Impossible de générer rights.xml depuis le licenseToken")

    return src_node.text, rights_xml


def _embed_rights_xml(epub_path: Path, rights_xml: str) -> None:
    """Adjoint META-INF/rights.xml dans l'EPUB DRM (in-place)."""
    with zipfile.ZipFile(epub_path, "a") as zf:
        zf.writestr("META-INF/rights.xml", rights_xml)


def _humanize_fulfill_error(reply_data: str | None) -> str:
    if not reply_data:
        return "Le serveur Adobe a renvoyé une erreur sans message."
    text = reply_data.strip()
    # Le reply_data peut être du XML d'erreur ADEPT ou du texte humain — on
    # extrait quelque chose de lisible si possible.
    if "<error" in text or text.startswith("<"):
        try:
            root = etree.fromstring(text.encode("utf-8"))
            data = root.get("data") or root.findtext(_ns("data")) or ""
            return f"Adobe a refusé : {data or text[:200]}"
        except etree.XMLSyntaxError:
            pass
    return f"Adobe a refusé : {text[:300]}"
