"""Conservación de bloques JPEG originales y verificación estricta con ExifTool."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


class MetadataError(ValueError):
    pass


def tool_path():
    configured = os.environ.get("RACEFRAME_EXIFTOOL")
    local = Path(__file__).resolve().parents[3] / ".runtime/exiftool/exiftool"
    bundled = Path(getattr(sys, "_MEIPASS", "")) / "exiftool/exiftool"
    found = (
        configured
        or (str(bundled) if getattr(sys, "frozen", False) and bundled.is_file() else None)
        or shutil.which("exiftool")
        or (str(local) if local.is_file() else None)
    )
    if not found:
        raise MetadataError("Falta ExifTool: no se publicará un recorte sin verificar metadatos")
    return found


def run_tool(arguments):
    tool = tool_path()
    command = ["/usr/bin/perl", tool] if sys.platform == "darwin" else [tool]
    result = subprocess.run([*command, *arguments], capture_output=True, timeout=60)
    if result.returncode or result.stderr.strip():
        raise MetadataError(
            "ExifTool no pudo verificar/copiar los metadatos: "
            + result.stderr.decode(errors="replace")
        )
    return result.stdout


def read_metadata(path):
    values = json.loads(
        run_tool(
            [
                "-j",
                "-G1",
                "-s",
                "-n",
                "-a",
                "-struct",
                "-EXIF:all",
                "-MakerNotes:all",
                "-MPF:all",
                "-IPTC:all",
                "-XMP:all",
                "-ICC_Profile:all",
                "-Photoshop:all",
                "-Comment",
                str(path),
            ]
        )
    )[0]
    values.pop("SourceFile", None)
    return values


def jpeg_header(data):
    if data[:2] != b"\xff\xd8":
        raise MetadataError("Cabecera JPEG inválida")
    segments = []
    offset = 2
    while offset < len(data):
        start = offset
        if data[offset] != 255:
            raise MetadataError("Segmento JPEG inválido")
        while data[offset] == 255:
            offset += 1
        marker = data[offset]
        offset += 1
        if marker in (0xDA, 0xD9):
            return segments, data[start:]
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:
            segments.append((marker, data[start:offset]))
            continue
        length = int.from_bytes(data[offset : offset + 2], "big")
        if length < 2 or offset + length > len(data):
            raise MetadataError("Longitud de segmento JPEG inválida")
        offset += length
        segments.append((marker, data[start:offset]))
    raise MetadataError("JPEG sin datos de imagen")


def is_metadata(marker):
    return 0xE0 <= marker <= 0xEF or marker == 0xFE


def preserve_metadata(source_handle, encoded_path, cropped_image):
    # Copiar segmentos completos conserva incluso bloques APP que las bibliotecas no interpretan.
    source_handle.seek(0)
    original = source_handle.read()
    original_segments, original_tail = jpeg_header(original)
    encoded_segments, tail = jpeg_header(encoded_path.read_bytes())
    rebuilt = b"\xff\xd8" + b"".join(
        raw for marker, raw in original_segments if is_metadata(marker)
    )
    rebuilt += b"".join(raw for marker, raw in encoded_segments if not is_metadata(marker)) + tail
    # Canon MPF conserva una imagen auxiliar al final. Sus offsets deben seguir siendo válidos.
    original_end = len(original) - len(original_tail) + original_tail.find(b"\xff\xd9") + 2
    if re.search(rb"\xff[\xe0-\xef\xfe]", original_tail[: original_tail.find(b"\xff\xd9")]):
        raise MetadataError("Metadatos entre escaneos JPEG aún no soportados")
    trailer = original[original_end:]
    if trailer:
        if original_tail.find(b"\xff\xd9") < 0 or len(rebuilt) > original_end:
            raise MetadataError("No se puede conservar de forma segura el tráiler MPF de este JPEG")
        rebuilt += b"\x00" * (original_end - len(rebuilt)) + trailer
    encoded_path.write_bytes(rebuilt)
    # ExifTool lee el original desde una copia temporal: nunca recibe el original como destino.
    fd, snapshot_name = tempfile.mkstemp(suffix=".jpg", dir=encoded_path.parent)
    snapshot = Path(snapshot_name)
    thumb = snapshot.with_suffix(".thumb.jpg")
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(original)
        before = read_metadata(snapshot)
        with cropped_image.copy() as preview:
            preview.thumbnail((160, 160))
            preview.save(thumb, format="JPEG", quality=85)
            tw, th = preview.size
        width, height = cropped_image.size
        edits = [
            "-overwrite_original",
            "-IFD0:Orientation#=1",
            f"-IFD0:ImageWidth={width}",
            f"-IFD0:ImageHeight={height}",
            f"-ExifIFD:ExifImageWidth={width}",
            f"-ExifIFD:ExifImageHeight={height}",
            f"-ThumbnailImage<={thumb}",
            "-IFD1:Orientation#=1",
            f"-IFD1:ImageWidth={tw}",
            f"-IFD1:ImageHeight={th}",
        ]
        if "XMP-tiff:Orientation" in before:
            edits.append("-XMP-tiff:Orientation#=1")
        run_tool([*edits, str(encoded_path)])
        after = read_metadata(encoded_path)
        allowed = {
            "IFD0:Orientation",
            "IFD0:ImageWidth",
            "IFD0:ImageHeight",
            "ExifIFD:ExifImageWidth",
            "ExifIFD:ExifImageHeight",
            "XMP-tiff:Orientation",
            "IFD1:Orientation",
            "IFD1:ImageWidth",
            "IFD1:ImageHeight",
            "IFD1:ThumbnailOffset",
            "IFD1:ThumbnailLength",
            "IFD1:ThumbnailImage",
        }
        # La posición absoluta del MPF cambia al reubicar la cabecera; su contenido no debe cambiar.
        allowed.update(key for key in before if key.endswith(":MPImageStart"))
        for key in before:
            if key.startswith("MPImage") and key.endswith(":PreviewImage"):
                if run_tool(["-b", "-" + key, str(snapshot)]) != run_tool(
                    ["-b", "-" + key, str(encoded_path)]
                ):
                    raise MetadataError("No se conservó la previsualización MPF original")
        changed = [
            key for key, value in before.items() if key not in allowed and after.get(key) != value
        ]
        if changed:
            raise MetadataError("No se conservaron los campos: " + ", ".join(changed))
        # APP/COM ajenos a EXIF se conservan literalmente, incluidos ICC y bloques desconocidos.
        remaining = Counter(
            raw for marker, raw in jpeg_header(encoded_path.read_bytes())[0] if is_metadata(marker)
        )
        for marker, raw in original_segments:
            if not is_metadata(marker) or (
                marker == 0xE1 and (b"Exif\x00\x00" in raw[:12] or b"XMP-tiff:Orientation" in raw)
            ):
                continue
            if marker == 0xE1 and "XMP-tiff:Orientation" in before:
                continue  # Valores XMP comparados arriba; solo se permite actualizar orientación.
            if remaining[raw] <= 0:
                raise MetadataError("No se conservó un bloque APP/COM original")
            remaining[raw] -= 1
        if trailer and not encoded_path.read_bytes().endswith(trailer):
            raise MetadataError("No se conservó el tráiler con la previsualización original")
        return len(before)
    except (OSError, ValueError, subprocess.SubprocessError, IndexError) as exc:
        if isinstance(exc, MetadataError):
            raise
        raise MetadataError("No se pudo completar la conservación estricta de metadatos") from exc
    finally:
        snapshot.unlink(missing_ok=True)
        thumb.unlink(missing_ok=True)
