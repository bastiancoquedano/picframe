import hashlib

import pytest
from PIL import Image, ImageCms

from raceframe.core.models import Box, Composition, CompositionStatus
from raceframe.export.jpeg import export_image, validate_volume
from raceframe.imaging.discovery import discover
from raceframe.imaging.loader import load_image


def test_copy_exact_collision_and_original(photo_factory, tmp_path):
    path = photo_factory("input/photo.jpg", orientation=6)
    inv = discover(path.parent)
    dest = tmp_path / "out"
    dest.mkdir()
    validate_volume(dest)
    before = path.read_bytes()
    with load_image(inv.root, inv.images[0]) as loaded:
        comp = Composition(CompositionStatus.REVIEW_REQUIRED, Box(0, 0, 80, 120))
        a = export_image(inv.root, inv.images[0], loaded, comp, dest)
        b = export_image(inv.root, inv.images[0], loaded, comp, dest)
    assert a.path != b.path
    assert a.path.name == path.name
    assert b.path.stem == path.stem + "__2"
    assert a.path.read_bytes() == b.path.read_bytes() == before == path.read_bytes()
    assert a.sha256 == hashlib.sha256(before).hexdigest()
    assert not list(dest.glob("*.tmp"))


def test_crop_metadata_and_orientation(photo_factory, tmp_path):
    path = photo_factory("input/photo.jpg", orientation=6)
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    with Image.open(path) as raw:
        raw.save(path.with_name("icc.jpg"), exif=raw.getexif(), icc_profile=profile)
    inv = discover(path.parent)
    item = next(i for i in inv.images if i.relative_path == "icc.jpg")
    before = item.path.read_bytes()
    dest = tmp_path / "out"
    dest.mkdir()
    intents = []
    with load_image(inv.root, item) as loaded:
        comp = Composition(CompositionStatus.CROPPED, Box(0, 10, 80, 110))
        result = export_image(inv.root, item, loaded, comp, dest, before_publish=intents.append)
    with Image.open(result.path) as output:
        assert output.size == (80, 100)
        assert output.getexif().get(274, 1) == 1
        assert output.getexif()[271] == "Synthetic Camera"
        assert output.info["icc_profile"] == profile
    assert item.path.read_bytes() == before
    assert intents[0]["sha256"] == result.sha256
    assert "metadata_verified" in result.warnings


def test_publication_failure_leaves_no_final_file(photo_factory, tmp_path, monkeypatch):
    path = photo_factory("input/photo.jpg")
    inv = discover(path.parent)
    dest = tmp_path / "out"
    dest.mkdir()
    import raceframe.export.jpeg as exporter

    def fail(*args, **kwargs):
        raise OSError("disk failure")

    monkeypatch.setattr(exporter.os, "link", fail)
    with load_image(inv.root, inv.images[0]) as loaded:
        with pytest.raises(OSError):
            export_image(
                inv.root,
                inv.images[0],
                loaded,
                Composition(CompositionStatus.UNCHANGED, Box(0, 0, 120, 80)),
                dest,
            )
    assert list(dest.iterdir()) == []


def test_invalid_crop_rejected(photo_factory, tmp_path):
    path = photo_factory("input/photo.jpg")
    inv = discover(path.parent)
    dest = tmp_path / "out"
    dest.mkdir()
    with load_image(inv.root, inv.images[0]) as loaded:
        for box in [Box(-1, 0, 10, 10), Box(0, 0, 0, 10), Box(0.2, 0, 10, 10)]:
            with pytest.raises(ValueError):
                export_image(
                    inv.root,
                    inv.images[0],
                    loaded,
                    Composition(CompositionStatus.CROPPED, box),
                    dest,
                )
    assert not list(dest.iterdir())


def test_exif_subfields_and_makernote_preserved(photo_factory, tmp_path):
    path = photo_factory("input/a.jpg")
    with Image.open(path) as image:
        exif = image.getexif()
        exif[34665] = {36867: "2026:11:01 12:00:00", 37500: b"opaque maker data"}
        exif[34853] = {1: "N", 2: (1.0, 2.0, 3.0), 3: "W", 4: (4.0, 5.0, 6.0)}
        image.save(path.with_name("metadata.jpg"), exif=exif)
    inv = discover(path.parent)
    item = next(i for i in inv.images if i.relative_path == "metadata.jpg")
    dest = tmp_path / "out"
    dest.mkdir()
    with load_image(inv.root, item) as loaded:
        result = export_image(
            inv.root, item, loaded, Composition(CompositionStatus.CROPPED, Box(0, 0, 100, 70)), dest
        )
    with Image.open(result.path) as image:
        exif = image.getexif()
        assert exif.get_ifd(34665)[36867] == "2026:11:01 12:00:00"
        assert exif.get_ifd(34665)[40962] == 100
        assert exif.get_ifd(34853)[1] == "N"
        assert exif.get_ifd(34665)[37500] == b"opaque maker data"
    assert "metadata_verified" in result.warnings


