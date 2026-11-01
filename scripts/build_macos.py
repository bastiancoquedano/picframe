"""Construye una aplicación local; no firma para distribución ni publica artefactos."""

import os
import subprocess
import sys
from pathlib import Path


def main():
    if sys.platform != "darwin":
        raise SystemExit("La app macOS se construye en macOS")
    root = Path(__file__).resolve().parents[1]
    for path in (root / "models/yolo11n.pt", root / ".runtime/exiftool/exiftool"):
        if not path.is_file():
            raise SystemExit(f"Falta recurso preparado: {path.name}")
    runtime = root / ".runtime"
    runtime.mkdir(exist_ok=True)
    log = runtime / "build-macos.log"
    env = {
        **os.environ,
        "YOLO_OFFLINE": "true",
        "YOLO_AUTOINSTALL": "false",
        "YOLO_CONFIG_DIR": str(runtime / "build-settings"),
        "MPLCONFIGDIR": str(runtime / "build-matplotlib"),
    }
    with log.open("w") as output:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--noconfirm",
                "--clean",
                "--distpath",
                str(root / "dist"),
                "--workpath",
                str(root / "build/desktop"),
                str(root / "packaging/raceframe.spec"),
            ],
            cwd=root,
            env=env,
            stdout=output,
            stderr=subprocess.STDOUT,
        )
    if result.returncode:
        print(log.read_text()[-9000:])
        raise SystemExit(result.returncode)
    resources = root / "dist/Raceframe.app/Contents/Resources"
    for package in ("ultralytics", "torch", "torchvision", "opencv_python", "numpy", "pillow"):
        if not list(resources.glob(package + "-*.dist-info")):
            raise SystemExit("Faltan metadatos de dependencia en el bundle: " + package)
    print(root / "dist/Raceframe.app")


if __name__ == "__main__":
    main()
