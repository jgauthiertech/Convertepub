"""Dialog des paramètres : dossier de sortie + accès aux logs."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Paramètres")
        self.setMinimumWidth(520)

        form = QFormLayout()

        output_row = QHBoxLayout()
        self._output_field = QLineEdit(str(get_output_dir()))
        browse_btn = QPushButton("Parcourir…")
        browse_btn.clicked.connect(self._browse_output_dir)
        output_row.addWidget(self._output_field, 1)
        output_row.addWidget(browse_btn)
        form.addRow("Dossier de sortie :", output_row)

        logs_row = QHBoxLayout()
        logs_btn = QPushButton(str(config.logs_dir()))
        logs_btn.setFlat(True)
        logs_btn.setStyleSheet("text-align: left; color: #3478f6;")
        logs_btn.clicked.connect(lambda: _open_path(config.logs_dir()))
        logs_row.addWidget(logs_btn, 1)
        form.addRow("Logs :", logs_row)

        activations_row = QHBoxLayout()
        act_btn = QPushButton(str(config.activations_dir()))
        act_btn.setFlat(True)
        act_btn.setStyleSheet("text-align: left; color: #3478f6;")
        act_btn.clicked.connect(lambda: _open_path(config.activations_dir()))
        activations_row.addWidget(act_btn, 1)
        form.addRow("Activations Adobe :", activations_row)

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
            self, "Choisir le dossier de sortie", self._output_field.text()
        )
        if path:
            self._output_field.setText(path)

    def _on_accept(self) -> None:
        output_dir = Path(self._output_field.text()).expanduser()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            QMessageBox.warning(
                self, "Dossier invalide",
                f"Impossible de créer ce dossier :\n{exc}",
            )
            return
        set_output_dir(output_dir)
        self.accept()


def _open_path(path: Path) -> None:
    """Ouvre un dossier dans l'explorateur Windows."""
    import os, subprocess
    path.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", str(path)])
