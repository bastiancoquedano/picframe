"""Prepara ExifTool oficial sin instalación global ni fotografías."""

import json
import shutil
import subprocess
from pathlib import Path


def main():
    found = shutil.which("exiftool")
    local = Path(__file__).resolve().parents[1] / ".runtime/exiftool"
    if not found and not (local / "exiftool").is_file():
        local.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                "13.58",
                "https://github.com/exiftool/exiftool.git",
                str(local),
            ],
            check=True,
        )
    tool = found or str(local / "exiftool")
    if not found:
        revision = subprocess.check_output(
            ["git", "-C", str(local), "rev-parse", "HEAD"], text=True
        ).strip()
        if revision != "38bdbace3037a89d2c332664fc60bddad118958a":
            raise SystemExit("La revisión de ExifTool no coincide con la fijada")
    result = subprocess.check_output([tool, "-ver"], text=True).strip()
    print(json.dumps({"tool": "ExifTool", "version": result}))


if __name__ == "__main__":
    main()
