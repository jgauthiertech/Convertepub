"""Chemins de configuration globaux pour Convertepub."""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Convertepub"
APP_VERSION = "0.1.1"


def _local_app_data() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base)
    return Path.home() / ".local" / "share"


def app_data_dir() -> Path:
    path = _local_app_data() / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def activations_dir() -> Path:
    path = app_data_dir() / "activations"
    path.mkdir(parents=True, exist_ok=True)
    return path


def logs_dir() -> Path:
    path = app_data_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def history_file() -> Path:
    return app_data_dir() / "history.json"


def settings_file() -> Path:
    return app_data_dir() / "settings.json"


def default_output_dir() -> Path:
    return Path.home() / "Documents" / APP_NAME
