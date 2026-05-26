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

from src.config import APP_VERSION
from src.i18n import t


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("about.title"))
        self.setMinimumWidth(480)
        self.setModal(True)

        title = QLabel(t("app.title"))
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version = QLabel(t("about.version", version=APP_VERSION))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #888;")

        tagline = QLabel(t("app.tagline"))
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color: #555; margin-top: 12px;")

        developed_by_text = t("about.developed_by")
        author_block = QLabel(
            f"<div style='text-align: center; margin-top: 24px;'>"
            f"<div style='font-size: 13px; color: #888;'>{developed_by_text}</div>"
            f"<div style='font-size: 16px; font-weight: 600; margin-top: 4px;'>"
            f"Julien Gauthier"
            f"</div>"
            f"<div style='margin-top: 10px;'>"
            f"<a href='mailto:iam@juliengauthier.org' style='color: #3478f6;'>"
            f"iam@juliengauthier.org"
            f"</a>"
            f"</div>"
            f"<div style='margin-top: 4px;'>"
            f"<a href='https://juliengauthier.org' style='color: #3478f6;'>"
            f"juliengauthier.org"
            f"</a>"
            f"</div>"
            f"</div>"
        )
        author_block.setTextFormat(Qt.TextFormat.RichText)
        author_block.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author_block.setOpenExternalLinks(True)
        author_block.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )

        credits = QLabel(
            f"<div style='font-size: 11px; color: #888; margin-top: 24px; "
            f"text-align: center;'>"
            f"{t('about.credits')}"
            f"</div>"
        )
        credits.setTextFormat(Qt.TextFormat.RichText)
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setOpenExternalLinks(True)
        credits.setWordWrap(True)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        for btn in buttons.buttons():
            btn.clicked.connect(self.accept)
            btn.setText(t("action.close"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 20)
        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(tagline)
        layout.addWidget(author_block)
        layout.addWidget(credits)
        layout.addStretch()
        layout.addWidget(buttons)
