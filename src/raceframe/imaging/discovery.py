"""Inventario local estable y apertura de entradas revalidadas, siempre de solo lectura."""

import os
import stat
from contextlib import contextmanager
from pathlib import Path

from raceframe.core.models import InputImage, Inventory


def discover(source: Path, output: Path | None = None, *, recursive: bool = False) -> Inventory:
    try:
        root = Path(source).resolve(strict=True)
    except OSError as exc:
        raise ValueError("La carpeta de origen no existe o no es accesible") from exc
    if not root.is_dir():
        raise ValueError("El origen debe ser una carpeta")
    requested_destination = Path(output) if output is not None else root.parent / "Raceframe_Output"
    destination = requested_destination.resolve()
    if destination == root or destination.is_relative_to(root):
        raise ValueError("El destino debe estar fuera de la carpeta de origen")
    if destination.exists() and not destination.is_dir():
        raise ValueError("El destino debe ser una carpeta")
    paths = []
    warnings = []

    def walk_error(error):
        raise ValueError("No se pudo recorrer una carpeta de origen") from error

    for parent, dirs, names in os.walk(root, followlinks=False, onerror=walk_error):
        retained = []
        for name in sorted(dirs):
            if (Path(parent) / name).is_symlink():
                relative = (Path(parent) / name).relative_to(root)
                warnings.append(f"symlink_directory_ignored: {relative}")
            else:
                retained.append(name)
        dirs[:] = retained if recursive else []
        for name in sorted(names):
            lexical = Path(parent) / name
            if lexical.suffix.lower() not in (".jpg", ".jpeg"):
                continue
            try:
                actual = lexical.resolve(strict=True)
                if not actual.is_relative_to(root):
                    warnings.append(f"external_symlink_ignored: {lexical.relative_to(root)}")
                    continue
                info = actual.stat()
            except OSError as exc:
                raise ValueError(f"No se pudo inventariar {lexical.relative_to(root)}") from exc
            if stat.S_ISREG(info.st_mode):
                paths.append((lexical.relative_to(root).as_posix(), actual, info))
    images = tuple(
        InputImage(
            image_id=relative,
            path=actual,
            relative_path=relative,
            size_bytes=info.st_size,
            mtime_ns=info.st_mtime_ns,
            device=info.st_dev,
            inode=info.st_ino,
        )
        for relative, actual, info in sorted(paths, key=lambda row: row[0])
    )
    return Inventory(root, destination, images, tuple(warnings))


@contextmanager
def open_input(root: Path, item: InputImage):
    """Rechaza una entrada sustituida o modificada desde el inventario."""
    handle = None
    try:
        current = (root / item.relative_path).resolve(strict=True)
        if not current.is_relative_to(root) or current != item.path:
            raise ValueError("La entrada cambió de ubicación")
        fd = os.open(current, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        handle = os.fdopen(fd, "rb")
        info = os.fstat(handle.fileno())
        signature = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
        expected = (item.device, item.inode, item.size_bytes, item.mtime_ns)
        if not stat.S_ISREG(info.st_mode) or signature != expected:
            raise ValueError("La entrada fue modificada después del inventario")
    except (OSError, RuntimeError) as exc:
        if handle is not None:
            handle.close()
        raise ValueError("No se pudo revalidar la entrada") from exc
    except ValueError:
        if handle is not None:
            handle.close()
        raise
    try:
        yield handle
    finally:
        handle.close()
