import pytest

from raceframe.imaging.discovery import discover, open_input


def test_inventory_and_recursion(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    (root / "B.JPG").write_bytes(b"test")
    (root / "á.jpeg").write_bytes(b"other")
    (root / "no.png").write_bytes(b"ignore")
    (root / "sub").mkdir()
    (root / "sub" / "B.JPG").write_bytes(b"nested")
    first = discover(root)
    assert [i.relative_path for i in first.images] == ["B.JPG", "á.jpeg"]
    assert first.destination == tmp_path / "Raceframe_Output"
    recursive = discover(root, recursive=True)
    assert len(recursive.images) == 3
    assert recursive.images == discover(root, recursive=True).images
    assert len({i.image_id for i in recursive.images}) == 3
    assert not first.destination.exists()


@pytest.mark.parametrize("relative", [".", "nested", "nested/deeper"])
def test_reject_unsafe_destinations(tmp_path, relative):
    root = tmp_path / "input"
    root.mkdir()
    with pytest.raises(ValueError):
        discover(root, root / relative, recursive=True)


def test_symlink_paths_and_cycles(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    (root / "photo.jpg").write_bytes(b"inside")
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"outside")
    (root / "outside.jpg").symlink_to(outside)
    (root / "loop").symlink_to(root, target_is_directory=True)
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises(ValueError):
        discover(root, alias)
    result = discover(root, recursive=True)
    assert len(result.images) == 1
    assert result.warnings


def test_revalidate_input(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    path = root / "photo.jpg"
    path.write_bytes(b"original")
    inv = discover(root)
    item = inv.images[0]
    with open_input(inv.root, item) as handle:
        assert handle.read() == b"original"
    path.write_bytes(b"different bytes")
    with pytest.raises(ValueError):
        with open_input(inv.root, item):
            pass
    path.unlink()
    outside = tmp_path / "other.jpg"
    outside.write_bytes(b"original")
    path.symlink_to(outside)
    with pytest.raises(ValueError):
        with open_input(inv.root, item):
            pass


def test_empty_missing_and_file(tmp_path):
    assert discover(tmp_path).images == ()
    with pytest.raises(ValueError):
        discover(tmp_path / "missing")
    path = tmp_path / "file.jpg"
    path.touch()
    with pytest.raises(ValueError):
        discover(path)


def test_symlink_to_internal_file_is_revalidated(tmp_path):
    root = tmp_path / "in"
    root.mkdir()
    original = root / "a.jpg"
    original.write_bytes(b"inside")
    (root / "b.jpg").symlink_to(original)
    inv = discover(root)
    assert len(inv.images) == 2
    with open_input(inv.root, inv.images[1]) as handle:
        assert handle.read() == b"inside"


def test_nested_destination_without_recursion_is_safe(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    (root / "a.jpg").write_bytes(b"source")
    output = root / "exportaciones"
    output.mkdir()
    (output / "old.jpg").write_bytes(b"existing")
    inv = discover(root, output, recursive=False)
    assert [i.relative_path for i in inv.images] == ["a.jpg"]
    assert inv.destination == output
    with pytest.raises(ValueError):
        discover(root, root, recursive=False)
    with pytest.raises(ValueError):
        discover(root, output, recursive=True)
