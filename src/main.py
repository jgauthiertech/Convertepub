"""Point d'entrée Convertepub.

Sans argument : lance la GUI PySide6 (à implémenter).
Avec --cli FICHIER.acsm : convertit en mode console.
Avec --setup-only : crée juste une activation Adobe anonyme et quitte
                    (utile pour valider la connexion sans consommer un token ACSM).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Forcer UTF-8 sur stdout/stderr (Windows console est cp1252 par défaut)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from src import config
from src.core import activation as activation_mod
from src.core.converter import (
    ConversionError,
    ConversionStep,
    TokenAlreadyConsumedError,
    TokenExpiredError,
    convert,
)


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _cli_progress(step: ConversionStep, detail: str) -> None:
    markers = {
        ConversionStep.PARSING: "[1/5]",
        ConversionStep.ACTIVATING: "[2/5]",
        ConversionStep.FULFILLING: "[3/5]",
        ConversionStep.DOWNLOADING: "[4/5]",
        ConversionStep.DECRYPTING: "[5/5]",
        ConversionStep.DONE: " OK  ",
    }
    marker = markers.get(step, "  -  ")
    print(f"  {marker}  {step.value:<12} {detail}", flush=True)


def cmd_setup_only() -> int:
    print("Création d'une activation Adobe anonyme…", flush=True)
    try:
        slot = activation_mod.create_anonymous_activation()
    except Exception as exc:
        print(f"ÉCHEC : {exc}", file=sys.stderr)
        return 2
    print(f"OK — activation '{slot.slot_id}' provisionnée dans {slot.directory}")
    return 0


def cmd_convert(acsm_path: Path, output_dir: Path) -> int:
    if not acsm_path.is_file():
        print(f"Fichier introuvable : {acsm_path}", file=sys.stderr)
        return 2
    print(f"Conversion de '{acsm_path.name}' -> {output_dir}", flush=True)
    try:
        result = convert(acsm_path, output_dir, on_progress=_cli_progress)
    except TokenExpiredError as exc:
        print(f"\nÉCHEC — token expiré : {exc}", file=sys.stderr)
        return 3
    except TokenAlreadyConsumedError as exc:
        print(f"\nÉCHEC — token déjà utilisé : {exc}", file=sys.stderr)
        return 5
    except ConversionError as exc:
        print(f"\nÉCHEC — {exc}", file=sys.stderr)
        return 1
    print(f"\nLivre converti : {result.output_path}")
    return 0


def cmd_gui() -> int:
    try:
        from src.gui.main_window import run_app
    except ImportError as exc:
        print(
            "La GUI n'est pas encore implémentée. "
            "Utilise --cli pour le mode console.",
            file=sys.stderr,
        )
        print(f"  ({exc})", file=sys.stderr)
        return 4
    return run_app()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="convertepub",
        description="Convertit un fichier ACSM (Fnac, Furet du Nord, etc.) en EPUB sans DRM.",
    )
    parser.add_argument("--cli", metavar="FICHIER", help="Mode console : convertit ce fichier .acsm")
    parser.add_argument(
        "-o", "--output", metavar="DOSSIER",
        help=f"Dossier de sortie (défaut : {config.default_output_dir()})",
    )
    parser.add_argument(
        "--setup-only",
        action="store_true",
        help="Crée juste une activation Adobe anonyme et quitte",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Logs détaillés")
    args = parser.parse_args(argv)

    _setup_logging(args.verbose)

    if args.setup_only:
        return cmd_setup_only()

    if args.cli:
        output_dir = Path(args.output) if args.output else config.default_output_dir()
        return cmd_convert(Path(args.cli), output_dir)

    return cmd_gui()


if __name__ == "__main__":
    sys.exit(main())
