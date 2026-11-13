import pytest
from PIL import Image

from raceframe.export.jpeg import export_rendered_jpeg
from raceframe.imaging.discovery import discover
from raceframe.imaging.loader import load_image


def test_full_size_rendered_jpeg_preserves_metadata_and_original(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(600, 400), orientation=6)
    original = source.read_bytes()
    inventory = discover(source.parent, tmp_path / "out")
    item = inventory.images[0]
    inventory.destination.mkdir()
    with (
        load_image(inventory.root, item) as loaded,
        Image.new("RGB", loaded.image.size, "#8932ab") as rendered,
    ):
        result = export_rendered_jpeg(
            inventory.root, item, loaded, rendered, inventory.destination, quality=91
        )
        assert result.dimensions == loaded.image.size == (400, 600)
    assert "metadata_verified" in result.warnings
    assert result.path.read_bytes() != original
    assert source.read_bytes() == original
    with Image.open(result.path) as output:
        assert output.size == (400, 600)
        assert output.getexif()[271] == "Synthetic Camera"
        assert output.getexif()[274] == 1


def test_rendered_export_rejects_dimensions_that_change_the_frame(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(600, 400))
    inventory = discover(source.parent, tmp_path / "out")
    item = inventory.images[0]
    inventory.destination.mkdir()
    with load_image(inventory.root, item) as loaded, Image.new("RGB", (300, 200)) as rendered:
        with pytest.raises(ValueError, match="dimensiones de origen"):
            export_rendered_jpeg(inventory.root, item, loaded, rendered, inventory.destination)
    assert not list(inventory.destination.iterdir())


def test_rendered_export_never_overwrites_existing_files(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(600, 400))
    inventory = discover(source.parent, tmp_path / "out")
    item = inventory.images[0]
    inventory.destination.mkdir()
    existing = inventory.destination / "a.jpg"
    existing.write_bytes(b"anterior")
    with (
        load_image(inventory.root, item) as loaded,
        Image.new("RGB", loaded.image.size, "blue") as rendered,
    ):
        result = export_rendered_jpeg(inventory.root, item, loaded, rendered, inventory.destination)
    assert result.path.name == "a__2.jpg"
    assert existing.read_bytes() == b"anterior"
