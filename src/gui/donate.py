"""Bandeau de don permanent + dialog de remerciement après conversion."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

DONATION_URL = "https://revolut.me/datadump"
DONATION_LABEL = "revolut.me/datadump"


class DonationBanner(QWidget):
    """Petit bandeau cliquable, visible en permanence en bas de la fenêtre."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        label = QLabel(
            f"Convertepub t'aide ? "
            f"<a href='{DONATION_URL}' style='color: #d63384; "
            f"text-decoration: none; font-weight: 600;'>"
            f"Soutiens le projet → {DONATION_LABEL}"
            f"</a>"
        )
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        label.setOpenExternalLinks(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            "QLabel { padding: 8px; background: #fff4f8;"
            " border-top: 1px solid #ffd3e2; color: #555; }"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)


class ThanksDialog(QDialog):
    """Apparaît après une conversion réussie pour proposer de soutenir l'auteur."""

    def __init__(self, parent=None, book_title: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Conversion réussie")
        self.setMinimumWidth(420)
        self.setModal(True)

        header = QLabel("C'est super, merci !")
        f = QFont()
        f.setPointSize(18)
        f.setBold(True)
        header.setFont(f)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #d63384;")

        subtitle_text = "Ton livre est prêt à être envoyé sur ta liseuse."
        if book_title:
            subtitle_text = f"« {book_title} » est prêt à être envoyé sur ta liseuse."
        subtitle = QLabel(subtitle_text)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #555; margin-top: 8px;")
        subtitle.setWordWrap(True)

        body = QLabel(
            f"<div style='text-align: center; margin-top: 20px;'>"
            f"Si Convertepub te rend service, tu peux soutenir le développement"
            f" avec un café (ou plus) :"
            f"<div style='margin-top: 16px;'>"
            f"<a href='{DONATION_URL}' style='color: #d63384; "
            f"font-size: 16px; font-weight: 600; text-decoration: none;'>"
            f"→ {DONATION_LABEL}"
            f"</a>"
            f"</div>"
            f"</div>"
        )
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setOpenExternalLinks(True)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        for btn in buttons.buttons():
            btn.clicked.connect(self.accept)
            btn.setText("Fermer")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 20)
        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addWidget(body)
        layout.addStretch()
        layout.addWidget(buttons)
