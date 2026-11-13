"""Publicación exclusiva de archivos completos en el mismo volumen."""

import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from raceframe.core.models import Box, CompositionStatus
from raceframe.export.metadata import preserve_metadata
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


def _publish_temporary(root, item, destination, temporary, dimensions, notes, before_publish):
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


def export_image(root, item, loaded, composition, destination, *, quality=95, before_publish=None):
    destination = Path(destination).resolve(strict=True)
    if destination == root:
        raise ValueError("La salida no puede coincidir con el origen")
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
                    cropped.save(
                        output,
                        format="JPEG",
                        quality=quality,
                    )
            output.flush()
            os.fsync(output.fileno())
        if composition.status == CompositionStatus.CROPPED:
            with (
                open_input(root, item) as source,
                loaded.image.crop(tuple(map(int, box.as_tuple()))) as cropped,
            ):
                preserve_metadata(source, temporary, cropped)
            with temporary.open("rb") as confirmed:
                os.fsync(confirmed.fileno())
            notes = ("metadata_verified",)
        return _publish_temporary(
            root, item, destination, temporary, dimensions, notes, before_publish
        )
    finally:
        temporary.unlink(missing_ok=True)


def export_rendered_jpeg(
    root, item, loaded, rendered, destination, *, quality=95, before_publish=None
):
    """Publica un watermark ya renderizado, full-frame, conservando metadatos de origen."""
    root = Path(root).resolve(strict=True)
    destination = Path(destination).resolve(strict=True)
    if destination == root:
        raise ValueError("La salida no puede coincidir con el origen")
    if rendered.mode != "RGB" or rendered.size != loaded.image.size:
        raise ValueError("El render debe ser RGB y conservar las dimensiones de origen")
    if type(quality) is not int or not 1 <= quality <= 95:
        raise ValueError("Calidad JPEG inválida")
    fd, name = tempfile.mkstemp(prefix=".picframe-watermark-", suffix=".tmp", dir=destination)
    temporary = Path(name)
    dimensions = rendered.size
    try:
        with os.fdopen(fd, "wb") as output:
            rendered.save(output, format="JPEG", quality=quality)
            output.flush()
            os.fsync(output.fileno())
        with open_input(root, item) as source:
            preserve_metadata(source, temporary, rendered)
        with temporary.open("rb") as confirmed:
            os.fsync(confirmed.fileno())
        return _publish_temporary(
            root, item, destination, temporary, dimensions, ("metadata_verified",), before_publish
        )
    finally:
        temporary.unlink(missing_ok=True)


def export_original_copy(root, item, destination, dimensions, *, before_publish=None):
    """Publica una copia byte-a-byte de origen para fallback, sin decodificarla ni recodificarla."""
    root = Path(root).resolve(strict=True)
    destination = Path(destination).resolve(strict=True)
    if destination == root:
        raise ValueError("La salida no puede coincidir con el origen")
    fd, name = tempfile.mkstemp(prefix=".picframe-watermark-copy-", suffix=".tmp", dir=destination)
    temporary = Path(name)
    try:
        with os.fdopen(fd, "wb") as output, open_input(root, item) as source:
            shutil.copyfileobj(source, output, length=1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        return _publish_temporary(
            root,
            item,
            destination,
            temporary,
            dimensions,
            ("metadata_verified", "source_bytes_preserved"),
            before_publish,
        )
    finally:
        temporary.unlink(missing_ok=True)
