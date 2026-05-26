"""Worker Qt qui exécute une conversion ACSM→EPUB en arrière-plan."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from src.core.converter import (
    ConversionError,
    ConversionResult,
    ConversionStep,
    TokenAlreadyConsumedError,
    TokenExpiredError,
    convert,
)

log = logging.getLogger(__name__)


class WorkerSignals(QObject):
    progress = Signal(str, ConversionStep, str)  # acsm_name, step, detail
    finished = Signal(str, ConversionResult)     # acsm_name, result
    failed = Signal(str, str, str)                # acsm_name, error_kind, message


class ConversionWorker(QRunnable):
    """Une instance par fichier ACSM à convertir.

    Le QThreadPool exécute les workers, avec maxThreadCount=1 dans la GUI
    pour rester séquentiel (le serveur Adobe n'aime pas les requêtes
    concurrentes depuis le même device).
    """

    def __init__(self, acsm_path: Path, output_dir: Path):
        super().__init__()
        self.acsm_path = acsm_path
        self.output_dir = output_dir
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self) -> None:
        name = self.acsm_path.name

        def on_progress(step: ConversionStep, detail: str) -> None:
            self.signals.progress.emit(name, step, detail)

        try:
            result = convert(self.acsm_path, self.output_dir, on_progress=on_progress)
        except TokenExpiredError as exc:
            self.signals.failed.emit(name, "token_expired", str(exc))
        except TokenAlreadyConsumedError as exc:
            self.signals.failed.emit(name, "token_consumed", str(exc))
        except ConversionError as exc:
            self.signals.failed.emit(name, "conversion_error", str(exc))
        except Exception as exc:  # noqa: BLE001
            log.exception("Erreur inattendue lors de la conversion de %s", name)
            self.signals.failed.emit(name, "unexpected", f"{type(exc).__name__}: {exc}")
        else:
            self.signals.finished.emit(name, result)
