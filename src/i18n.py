"""Système i18n simple : dictionnaire en mémoire + persistance dans settings.json.

Pour une app de cette taille (~70 chaînes), un dictionnaire Python est plus
pragmatique que Qt Linguist (.ts/.qm) — pas de génération de fichiers, pas
de compilation, lecture directe dans le code.

Usage :
    from src.i18n import t, set_language, get_language

    label.setText(t("drop_zone.title"))
    label.setText(t("conversion.status_ok", filename=path.name))
"""

from __future__ import annotations

import json
import locale
import logging
from pathlib import Path
from typing import Iterable

from src import config

log = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "fr"
SUPPORTED_LANGUAGES = ("fr", "en")

LANGUAGE_LABELS = {
    "fr": "Français",
    "en": "English",
}

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "fr": {
        # Application
        "app.title": "Convertepub",
        "app.tagline": "Convertit les fichiers ACSM (Fnac, Furet du Nord, Cultura,\nDecitre…) en EPUB lisibles sur n'importe quelle liseuse.",

        # Menus
        "menu.file": "&Fichier",
        "menu.file.open": "&Ouvrir des fichiers ACSM…",
        "menu.file.open_output": "Ouvrir le dossier de &sortie",
        "menu.file.settings": "&Paramètres…",
        "menu.file.quit": "&Quitter",
        "menu.help": "&Aide",
        "menu.help.about": "À &propos",
        "menu.help.donate": "&Soutenir le projet…",

        # Drop zone
        "drop_zone.title": "Glisse tes fichiers .acsm ici",
        "drop_zone.hint": "ou clique pour les sélectionner",
        "drop_zone.file_picker_title": "Choisir des fichiers ACSM",
        "drop_zone.file_picker_filter": "Fichiers ACSM (*.acsm)",

        # Liste de conversion
        "list.col_file": "Fichier",
        "list.col_status": "Statut",
        "list.col_progress": "Progression",
        "list.status_pending": "En attente",
        "list.status_done": "OK — {filename}",
        "list.error_token_expired": "Token expiré",
        "list.error_token_consumed": "Token déjà utilisé",
        "list.error_conversion": "Erreur",
        "list.error_unexpected": "Erreur inattendue",

        # Étapes de conversion
        "step.parsing": "Lecture ACSM",
        "step.activating": "Activation Adobe",
        "step.fulfilling": "Demande au serveur",
        "step.downloading": "Téléchargement",
        "step.decrypting": "Retrait du DRM",
        "step.done": "Terminé",

        # Boutons / actions
        "action.open_output_dir": "Ouvrir le dossier de sortie",
        "action.browse": "Parcourir…",
        "action.close": "Fermer",
        "action.later": "Plus tard",

        # Statusbar
        "status.output_dir": "Sortie : {path}",

        # Paramètres
        "settings.title": "Paramètres",
        "settings.output_dir": "Dossier de sortie :",
        "settings.logs": "Logs :",
        "settings.activations": "Activations Adobe :",
        "settings.language": "Langue :",
        "settings.invalid_dir_title": "Dossier invalide",
        "settings.invalid_dir_msg": "Impossible de créer ce dossier :\n{error}",
        "settings.pick_output_dir": "Choisir le dossier de sortie",

        # À propos
        "about.title": "À propos de Convertepub",
        "about.version": "Version {version}",
        "about.developed_by": "Développé par",
        "about.credits": (
            "Pile ADEPT tirée de "
            "<a href='https://github.com/Leseratte10/acsm-calibre-plugin' "
            "style='color: #777;'>acsm-calibre-plugin</a> (Leseratte10)<br/>"
            "et "
            "<a href='https://github.com/noDRM/DeDRM_tools' "
            "style='color: #777;'>DeDRM_tools</a> (Apprentice Alf / noDRM).<br/><br/>"
            "Application sous licence GPL-3.0."
        ),

        # Donation banner
        "donate.banner": "Convertepub t'aide ? Soutiens le projet → ",

        # Startup donation popup
        "donate.startup.title": "Soutenir Convertepub",
        "donate.startup.header": "Bienvenue dans Convertepub",
        "donate.startup.body": "Cette application est libre et gratuite.<br/>Si elle te rend service, tu peux soutenir son développement :",

        # Thanks dialog (post-conversion)
        "thanks.title": "Conversion réussie",
        "thanks.header": "C'est super, merci !",
        "thanks.subtitle_with_book": "« {book} » est prêt à être envoyé sur ta liseuse.",
        "thanks.subtitle_generic": "Ton livre est prêt à être envoyé sur ta liseuse.",
        "thanks.body": "Si Convertepub te rend service, tu peux soutenir le développement avec un café (ou plus) :",
    },
    "en": {
        # Application
        "app.title": "Convertepub",
        "app.tagline": "Converts ACSM files (Fnac, Furet du Nord, Cultura,\nDecitre…) into EPUBs readable on any e-reader.",

        # Menus
        "menu.file": "&File",
        "menu.file.open": "&Open ACSM files…",
        "menu.file.open_output": "Open output &folder",
        "menu.file.settings": "&Settings…",
        "menu.file.quit": "&Quit",
        "menu.help": "&Help",
        "menu.help.about": "&About",
        "menu.help.donate": "&Support the project…",

        # Drop zone
        "drop_zone.title": "Drop your .acsm files here",
        "drop_zone.hint": "or click to select them",
        "drop_zone.file_picker_title": "Choose ACSM files",
        "drop_zone.file_picker_filter": "ACSM files (*.acsm)",

        # Conversion list
        "list.col_file": "File",
        "list.col_status": "Status",
        "list.col_progress": "Progress",
        "list.status_pending": "Pending",
        "list.status_done": "OK — {filename}",
        "list.error_token_expired": "Token expired",
        "list.error_token_consumed": "Token already used",
        "list.error_conversion": "Error",
        "list.error_unexpected": "Unexpected error",

        # Conversion steps
        "step.parsing": "Reading ACSM",
        "step.activating": "Adobe activation",
        "step.fulfilling": "Server request",
        "step.downloading": "Downloading",
        "step.decrypting": "Removing DRM",
        "step.done": "Done",

        # Buttons / actions
        "action.open_output_dir": "Open output folder",
        "action.browse": "Browse…",
        "action.close": "Close",
        "action.later": "Later",

        # Statusbar
        "status.output_dir": "Output: {path}",

        # Settings
        "settings.title": "Settings",
        "settings.output_dir": "Output folder:",
        "settings.logs": "Logs:",
        "settings.activations": "Adobe activations:",
        "settings.language": "Language:",
        "settings.invalid_dir_title": "Invalid folder",
        "settings.invalid_dir_msg": "Could not create this folder:\n{error}",
        "settings.pick_output_dir": "Choose output folder",

        # About
        "about.title": "About Convertepub",
        "about.version": "Version {version}",
        "about.developed_by": "Developed by",
        "about.credits": (
            "ADEPT stack taken from "
            "<a href='https://github.com/Leseratte10/acsm-calibre-plugin' "
            "style='color: #777;'>acsm-calibre-plugin</a> (Leseratte10)<br/>"
            "and "
            "<a href='https://github.com/noDRM/DeDRM_tools' "
            "style='color: #777;'>DeDRM_tools</a> (Apprentice Alf / noDRM).<br/><br/>"
            "Application licensed under GPL-3.0."
        ),

        # Donation banner
        "donate.banner": "Convertepub helps you? Support the project → ",

        # Startup donation popup
        "donate.startup.title": "Support Convertepub",
        "donate.startup.header": "Welcome to Convertepub",
        "donate.startup.body": "This application is free and open-source.<br/>If it helps you, you can support its development:",

        # Thanks dialog (post-conversion)
        "thanks.title": "Conversion successful",
        "thanks.header": "Awesome, thank you!",
        "thanks.subtitle_with_book": "\"{book}\" is ready to be sent to your e-reader.",
        "thanks.subtitle_generic": "Your book is ready to be sent to your e-reader.",
        "thanks.body": "If Convertepub helps you, you can support its development with a coffee (or more):",
    },
}


