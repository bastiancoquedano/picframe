import hashlib

import pytest

from raceframe.imaging.discovery import discover
from raceframe.imaging.loader import load_image


@pytest.mark.parametrize(
    "orientation,color",
    [
        (1, (255, 0, 0)),
        (2, (0, 128, 0)),
        (3, (255, 255, 255)),
        (4, (0, 0, 255)),
        (5, (255, 0, 0)),
        (6, (0, 0, 255)),
        (7, (255, 255, 255)),
        (8, (0, 128, 0)),
    ],
)
def test_all_orientations(photo_factory, orientation, color):
    path = photo_factory(orientation=orientation)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    inv = discover(path.parent)
    with load_image(inv.root, inv.images[0]) as loaded:
        assert loaded.stored_size == (120, 80)
        expected_size = (80, 120) if orientation >= 5 else (120, 80)
        assert loaded.image.size == expected_size
        assert loaded.source_orientation == orientation
        pixel = loaded.image.getpixel((expected_size[0] // 4, expected_size[1] // 4))
        assert all(abs(a - b) < 10 for a, b in zip(pixel, color, strict=True))
        assert loaded.exif.get(274, 1) == 1
        assert loaded.exif[271] == "Synthetic Camera"
        assert loaded.warnings == ()
        image = loaded.image
    with pytest.raises(ValueError):
        image.getpixel((0, 0))
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before


@pytest.mark.parametrize("orientation", [None, 99])
def test_missing_invalid_orientation(photo_factory, orientation):
    path = photo_factory(orientation=orientation)
    inv = discover(path.parent)
    with load_image(inv.root, inv.images[0]) as loaded:
        assert loaded.image.size == (120, 80)
        assert bool(loaded.warnings) is (orientation == 99)
        assert loaded.exif.get(274, 1) == 1


def test_damaged_file(tmp_path):
    path = tmp_path / "broken.jpg"
    path.write_bytes(b"not a jpeg")
    inv = discover(tmp_path)
    with pytest.raises(ValueError):
        with load_image(inv.root, inv.images[0]):
            pass


def test_icc_is_captured(photo_factory):
    from PIL import Image, ImageCms

    path = photo_factory()
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    with Image.open(path) as image:
        image.save(path.with_name("icc.jpg"), icc_profile=profile)
    inv = discover(path.parent)
    item = next(item for item in inv.images if item.relative_path == "icc.jpg")
    with load_image(inv.root, item) as loaded:
        assert loaded.icc_profile == profile


def test_other_format_with_jpeg_extension_is_rejected(photo_factory):
    from PIL import Image

    path = photo_factory()
    with Image.open(path) as image:
        image.save(path.with_name("disguised.jpg"), format="PNG")
    inv = discover(path.parent)
    item = next(item for item in inv.images if item.relative_path == "disguised.jpg")
    with pytest.raises(ValueError):
        with load_image(inv.root, item):
            pass
