"""Setup centralisé du logging Convertepub.

Le moindre log doit atterrir dans %LOCALAPPDATA%\\Convertepub\\logs\\convertepub.log,
peu importe que l'app tourne en mode GUI windowed (sys.stdout=None) ou en CLI.
C'est le seul moyen de diagnostiquer les bugs chez les end-users à distance.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
from logging.handlers import RotatingFileHandler

from src import config

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 3


def _stdout_is_usable() -> bool:
    # Sous PyInstaller --windowed, sys.stdout vaut None : écrire dedans casse.
    stream = sys.stdout
    if stream is None:
        return False
    try:
        stream.write("")
        stream.flush()
        return True
    except Exception:
        return False


def init_logging(verbose: bool = False) -> None:
    """Configure le root logger (idempotent) avec fichier + console (si dispo)."""
    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    root = logging.getLogger()
    for handler in list(root.handlers):
        root.removeHandler(handler)
        try:
            handler.close()
        except Exception:
            pass
    root.setLevel(level)

    log_path = config.logs_dir() / "convertepub.log"
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    if _stdout_is_usable():
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    _log_session_header()


def _log_session_header() -> None:
    log = logging.getLogger("convertepub.session")
    log.info("=" * 60)
    log.info(
        "Convertepub %s | Python %s | %s %s (%s)",
        config.APP_VERSION,
        platform.python_version(),
        platform.system(),
        platform.release(),
        platform.machine(),
    )
    log.info("Frozen: %s | Executable: %s", getattr(sys, "frozen", False), sys.executable)
    log.info("Working dir: %s", os.getcwd())
    log.info("App data: %s", config.app_data_dir())
    log.info("=" * 60)
