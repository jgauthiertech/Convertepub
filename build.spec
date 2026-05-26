# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec pour Convertepub.

Build : pyinstaller build.spec
Sortie : dist/Convertepub.exe (autonome, Windows)
"""

from pathlib import Path

block_cipher = None

# Modules PySide6 qu'on n'utilise PAS — exclusion pour réduire la taille de
# l'exécutable. Sans ces excludes, le binaire pèse ~200 MB (Qt embarque
# WebEngine, Multimedia, 3D, Charts, etc.). Avec, on tombe à ~60-80 MB.
PYSIDE_EXCLUDES = [
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DRender",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtConcurrent",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtPrintSupport",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtWebChannel",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtXml",
]

# Le moteur ADEPT charge dynamiquement des modules via try/except, PyInstaller
# peut ne pas tous les détecter. On les force ici.
HIDDEN_IMPORTS = [
    "src.core.adept.libadobe",
    "src.core.adept.libadobeAccount",
    "src.core.adept.libadobeFulfill",
    "src.core.adept.customRSA",
    "src.core.adept.cpuid",
    "src.core.adept.ineptepub",
    "src.core.adept.zeroedzipinfo",
    "Cryptodome",
    "Cryptodome.Cipher",
    "Cryptodome.Cipher.AES",
    "Cryptodome.Cipher.PKCS1_v1_5",
    "Cryptodome.Hash",
    "Cryptodome.Hash.SHA",
    "Cryptodome.PublicKey",
    "Cryptodome.PublicKey.RSA",
    "Cryptodome.Random",
    "Cryptodome.Util",
    "Cryptodome.Util.asn1",
    "oscrypto",
    "oscrypto.keys",
    "oscrypto.asymmetric",
    "asn1crypto",
]

a = Analysis(
    ["src/main.py"],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[],
    hiddenimports=HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=PYSIDE_EXCLUDES + ["tkinter"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="Convertepub",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,             # UPX peut être bloqué par les antivirus, on s'en passe
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,         # mode GUI : pas de fenêtre console derrière
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico",   # à activer quand on aura une icône
)
