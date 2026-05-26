"""Fenêtre principale de Convertepub."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src import config
from src.core.converter import ConversionResult, ConversionStep
from src.gui.dialogs.settings_dialog import (
    SettingsDialog,
    get_output_dir,
)
from src.gui.widgets.conversion_list import ConversionListWidget
from src.gui.widgets.drop_zone import DropZone
from src.workers.conversion_worker import ConversionWorker

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Convertepub")
        self.resize(900, 600)

        self._thread_pool = QThreadPool.globalInstance()
        # Conversions séquentielles : on n'envoie qu'une requête à la fois
        # au serveur Adobe (pour éviter de saturer / se faire ratelimiter).
        self._thread_pool.setMaxThreadCount(1)

        # === Widgets ===
        self._drop_zone = DropZone()
        self._drop_zone.files_dropped.connect(self._enqueue_files)

        self._list = ConversionListWidget()

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._drop_zone)
        splitter.addWidget(self._list)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        # === Toolbar bas ===
        bottom = QWidget()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        open_btn = QPushButton("Ouvrir le dossier de sortie")
        open_btn.clicked.connect(self._open_output_dir)
        bottom_layout.addWidget(open_btn)
        bottom_layout.addStretch()

        # === Layout principal ===
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 0)
        layout.addWidget(splitter, 1)
        layout.addWidget(bottom)
        self.setCentralWidget(central)

        self._build_toolbar()

        self.setStatusBar(QStatusBar())
        self._refresh_status()

    def _build_toolbar(self) -> None:
        bar = QToolBar()
        bar.setMovable(False)
        bar.setStyleSheet("QToolBar { border: 0; padding: 4px; }")
        self.addToolBar(bar)

        settings_action = QAction("Paramètres", self)
        settings_action.triggered.connect(self._open_settings)
        bar.addAction(settings_action)

    def _refresh_status(self) -> None:
        self.statusBar().showMessage(f"Sortie : {get_output_dir()}")

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec():
            self._refresh_status()

    def _open_output_dir(self) -> None:
        import os
        path = get_output_dir()
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]

    def _enqueue_files(self, paths: list[Path]) -> None:
        output_dir = get_output_dir()
        for p in paths:
            self._list.add_pending(p)
            worker = ConversionWorker(p, output_dir)
            worker.signals.progress.connect(self._on_progress)
            worker.signals.finished.connect(self._on_finished)
            worker.signals.failed.connect(self._on_failed)
            self._thread_pool.start(worker)

    def _on_progress(self, name: str, step: ConversionStep, detail: str) -> None:
        self._list.update_progress(name, step, detail)

    def _on_finished(self, name: str, result: ConversionResult) -> None:
        self._list.mark_done(name, result.output_path)
        log.info("Conversion terminée : %s -> %s", name, result.output_path)

    def _on_failed(self, name: str, kind: str, message: str) -> None:
        self._list.mark_failed(name, kind, message)
        log.warning("Conversion échouée [%s] %s : %s", kind, name, message)


def run_app() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.logs_dir() / "convertepub.log", encoding="utf-8"),
        ],
    )

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)

    window = MainWindow()
    window.show()
    return app.exec()
