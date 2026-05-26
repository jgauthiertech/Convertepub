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
from src.i18n import t


_STEP_PROGRESS = {
    ConversionStep.PARSING: 10,
    ConversionStep.ACTIVATING: 25,
    ConversionStep.FULFILLING: 40,
    ConversionStep.DOWNLOADING: 70,
    ConversionStep.DECRYPTING: 90,
    ConversionStep.DONE: 100,
}

_STEP_KEY = {
    ConversionStep.PARSING: "step.parsing",
    ConversionStep.ACTIVATING: "step.activating",
    ConversionStep.FULFILLING: "step.fulfilling",
    ConversionStep.DOWNLOADING: "step.downloading",
    ConversionStep.DECRYPTING: "step.decrypting",
    ConversionStep.DONE: "step.done",
}

_ERROR_KEY = {
    "token_expired": "list.error_token_expired",
    "token_consumed": "list.error_token_consumed",
    "conversion_error": "list.error_conversion",
    "unexpected": "list.error_unexpected",
}


class ConversionListWidget(QTableWidget):
    """Une ligne par fichier ACSM, avec statut + barre de progression."""

    COL_FILE = 0
    COL_STATUS = 1
    COL_PROGRESS = 2

    def __init__(self, parent=None):
        super().__init__(0, 3, parent)
        self.setHorizontalHeaderLabels([
            t("list.col_file"),
            t("list.col_status"),
            t("list.col_progress"),
        ])
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
            self._set_status(row, t("list.status_pending"), 0)
            return

        row = self.rowCount()
        self.insertRow(row)
        self._row_by_name[name] = row

        file_item = QTableWidgetItem(name)
        file_item.setToolTip(str(acsm_path))
        self.setItem(row, self.COL_FILE, file_item)
        self.setItem(row, self.COL_STATUS, QTableWidgetItem(t("list.status_pending")))

        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(0)
        self.setCellWidget(row, self.COL_PROGRESS, bar)

    def update_progress(self, name: str, step: ConversionStep, detail: str) -> None:
        row = self._row_by_name.get(name)
        if row is None:
            return
        label = t(_STEP_KEY.get(step, "step.done"))
        percent = _STEP_PROGRESS.get(step, 0)
        if detail and step != ConversionStep.DONE:
            label = f"{label} — {detail}"
        self._set_status(row, label, percent)

    def mark_done(self, name: str, output_path: Path) -> None:
        row = self._row_by_name.get(name)
        if row is None:
            return
        item = self.item(row, self.COL_STATUS)
        if item is not None:
            item.setText(t("list.status_done", filename=output_path.name))
            item.setToolTip(str(output_path))
        bar = self.cellWidget(row, self.COL_PROGRESS)
        if isinstance(bar, QProgressBar):
            bar.setValue(100)

    def mark_failed(self, name: str, kind: str, message: str) -> None:
        row = self._row_by_name.get(name)
        if row is None:
            return
        item = self.item(row, self.COL_STATUS)
        if item is not None:
            item.setText(t(_ERROR_KEY.get(kind, "list.error_conversion")))
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
