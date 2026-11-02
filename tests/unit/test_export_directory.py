import pytest

from raceframe.export.directory import create_job_directory, validate_job_name


@pytest.mark.parametrize(
    "name",
    [
        "",
        " ",
        ".",
        "..",
        "../escape",
        "/tmp/out",
        "a/b",
        "a\\b",
        "a:b",
        "line\n",
        "a\x00b",
        "ñ" * 101,
    ],
)
def test_rejects_invalid_folder_names_before_creating_anything(tmp_path, name):
    with pytest.raises(ValueError):
        create_job_directory(tmp_path / "out", name, "id")
    assert not (tmp_path / "out").exists()


def test_named_directory_does_not_follow_existing_symlink(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "out"
    root.mkdir()
    (root / "Carrera").symlink_to(outside, target_is_directory=True)
    assert create_job_directory(root, "Carrera", "id") == root / "Carrera (2)"
    assert list(outside.iterdir()) == []


def test_default_preserves_cli_directory_contract(tmp_path):
    assert create_job_directory(tmp_path, None, "123") == tmp_path / "job-123"
    assert validate_job_name("  Carrera Ñandú  ") == "Carrera Ñandú"
