"""Diagnóstico local de Apple Vision; no guarda ni transmite la imagen o la máscara."""

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps

from raceframe.watermark.vision import VisionPersonSegmenter


def main(argv=None):
    parser = argparse.ArgumentParser(description="Comprobar la máscara local de Apple Vision")
    parser.add_argument("image", type=Path, help="JPEG local; no se copia ni modifica")
    parser.add_argument("--quality", choices=("accurate", "balanced", "fast"), default="accurate")
    arguments = parser.parse_args(argv)
    path = arguments.image.expanduser()
    if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg"}:
        parser.error("Selecciona un JPEG local existente")
    with Image.open(path) as source:
        oriented = ImageOps.exif_transpose(source).convert("RGB")
        try:
            segmenter = VisionPersonSegmenter(arguments.quality)
            result = segmenter.segment(oriented)
            report = {
                "backend": result.backend,
                "backend_version": result.backend_version,
                "compute_device": result.compute_device,
                "quality": result.quality,
                "vision_revision": result.revision,
                "status": result.status,
                "reason": result.reason,
                "oriented_dimensions": list(oriented.size),
                "mask_dimensions": [int(result.mask.shape[1]), int(result.mask.shape[0])],
                "mask_bytes_owned_by_picframe": bool(result.mask.flags.owndata),
                "mask_pixels_confident": int((result.mask >= 128).sum()),
            }
        finally:
            oriented.close()
    print(json.dumps(report, ensure_ascii=False))
    # Una máscara de baja confianza es un resultado utilizable del gate: confirma
    # que Vision respondió y que la app puede activar el fallback previsto.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
