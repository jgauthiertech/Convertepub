"""Bandeau de don permanent + dialog de remerciement après conversion."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.i18n import t

DONATION_URL = "https://revolut.me/datadump"
DONATION_LABEL = "revolut.me/datadump"


def _link_html(font_size: int = 14) -> str:
    return (
        f"<a href='{DONATION_URL}' style='color: #d63384; "
        f"font-size: {font_size}px; font-weight: 600; text-decoration: none;'>"
        f"→ {DONATION_LABEL}"
        f"</a>"
    )


class DonationBanner(QWidget):
    """Petit bandeau cliquable, visible en permanence en bas de la fenêtre."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        label = QLabel(
            t("donate.banner")
            + f"<a href='{DONATION_URL}' style='color: #d63384; "
            f"text-decoration: none; font-weight: 600;'>{DONATION_LABEL}</a>"
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


class StartupDonationDialog(QDialog):
    """Apparaît au démarrage de l'app pour proposer de soutenir le projet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("donate.startup.title"))
        self.setMinimumWidth(440)
        self.setModal(True)

        header = QLabel(t("donate.startup.header"))
        f = QFont()
        f.setPointSize(17)
        f.setBold(True)
        header.setFont(f)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        body = QLabel(t("donate.startup.body"))
        body.setTextFormat(Qt.TextFormat.RichText)
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setStyleSheet("color: #555; margin-top: 12px;")
        body.setWordWrap(True)

        link = QLabel(
            f"<div style='text-align: center; margin-top: 18px;'>"
            f"{_link_html(17)}"
            f"</div>"
        )
        link.setTextFormat(Qt.TextFormat.RichText)
        link.setOpenExternalLinks(True)
        link.setAlignment(Qt.AlignmentFlag.AlignCenter)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        for btn in buttons.buttons():
            btn.clicked.connect(self.accept)
            btn.setText(t("action.later"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 20)
        layout.addWidget(header)
        layout.addWidget(body)
        layout.addWidget(link)
        layout.addStretch()
        layout.addWidget(buttons)


class ThanksDialog(QDialog):
    """Apparaît après une conversion réussie pour proposer de soutenir l'auteur."""

    def __init__(self, parent=None, book_title: str | None = None):
        super().__init__(parent)
        self.setWindowTitle(t("thanks.title"))
        self.setMinimumWidth(420)
        self.setModal(True)

        header = QLabel(t("thanks.header"))
        f = QFont()
        f.setPointSize(18)
        f.setBold(True)
        header.setFont(f)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: #d63384;")

        if book_title:
            subtitle_text = t("thanks.subtitle_with_book", book=book_title)
        else:
            subtitle_text = t("thanks.subtitle_generic")
        subtitle = QLabel(subtitle_text)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #555; margin-top: 8px;")
        subtitle.setWordWrap(True)

        body = QLabel(
            f"<div style='text-align: center; margin-top: 20px;'>"
            f"{t('thanks.body')}"
            f"<div style='margin-top: 16px;'>"
            f"{_link_html(16)}"
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
            btn.setText(t("action.close"))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 20)
        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addWidget(body)
        layout.addStretch()
        layout.addWidget(buttons)
