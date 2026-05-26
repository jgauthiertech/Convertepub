"""Parse minimal d'un fichier ACSM (Adobe Content Server Message).

Extrait les métadonnées du livre et le type de transaction pour permettre :
- un nommage propre du fichier de sortie
- une détection de l'expiration du token avant de tenter le fulfillment
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from lxml import etree

NS_ADEPT = "http://ns.adobe.com/adept"
NS_DC = "http://purl.org/dc/elements/1.1/"

_WINDOWS_FORBIDDEN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass(frozen=True)
class AcsmMetadata:
    title: str
    author: str | None
    publisher: str | None
    identifier: str | None
    format: str | None
    fulfillment_type: str | None
    purchase: datetime | None
    expiration: datetime | None

    @property
    def is_expired(self) -> bool:
        if self.expiration is None:
            return False
        return datetime.now(timezone.utc) > self.expiration

    @property
    def is_epub(self) -> bool:
        return (self.format or "").lower().startswith("application/epub")

    def suggested_filename(self, extension: str = ".epub") -> str:
        """Nom de fichier propre pour Windows : '{auteur} - {titre}{ext}'."""
        parts = [self.author, self.title] if self.author else [self.title]
        base = " - ".join(p for p in parts if p)
        base = _sanitize_for_windows(base) or "livre"
        return f"{base}{extension}"


class AcsmParseError(Exception):
    pass


def parse_acsm(path: Path) -> AcsmMetadata:
    try:
        tree = etree.parse(str(path))
    except (etree.XMLSyntaxError, OSError) as exc:
        raise AcsmParseError(f"Impossible de lire l'ACSM : {exc}") from exc

    root = tree.getroot()
    if root.tag != f"{{{NS_ADEPT}}}fulfillmentToken":
        raise AcsmParseError(
            f"Format ACSM inattendu : racine est '{root.tag}', attendu fulfillmentToken"
        )

    meta_node = root.find(f"{{{NS_ADEPT}}}resourceItemInfo/{{{NS_ADEPT}}}metadata")
    title = _dc_text(meta_node, "title") or "Livre"
    author = _dc_text(meta_node, "creator")
    publisher = _dc_text(meta_node, "publisher")
    identifier = _dc_text(meta_node, "identifier")
    fmt = _dc_text(meta_node, "format")

    fulfillment_type = root.get("fulfillmentType")
    purchase = _parse_iso(_text(root, f"{{{NS_ADEPT}}}purchase"))
    expiration = _parse_iso(_text(root, f"{{{NS_ADEPT}}}expiration"))

    return AcsmMetadata(
        title=title,
        author=author,
        publisher=publisher,
        identifier=identifier,
        format=fmt,
        fulfillment_type=fulfillment_type,
        purchase=purchase,
        expiration=expiration,
    )


def _dc_text(parent, local_name: str) -> str | None:
    if parent is None:
        return None
    node = parent.find(f"{{{NS_DC}}}{local_name}")
    return node.text.strip() if node is not None and node.text else None


def _text(parent, tag: str) -> str | None:
    if parent is None:
        return None
    node = parent.find(tag)
    return node.text.strip() if node is not None and node.text else None


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    # ACSM uses RFC3339 with Z or +00:00 suffix
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _sanitize_for_windows(name: str) -> str:
    cleaned = _WINDOWS_FORBIDDEN.sub("", name).strip().rstrip(". ")
    return cleaned[:200]