_current_language: str | None = None


def _detect_system_language() -> str:
    """Devine la langue par défaut depuis la locale Windows."""
    try:
        lang_code, _ = locale.getlocale()
        if lang_code and lang_code.lower().startswith("fr"):
            return "fr"
    except (TypeError, ValueError):
        pass
    return "en"


def _settings_path() -> Path:
    return config.settings_file()


def _load_language_from_settings() -> str | None:
    path = _settings_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    lang = data.get("language")
    if lang in SUPPORTED_LANGUAGES:
        return lang
    return None


def _save_language_to_settings(lang: str) -> None:
    path = _settings_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (json.JSONDecodeError, OSError):
        data = {}
    data["language"] = lang
    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError as exc:
        log.warning("Impossible de sauvegarder la langue : %s", exc)


def get_language() -> str:
    """Renvoie la langue active (la charge depuis settings au premier appel)."""
    global _current_language
    if _current_language is None:
        _current_language = (
            _load_language_from_settings() or _detect_system_language()
        )
        if _current_language not in SUPPORTED_LANGUAGES:
            _current_language = DEFAULT_LANGUAGE
    return _current_language


def set_language(lang: str) -> None:
    """Change la langue active et la persiste."""
    global _current_language
    if lang not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Langue non supportée : {lang}")
    _current_language = lang
    _save_language_to_settings(lang)
    log.info("Langue active : %s", lang)


def t(key: str, **kwargs) -> str:
    """Renvoie la traduction d'une clé dans la langue active.

    Si la clé n'existe pas en langue active, on tombe sur le fr ; si elle
    n'existe nulle part, on renvoie la clé brute (pour faciliter le debug).
    """
    lang = get_language()
    text = _TRANSLATIONS.get(lang, {}).get(key)
    if text is None:
        text = _TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError) as exc:
            log.warning("Format failed for key '%s': %s", key, exc)
            return text
    return text


def supported_languages() -> Iterable[tuple[str, str]]:
    """Renvoie [(code, label), ...] pour le sélecteur de langue."""
    return [(code, LANGUAGE_LABELS[code]) for code in SUPPORTED_LANGUAGES]
