# Convertepub

Windows application that converts an `.acsm` file (Adobe Content Server Message) into a DRM-free EPUB. Designed for books purchased from **Fnac**, **Furet du Nord**, **Cultura**, **Decitre** and other French retailers using the **TEA Ebook** backend.

Use case: you buy an EPUB, your retailer hands you a `.acsm`, and your e-reader (e.g. a Kindle) doesn't support Adobe ADEPT DRM. Convertepub bridges the gap — the output EPUB can be read anywhere, including a Kindle via Send-to-Kindle.

## Author

**Julien Gauthier** — <iam@juliengauthier.org> — <https://juliengauthier.org>

## Features

- Drag-and-drop one or more `.acsm` files into the window
- **Anonymous** Adobe activation, fully automatic (no account required)
- Transparent activation rotation if the device gets saturated
- **Bilingual UI** — French / English, auto-detected from system locale, switchable from the Settings dialog
- Standard menu bar (File / Help) with keyboard shortcuts
- Permanent donation banner + post-conversion thank-you popup
- CLI mode for scripting (`--cli file.acsm --output out/`)
- Output is a standard EPUB readable in Calibre, Sigil, Kobo, Kindle (via Send-to-Kindle)…

## Usage

### GUI mode
```
python -m src.main
```

### CLI mode
```
python -m src.main --cli my_book.acsm --output ./out
```

### First Adobe activation (optional — test connectivity without consuming a token)
```
python -m src.main --setup-only
```

### Packaged executable
Download `Convertepub.exe` from the [Releases page](https://github.com/jgauthiertech/Convertepub/releases) — no Python or installation needed. On first launch, Windows SmartScreen will block the unsigned binary: click **More info → Run anyway**.

## Pipeline

```
book.acsm  →  [Adobe ADEPT fulfillment]  →  book.epub (DRM)  →  [DRM removal]  →  clean book.epub
```

## Tech stack

- **Python 3.11+** — no external binary, 100% Python
- **PySide6** for the GUI
- **acsm-calibre-plugin** (extracted modules) for ACSM fulfillment
- **DeDRM_tools / ineptepub** (extracted module) for ADEPT DRM removal
- **PyInstaller** for packaging into a standalone Windows `.exe`

## Local storage

- `%LOCALAPPDATA%\Convertepub\activations\` — Adobe activation keys (one folder per slot, transparent rotation)
- `%LOCALAPPDATA%\Convertepub\logs\` — application logs
- `%LOCALAPPDATA%\Convertepub\settings.json` — user preferences (output folder, language…)

## Build the executable

```
.venv\Scripts\python.exe -m PyInstaller build.spec --noconfirm
```

Output: `dist/Convertepub.exe` (~54 MB, standalone, no Python required on the target machine).

## Legality

This application is intended for **interoperability of legally acquired works** with hardware that doesn't support Adobe DRM — a use case explicitly covered by Article L331-5 of the French Intellectual Property Code. It does not circumvent the technical protection measure for fraudulent use: you must own a legitimate license for the book.

## Credits

The ADEPT core of this application is taken from two projects without which none of this would be possible:

- **[acsm-calibre-plugin](https://github.com/Leseratte10/acsm-calibre-plugin)** by Leseratte10 — Python reimplementation of the Adobe fulfillment protocol
- **[DeDRM_tools / noDRM](https://github.com/noDRM/DeDRM_tools)** by Apprentice Alf, Apprentice Harper and i♥cabbages — `ineptepub` module for ADEPT DRM removal
- **[libgourou](https://forge.soutade.fr/soutade/libgourou)** by Grégory Soutadé — original research on the ADEPT protocol

Many thanks to them.

## Support the project

If Convertepub helps you, you can support its development:

→ [revolut.me/datadump](https://revolut.me/datadump)

## License

GPL-3.0-or-later. See [`LICENSE`](LICENSE).

This application incorporates GPL-3.0 code from the projects cited above, so the entire application falls under the same license. Any redistribution must publish the sources.
