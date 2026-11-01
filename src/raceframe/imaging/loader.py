"""Carga JPEG orientada con vida útil acotada y originales abiertos solo para lectura."""

import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from raceframe.core.models import InputImage
from raceframe.imaging.discovery import open_input


@dataclass
class LoadedImage:
    image: Image.Image
    stored_size: tuple[int, int]
    source_orientation: int | None
    exif: Image.Exif
    source_exif: bytes | None
    icc_profile: bytes | None
    warnings: tuple[str, ...]


@contextmanager
def load_image(root: Path, item: InputImage):
    upright = None
    try:
        with open_input(root, item) as handle, warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(handle) as raw:
                if raw.format != "JPEG":
                    raise ValueError("La entrada no contiene un JPEG")
                raw.load()
                stored_size = raw.size
                source_exif = raw.info.get("exif")
                icc_profile = raw.info.get("icc_profile")
                exif = raw.getexif()
                orientation = exif.get(274)
                notes = []
                if orientation is not None and orientation not in range(1, 9):
                    notes.append("orientation_invalid")
                    exif[274] = 1
                    raw.info["exif"] = exif.tobytes()
                upright = ImageOps.exif_transpose(raw)
                upright.load()
                loaded = LoadedImage(
                    image=upright,
                    stored_size=stored_size,
                    source_orientation=orientation,
                    exif=upright.getexif(),
                    source_exif=source_exif,
                    icc_profile=icc_profile,
                    warnings=tuple(notes),
                )
    except (
        OSError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        SyntaxError,
    ) as exc:
        if upright is not None:
            upright.close()
        raise ValueError("No se pudo decodificar el JPEG con seguridad") from exc
    except Exception:
        if upright is not None:
            upright.close()
        raise
    try:
        yield loaded
    finally:
        upright.close()
