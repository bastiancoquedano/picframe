"""Publicación exclusiva de archivos completos en el mismo volumen."""

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from raceframe.core.models import Box, CompositionStatus
from raceframe.imaging.discovery import open_input


def file_hash(path):
    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def validate_volume(destination):
    fd, name = tempfile.mkstemp(prefix=".raceframe-probe-", dir=destination)
    os.close(fd)
    source = Path(name)
    target = source.with_suffix(".link")
    try:
        os.link(source, target)
        sync_directory(destination)
    finally:
        source.unlink(missing_ok=True)
        target.unlink(missing_ok=True)


@dataclass(frozen=True)
class ExportResult:
    path: Path
    sha256: str
    dimensions: tuple[int, int]
    warnings: tuple[str, ...] = ()


def _cropped_exif(loaded, size):
    source = loaded.exif
    result = Image.Exif()
    # Serializar de nuevo evita conservar miniaturas con coordenadas antiguas.
    excluded = {274, 256, 257, 34665, 34853, 513, 514, 40965, 37500}
    for tag, value in source.items():
        if tag not in excluded:
            result[tag] = value
    result[274] = 1
    result[256], result[257] = size
    exif_ifd = dict(source.get_ifd(34665)) if 34665 in source else {}
    dropped = 37500 in exif_ifd or 37500 in source
    exif_ifd.pop(37500, None)  # MakerNotes tienen offsets y convenciones del fabricante.
    exif_ifd.pop(40965, None)
    exif_ifd[40962], exif_ifd[40963] = size
    result[34665] = exif_ifd
    if 34853 in source:
        result[34853] = dict(source.get_ifd(34853))
    notes = ["metadata_unverified"]
    if dropped:
        notes.append("metadata_dropped:MakerNote")
    return result, tuple(notes)


def export_image(root, item, loaded, composition, destination, *, quality=95, before_publish=None):
    destination = Path(destination).resolve(strict=True)
    if destination == root or destination.is_relative_to(root):
        raise ValueError("La salida debe estar fuera del origen")
    width, height = loaded.image.size
    box = composition.crop
    if (
        not box.valid
        or not Box(0, 0, width, height).contains(box)
        or any(int(v) != v for v in box.as_tuple())
    ):
        raise ValueError("Recorte inválido")
    if type(quality) is not int or not 1 <= quality <= 95:
        raise ValueError("Calidad JPEG inválida")
    fd, name = tempfile.mkstemp(prefix=".raceframe-", suffix=".tmp", dir=destination)
    temporary = Path(name)
    notes = ()
    try:
        with os.fdopen(fd, "wb") as output:
            if composition.status != CompositionStatus.CROPPED:
                with open_input(root, item) as source:
                    shutil.copyfileobj(source, output, length=1024 * 1024)
                dimensions = (width, height)
            else:
                with loaded.image.crop(tuple(map(int, box.as_tuple()))) as cropped:
                    dimensions = cropped.size
                    exif, notes = _cropped_exif(loaded, dimensions)
                    cropped.save(
                        output,
                        format="JPEG",
                        quality=quality,
                        exif=exif,
                        icc_profile=loaded.icc_profile,
                    )
            output.flush()
            os.fsync(output.fileno())
        digest = file_hash(temporary)
        base = Path(item.relative_path).name
        stem, extension = Path(base).stem, Path(base).suffix
        number = 1
        while True:
            filename = base if number == 1 else f"{stem}__{number}{extension}"
            target = destination / filename
            if target.exists() or target.is_symlink():
                number += 1
                continue
            # La intención durable precede a la publicación; una colisión genera otra intención.
            if before_publish is not None:
                before_publish(
                    {
                        "temporary": temporary.name,
                        "output_relative_path": filename,
                        "sha256": digest,
                        "dimensions": dimensions,
                        "warnings": list(notes),
                    }
                )
            try:
                os.link(temporary, target)
                sync_directory(destination)
                break
            except FileExistsError:
                if before_publish is not None:
                    before_publish(
                        {
                            "aborted": True,
                            "temporary": temporary.name,
                            "output_relative_path": filename,
                            "sha256": digest,
                            "dimensions": dimensions,
                        }
                    )
                number += 1
        return ExportResult(target, digest, dimensions, notes)
    finally:
        temporary.unlink(missing_ok=True)
