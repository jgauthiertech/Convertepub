"""Fenêtre principale de Convertepub."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QThreadPool, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src import config
from src.core.converter import ConversionResult, ConversionStep
from src.gui.dialogs.about_dialog import AboutDialog
from src.gui.dialogs.settings_dialog import (
    SettingsDialog,
    get_output_dir,
)
from src.gui.donate import (
    DONATION_URL,
    DonationBanner,
    StartupDonationDialog,
    ThanksDialog,
)
from src.gui.widgets.conversion_list import ConversionListWidget
from src.gui.widgets.drop_zone import DropZone
from src.i18n import t
from src.workers.conversion_worker import ConversionWorker

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(t("app.title"))
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
        open_btn = QPushButton(t("action.open_output_dir"))
        open_btn.clicked.connect(self._open_output_dir)
        bottom_layout.addWidget(open_btn)
        bottom_layout.addStretch()

        # === Bandeau de don (toujours visible) ===
        self._donation_banner = DonationBanner()

        # === Layout principal ===
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 0)
        layout.setSpacing(0)
        layout.addWidget(splitter, 1)
        layout.addWidget(bottom)
        layout.addWidget(self._donation_banner)
        self.setCentralWidget(central)

        self._build_menubar()

        self.setStatusBar(QStatusBar())
        self._refresh_status()

        # Popup de soutien au démarrage : on l'affiche après que la fenêtre
        # principale soit visible (sinon elle s'ouvre avant et c'est moche).
        QTimer.singleShot(300, self._show_startup_donation)

    # ----- Menu bar -----

    def _build_menubar(self) -> None:
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu(t("menu.file"))

        open_action = QAction(t("menu.file.open"), self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._pick_files)
        file_menu.addAction(open_action)

        open_out_action = QAction(t("menu.file.open_output"), self)
        open_out_action.triggered.connect(self._open_output_dir)
        file_menu.addAction(open_out_action)

        file_menu.addSeparator()

        settings_action = QAction(t("menu.file.settings"), self)
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        quit_action = QAction(t("menu.file.quit"), self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Help
        help_menu = menubar.addMenu(t("menu.help"))

        about_action = QAction(t("menu.help.about"), self)
        about_action.triggered.connect(self._open_about)
        help_menu.addAction(about_action)

        open_logs_action = QAction(t("menu.help.open_logs"), self)
        open_logs_action.triggered.connect(self._open_logs_dir)
        help_menu.addAction(open_logs_action)

        help_menu.addSeparator()

        donate_action = QAction(t("menu.help.donate"), self)
        donate_action.triggered.connect(self._open_donate_link)
        help_menu.addAction(donate_action)

    # ----- Actions -----

    def _refresh_status(self) -> None:
        self.statusBar().showMessage(t("status.output_dir", path=get_output_dir()))

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self)
        if dlg.exec():
            self._refresh_status()
            if dlg.language_changed:
                QMessageBox.information(
                    self,
                    t("settings.title"),
                    "Restart the application to apply the new language.\n"
                    "Redémarre l'application pour appliquer la nouvelle langue.",
                )

    def _open_about(self) -> None:
        AboutDialog(self).exec()

    def _open_donate_link(self) -> None:
        QDesktopServices.openUrl(QUrl(DONATION_URL))

    def _open_output_dir(self) -> None:
        import os
        path = get_output_dir()
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]

    def _open_logs_dir(self) -> None:
        import os
        path = config.logs_dir()
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            t("drop_zone.file_picker_title"),
            str(Path.home()),
            t("drop_zone.file_picker_filter"),
        )
        if paths:
            self._enqueue_files([Path(p) for p in paths])

    def _show_startup_donation(self) -> None:
        StartupDonationDialog(self).exec()

    # ----- Conversion handling -----

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
        ThanksDialog(self, book_title=result.metadata.title).exec()

    def _on_failed(self, name: str, kind: str, message: str) -> None:
        self._list.mark_failed(name, kind, message)
        log.warning("Conversion échouée [%s] %s : %s", kind, name, message)


def run_app() -> int:
    # Le logging est initialisé en amont par main.init_logging() — ici on
    # se contente de lancer la GUI.
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(config.APP_NAME)

    window = MainWindow()
    window.show()
    return app.exec()
