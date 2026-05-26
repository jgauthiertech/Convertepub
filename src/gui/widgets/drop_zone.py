"""Widget de glisser-déposer pour les fichiers ACSM."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget


class DropZone(QWidget):
    """Zone centrale qui accepte le drop de fichiers .acsm."""

    files_dropped = Signal(list)  # list[Path]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)

        self._title = QLabel("Glisse tes fichiers .acsm ici")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setStyleSheet("font-size: 18px; font-weight: 600;")

        self._hint = QLabel("ou clique pour les sélectionner")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setStyleSheet("color: #888; font-size: 13px;")

        layout.addStretch()
        layout.addWidget(self._title)
        layout.addWidget(self._hint)
        layout.addStretch()

        self._apply_idle_style()

    def _apply_idle_style(self) -> None:
        self.setStyleSheet(
            """
            DropZone {
                border: 2px dashed #888;
                border-radius: 12px;
                background: #fafafa;
            }
            """
        )

    def _apply_hover_style(self) -> None:
        self.setStyleSheet(
            """
            DropZone {
                border: 2px dashed #3478f6;
                border-radius: 12px;
                background: #e8f0fe;
            }
            """
        )

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._extract_acsm_paths(event):
            event.acceptProposedAction()
            self._apply_hover_style()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._apply_idle_style()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        paths = self._extract_acsm_paths(event)
        self._apply_idle_style()
        if paths:
            event.acceptProposedAction()
            self.files_dropped.emit(paths)
        else:
            event.ignore()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            paths, _ = QFileDialog.getOpenFileNames(
                self,
                "Choisir des fichiers ACSM",
                str(Path.home()),
                "Fichiers ACSM (*.acsm)",
            )
            if paths:
                self.files_dropped.emit([Path(p) for p in paths])
        super().mousePressEvent(event)

    @staticmethod
    def _extract_acsm_paths(event) -> list[Path]:
        if not event.mimeData().hasUrls():
            return []
        paths = []
        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue
            p = Path(url.toLocalFile())
            if p.is_file() and p.suffix.lower() == ".acsm":
                paths.append(p)
        return paths
