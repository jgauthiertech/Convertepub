"""Tableau qui affiche les conversions en cours et terminées."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
)

from src.core.converter import ConversionStep

_STEP_LABELS = {
    ConversionStep.PARSING: ("Lecture ACSM", 10),
    ConversionStep.ACTIVATING: ("Activation Adobe", 25),
    ConversionStep.FULFILLING: ("Demande au serveur", 40),
    ConversionStep.DOWNLOADING: ("Téléchargement", 70),
    ConversionStep.DECRYPTING: ("Retrait du DRM", 90),
    ConversionStep.DONE: ("Terminé", 100),
}


class ConversionListWidget(QTableWidget):
    """Une ligne par fichier ACSM, avec statut + barre de progression."""

    COL_FILE = 0
    COL_STATUS = 1
    COL_PROGRESS = 2

    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels(["Fichier", "Statut", "Progression"])
        self.verticalHeader().setVisible(False)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.horizontalHeader()
        header.setSectionResizeMode(self.COL_FILE, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_PROGRESS, QHeaderView.ResizeMode.Fixed)
        self.setColumnWidth(self.COL_PROGRESS, 200)

        self._row_by_name: dict[str, int] = {}

    def add_pending(self, acsm_path: Path) -> None:
        name = acsm_path.name
        if name in self._row_by_name:
            row = self._row_by_name[name]
            self._set_status(row, "En attente", 0)
            return

        row = self.rowCount()
        self.insertRow(row)
        self._row_by_name[name] = row

        file_item = QTableWidgetItem(name)
        file_item.setToolTip(str(acsm_path))
        self.setItem(row, self.COL_FILE, file_item)
        self.setItem(row, self.COL_STATUS, QTableWidgetItem("En attente"))

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        self.setCellWidget(row, self.COL_PROGRESS, bar)

    def update_progress(self, name: str, step: ConversionStep, detail: str) -> None:
        row = self._row_by_name.get(name)
        if row is None:
            return
        label, percent = _STEP_LABELS.get(step, (step.value, 0))
        if detail and step != ConversionStep.DONE:
            label = f"{label} — {detail}"
        self._set_status(row, label, percent)

    def mark_done(self, name: str, output_path: Path) -> None:
        row = self._row_by_name.get(name)
        if row is None:
            return
        item = self.item(row, self.COL_STATUS)
        if item is not None:
            item.setText(f"OK — {output_path.name}")
            item.setToolTip(str(output_path))
        bar = self.cellWidget(row, self.COL_PROGRESS)
        if isinstance(bar, QProgressBar):
            bar.setValue(100)

    def mark_failed(self, name: str, kind: str, message: str) -> None:
        row = self._row_by_name.get(name)
        if row is None:
            return
        kind_labels = {
            "token_expired": "Token expiré",
            "token_consumed": "Token déjà utilisé",
            "conversion_error": "Erreur",
            "unexpected": "Erreur inattendue",
        }
        item = self.item(row, self.COL_STATUS)
        if item is not None:
            item.setText(kind_labels.get(kind, "Erreur"))
            item.setToolTip(message)
            item.setForeground(Qt.GlobalColor.darkRed)
        bar = self.cellWidget(row, self.COL_PROGRESS)
        if isinstance(bar, QProgressBar):
            bar.setValue(0)

    def _set_status(self, row: int, label: str, percent: int) -> None:
        item = self.item(row, self.COL_STATUS)
        if item is not None:
            item.setText(label)
        bar = self.cellWidget(row, self.COL_PROGRESS)
        if isinstance(bar, QProgressBar):
            bar.setValue(percent)