def test_unknown_app_block_preserved(photo_factory, tmp_path):
    path = photo_factory("input/a.jpg")
    payload = b"unknown-app-private-data"
    segment = b"\xff\xef" + (len(payload) + 2).to_bytes(2, "big") + payload
    data = path.read_bytes()
    path.write_bytes(data[:2] + segment + data[2:])
    inv = discover(path.parent)
    dest = tmp_path / "out"
    dest.mkdir()
    with load_image(inv.root, inv.images[0]) as loaded:
        result = export_image(
            inv.root,
            inv.images[0],
            loaded,
            Composition(CompositionStatus.CROPPED, Box(0, 0, 100, 70)),
            dest,
        )
    assert segment in result.path.read_bytes()


def test_no_crop_published_without_metadata_verification(photo_factory, tmp_path, monkeypatch):
    import raceframe.export.metadata as metadata

    path = photo_factory("input/a.jpg")
    inv = discover(path.parent)
    dest = tmp_path / "out"
    dest.mkdir()

    def missing():
        raise metadata.MetadataError("unavailable")

    monkeypatch.setattr(metadata, "tool_path", missing)
    with load_image(inv.root, inv.images[0]) as loaded:
        with pytest.raises(metadata.MetadataError):
            export_image(
                inv.root,
                inv.images[0],
                loaded,
                Composition(CompositionStatus.CROPPED, Box(0, 0, 100, 70)),
                dest,
            )
    assert list(dest.iterdir()) == []


@pytest.mark.parametrize("size,success", [((120, 80), False), ((1200, 800), True)])
def test_mpf_auxiliary_preview_survives_crop(photo_factory, tmp_path, size, success):
    import io
    import struct

    from raceframe.export.metadata import is_metadata, jpeg_header, run_tool

    path = photo_factory("input/a.jpg", size=size)
    original = path.read_bytes()
    stream = io.BytesIO()
    with Image.new("RGB", (40, 30), "orange") as preview:
        preview.save(stream, format="JPEG")
    auxiliary = stream.getvalue()
    # MPF TIFF: versión, número de imágenes y tabla con dos entradas de 16 bytes.
    ifd = (
        struct.pack("<H", 3)
        + struct.pack("<HHI4s", 0xB000, 7, 4, b"0100")
        + struct.pack("<HHII", 0xB001, 4, 1, 2)
        + struct.pack("<HHII", 0xB002, 7, 32, 50)
        + struct.pack("<I", 0)
    )
    payload_size = 4 + 8 + len(ifd) + 32
    segment_size = payload_size + 4
    primary_size = len(original) + segment_size
    insertion = 2 + sum(len(raw) for marker, raw in jpeg_header(original)[0] if is_metadata(marker))
    entries = struct.pack("<IIIHH", 0x20030000, primary_size, 0, 0, 0) + struct.pack(
        "<IIIHH", 0x00010002, len(auxiliary), primary_size - (insertion + 8), 0, 0
    )
    payload = b"MPF\x00" + b"II*\x00" + struct.pack("<I", 8) + ifd + entries
    app = b"\xff\xe2" + (len(payload) + 2).to_bytes(2, "big") + payload
    path.write_bytes(original[:insertion] + app + original[insertion:] + auxiliary)
    inv = discover(path.parent)
    dest = tmp_path / "out"
    dest.mkdir()
    if not success:
        from raceframe.export.metadata import MetadataError

        with load_image(inv.root, inv.images[0]) as loaded:
            with pytest.raises(MetadataError):
                export_image(
                    inv.root,
                    inv.images[0],
                    loaded,
                    Composition(CompositionStatus.CROPPED, Box(0, 0, 100, 70)),
                    dest,
                )
        assert not list(dest.iterdir())
        return
    with load_image(inv.root, inv.images[0]) as loaded:
        result = export_image(
            inv.root,
            inv.images[0],
            loaded,
            Composition(CompositionStatus.CROPPED, Box(0, 0, 100, 70)),
            dest,
        )
    assert run_tool(["-b", "-PreviewImage", str(result.path)]) == auxiliary
