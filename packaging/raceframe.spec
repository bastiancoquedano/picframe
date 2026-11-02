# PyInstaller: bundle local arm64, sin Developer ID ni notarización.
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, copy_metadata
import sys

sys.setrecursionlimit(10000)
project = Path(SPECPATH).parent
import os
os.environ["YOLO_OFFLINE"] = "true"
os.environ["YOLO_AUTOINSTALL"] = "false"
hidden = collect_submodules("ultralytics")
package_metadata = []
for package in ("ultralytics", "torch", "torchvision", "opencv-python", "numpy", "pillow"):
    package_metadata += copy_metadata(package)
a = Analysis(
    [str(project / "scripts/desktop_entry.py")],
    pathex=[str(project / "src")],
    binaries=[],
    datas=package_metadata + [
        (str(project / "models/yolo11n.pt"), "models"),
        (str(project / ".runtime/exiftool/exiftool"), "exiftool"),
        (str(project / ".runtime/exiftool/lib"), "exiftool/lib"),
    ],
    hiddenimports=hidden,
    hookspath=[str(project / "packaging/hooks")],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "IPython",
        "notebook",
        "pytest",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtPdf",
        "PySide6.QtQml",
        "PySide6.QtQuick",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Picframe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Picframe")
app = BUNDLE(
    coll,
    name="Picframe.app",
    bundle_identifier="cl.picframe.desktop",
    info_plist={
        "CFBundleName": "Picframe",
        "CFBundleDisplayName": "Picframe",
        "CFBundleShortVersionString": "0.3.0",
        "NSHighResolutionCapable": True,
    },
)
