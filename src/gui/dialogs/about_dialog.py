"""Dialog 'À propos' — auteur, version, crédits, licence."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
)

APP_VERSION = "0.1.0"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos de Convertepub")
        self.setMinimumWidth(480)
        self.setModal(True)

        title = QLabel("Convertepub")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel(f"Version {APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #888;")

        tagline = QLabel(
            "Convertit les fichiers ACSM (Fnac, Furet du Nord, Cultura,\n"
            "Decitre…) en EPUB lisibles sur n'importe quelle liseuse."
        )
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color: #555; margin-top: 12px;")

        author_block = QLabel(
            "<div style='text-align: center; margin-top: 24px;'>"
            "<div style='font-size: 13px; color: #888;'>Développé par</div>"
            "<div style='font-size: 16px; font-weight: 600; margin-top: 4px;'>"
            "Julien Gauthier"
            "</div>"
            "<div style='margin-top: 10px;'>"
            "<a href='mailto:iam@juliengauthier.org' style='color: #3478f6;'>"
            "iam@juliengauthier.org"
            "</a>"
            "</div>"
            "<div style='margin-top: 4px;'>"
            "<a href='https://juliengauthier.org' style='color: #3478f6;'>"
            "juliengauthier.org"
            "</a>"
            "</div>"
            "</div>"
        )
        author_block.setTextFormat(Qt.TextFormat.RichText)
        author_block.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_block.setOpenExternalLinks(True)
        author_block.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )

        credits = QLabel(
            "<div style='font-size: 11px; color: #888; margin-top: 24px; "
            "text-align: center;'>"
            "Pile ADEPT tirée de "
            "<a href='https://github.com/Leseratte10/acsm-calibre-plugin' "
            "style='color: #777;'>acsm-calibre-plugin</a> (Leseratte10)<br/>"
            "et "
            "<a href='https://github.com/noDRM/DeDRM_tools' "
            "style='color: #777;'>DeDRM_tools</a> (Apprentice Alf / noDRM).<br/><br/>"
            "Application sous licence GPL-3.0."
            "</div>"
        )
        credits.setTextFormat(Qt.TextFormat.RichText)
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setOpenExternalLinks(True)
        credits.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        # Close button maps to "rejected" by default — also accept on click
        for btn in buttons.buttons():
            btn.clicked.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 20)
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(tagline)
        layout.addWidget(author_block)
        layout.addWidget(credits)
        layout.addStretch()
        layout.addWidget(buttons)
