"""Dialog des paramètres : langue, dossier de sortie + accès aux logs."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from src import config
from src.i18n import get_language, set_language, supported_languages, t


def load_settings() -> dict:
    path = config.settings_file()
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(data: dict) -> None:
    config.settings_file().write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def get_output_dir() -> Path:
    raw = load_settings().get("output_dir")
    if raw:
        return Path(raw)
    return config.default_output_dir()


def set_output_dir(path: Path) -> None:
    data = load_settings()
    data["output_dir"] = str(path)
    save_settings(data)


class SettingsDialog(QDialog):
    """Renvoie QDialog.Accepted ; le caller peut consulter `language_changed`."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("settings.title"))
        self.setMinimumWidth(520)

        self.language_changed = False
        self._initial_language = get_language()

        form = QFormLayout()

        # Sélecteur de langue
        self._lang_combo = QComboBox()
        for code, label in supported_languages():
            self._lang_combo.addItem(label, code)
        current_idx = self._lang_combo.findData(self._initial_language)
        if current_idx >= 0:
            self._lang_combo.setCurrentIndex(current_idx)
        form.addRow(t("settings.language"), self._lang_combo)

        # Dossier de sortie
        output_row = QHBoxLayout()
        self._output_field = QLineEdit(str(get_output_dir()))
        browse_btn = QPushButton(t("action.browse"))
        browse_btn.clicked.connect(self._browse_output_dir)
        output_row.addWidget(self._output_field, 1)
        output_row.addWidget(browse_btn)
        form.addRow(t("settings.output_dir"), output_row)

        # Logs (juste un lien d'ouverture)
        logs_btn = QPushButton(str(config.logs_dir()))
        logs_btn.setFlat(True)
        logs_btn.setStyleSheet("text-align: left; color: #3478f6;")
        logs_btn.clicked.connect(lambda: _open_path(config.logs_dir()))
        form.addRow(t("settings.logs"), logs_btn)

        # Activations
        act_btn = QPushButton(str(config.activations_dir()))
        act_btn.setFlat(True)
        act_btn.setStyleSheet("text-align: left; color: #3478f6;")
        act_btn.clicked.connect(lambda: _open_path(config.activations_dir()))
        form.addRow(t("settings.activations"), act_btn)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch()
        layout.addWidget(buttons)

    def _browse_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, t("settings.pick_output_dir"), self._output_field.text()
        )
        if path:
            self._output_field.setText(path)

    def _on_accept(self) -> None:
        output_dir = Path(self._output_field.text()).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(
                self,
                t("settings.invalid_dir_title"),
                t("settings.invalid_dir_msg", error=exc),
            )
            return
        set_output_dir(output_dir)

        new_lang = self._lang_combo.currentData()
        if new_lang and new_lang != self._initial_language:
            set_language(new_lang)
            self.language_changed = True

        self.accept()


def _open_path(path: Path) -> None:
    """Ouvre un dossier dans l'explorateur Windows."""
    import os, subprocess
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(path)])
