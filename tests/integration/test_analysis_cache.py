from raceframe.config import Config
from raceframe.core.models import Box, Detection
from raceframe.core.processing import analyze_image, process_folder
from raceframe.imaging.discovery import discover


def test_analysis_reused_without_inference(photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    fake_detector.detections = [Detection(0, Box(20, 10, 60, 70), 0.95)]
    inv = discover(path.parent, tmp_path / "out")
    row = analyze_image(inv.root, inv.images[0], fake_detector, Config())
    assert fake_detector.calls == 1
    assert not (tmp_path / "out").exists()
    result = process_folder(
        inv.root, inv.destination, detector=fake_detector, analysis_overrides={row["image_id"]: row}
    )
    assert fake_detector.calls == 1
    assert result["summary"]["exported"] == 1


def test_stale_configuration_or_file_is_rejected(photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    inv = discover(path.parent, tmp_path / "out")
    row = analyze_image(inv.root, inv.images[0], fake_detector, Config())
    changed = process_folder(
        inv.root,
        inv.destination,
        detector=fake_detector,
        config=Config(quality=80),
        analysis_overrides={row["image_id"]: row},
    )
    assert changed["summary"]["errors"] == 1
    assert changed["summary"]["exported"] == 0
    path.write_bytes(path.read_bytes() + b"changed")
    result = process_folder(
        inv.root, inv.destination, detector=fake_detector, analysis_overrides={row["image_id"]: row}
    )
    assert result["summary"]["errors"] == 1
    assert fake_detector.calls == 1


def test_changed_inventory_rejected_before_export(photo_factory, tmp_path, fake_detector):
    import pytest

    path = photo_factory("input/a.jpg")
    inv = discover(path.parent, tmp_path / "out")
    row = analyze_image(inv.root, inv.images[0], fake_detector, Config())
    photo_factory("input/b.jpg")
    with pytest.raises(ValueError, match="carpeta cambió"):
        process_folder(
            inv.root,
            inv.destination,
            detector=fake_detector,
            analysis_overrides={row["image_id"]: row},
        )
    assert not inv.destination.exists()
