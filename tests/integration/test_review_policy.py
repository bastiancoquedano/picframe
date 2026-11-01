from pathlib import Path

from raceframe.core.models import Box, Detection
from raceframe.core.processing import process_folder


def test_ambiguous_copy_is_exact(photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    fake_detector.detections = [
        Detection(0, Box(5, 10, 45, 70), 0.95),
        Detection(1, Box(75, 10, 115, 70), 0.95),
    ]
    result = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    row = result["images"][0]
    assert row["selection_status"] == "ambiguous"
    assert row["composition"]["status"] == "review_required"
    assert (
        Path(result["manifest_path"]).parent / row["output_relative_path"]
    ).read_bytes() == path.read_bytes()


def test_copy_failure_remains_error(photo_factory, tmp_path, fake_detector, monkeypatch):
    path = photo_factory("input/a.jpg")
    import raceframe.core.processing as processing

    def fail(*args, **kwargs):
        raise OSError("copy failed")

    monkeypatch.setattr(processing, "export_image", fail)
    result = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    assert result["images"][0]["operation_status"] == "error"
    assert result["summary"]["review_required"] == 1
