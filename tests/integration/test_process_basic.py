import json

from raceframe.core.models import Box, Detection
from raceframe.core.processing import process_folder


def test_mixed_folder_and_repeated_outputs(photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    (path.parent / "bad.jpg").write_bytes(b"broken")
    fake_detector.detections = [Detection(0, Box(20, 15, 40, 65), 0.95)]
    first = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    second = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    assert first["status"] == "completed_with_errors"
    assert first["summary"]["exported"] == 1
    assert first["summary"]["errors"] == 1
    assert first["manifest_path"] != second["manifest_path"]
    assert len(first["images"]) == 2
    assert json.loads(open(first["manifest_path"]).read())["job_id"] == first["job_id"]


def test_empty_and_review(photo_factory, tmp_path, fake_detector):
    source = tmp_path / "empty"
    source.mkdir()
    result = process_folder(source, tmp_path / "out", detector=fake_detector)
    assert result["status"] == "completed"
    assert result["summary"]["total"] == 0
    path = photo_factory("input/a.jpg", orientation=6)
    before = path.read_bytes()
    result = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    assert result["summary"]["review_required"] == 1
    from pathlib import Path

    output = Path(result["manifest_path"]).parent / result["images"][0]["output_relative_path"]
    assert output.read_bytes() == before == path.read_bytes()
