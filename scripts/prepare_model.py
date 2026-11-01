"""Preparación explícita de pesos oficiales; jamás se invoca desde process."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path

URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt"
SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description="Descarga explícita de YOLO11n, sin fotografías")
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[1] / "models/yolo11n.pt"
    )
    target = parser.parse_args().output.resolve()
    if target.exists():
        if not target.is_file() or digest(target) != SHA256:
            raise SystemExit("Ya existe un archivo diferente; no se sobrescribe")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".model-", dir=target.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, "wb") as output, urllib.request.urlopen(URL, timeout=60) as response:
                shutil.copyfileobj(response, output)
                output.flush()
                os.fsync(output.fileno())
            if digest(temporary) != SHA256:
                raise SystemExit("El hash no coincide con el peso oficial fijado; no se publica")
            os.link(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
    print(json.dumps({"model": target.name, "sha256": SHA256, "source": URL}))


if __name__ == "__main__":
    main()
