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
    assert "metadata_unverified" in result.warnings


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


def test_exif_subfields_and_makernote_warning(photo_factory, tmp_path):
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
        assert 37500 not in exif.get_ifd(34665)
    assert "metadata_dropped:MakerNote" in result.warnings
