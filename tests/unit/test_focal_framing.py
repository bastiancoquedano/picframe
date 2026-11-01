from raceframe.config import Config
from raceframe.core.cropping import calculate_crop, calculate_focal_crop
from raceframe.core.models import Box


def test_telephoto_subject_priority_and_resolution():
    box = Box(1400, 1800, 2300, 4000)
    result = calculate_focal_crop(4000, 6000, box, Config(), 189)
    assert result.status == "cropped"
    assert 0.70 <= box.height / result.crop.height <= 0.80
    assert max(result.crop.width, result.crop.height) >= 3000
    assert result.crop.contains(result.protected)


def test_wide_missing_and_threshold():
    box = Box(1400, 1800, 2300, 4000)
    cfg = Config()
    for focal in (10, 35, 69.9, None):
        assert calculate_focal_crop(4000, 6000, box, cfg, focal) == calculate_crop(
            4000, 6000, box, cfg
        )
    assert "focal_subject_priority" in calculate_focal_crop(4000, 6000, box, cfg, 70).reasons


def test_resolution_prevents_overcropping():
    box = Box(1400, 1800, 1600, 2400)
    result = calculate_focal_crop(4000, 6000, box, Config(), 100)
    assert max(result.crop.width, result.crop.height) >= 3000
    assert "occupancy_limited_by_resolution_or_safety" in result.reasons
