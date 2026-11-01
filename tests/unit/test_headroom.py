from raceframe.config import Config
from raceframe.core.cropping import calculate_crop, calculate_focal_crop
from raceframe.core.models import Box


def test_headroom_overrides_occupancy_with_body_safety():
    subject = Box(1700, 2800, 2600, 5000)
    result = calculate_focal_crop(4000, 6000, subject, Config(), 70)
    assert abs((subject.y1 - result.crop.y1) - result.crop.height / 3) <= 1
    assert subject.height / result.crop.height < 0.7
    assert result.crop.contains(result.protected)
    assert max(result.crop.width, result.crop.height) >= 3000
    assert abs(result.crop.width - result.crop.height * 2 / 3) <= 1
    assert "head_upper_third_priority" in result.reasons


def test_impossible_third_preserves_body_and_reports_limit():
    subject = Box(1500, 0, 2500, 6000)
    result = calculate_focal_crop(4000, 6000, subject, Config(), 100)
    assert result.crop == Box(0, 0, 4000, 6000)
    assert "headroom_limited_by_safety_or_bounds" in result.reasons


def test_wide_does_not_apply_headroom():
    subject = Box(100, 200, 300, 700)
    config = Config()
    assert calculate_focal_crop(600, 900, subject, config, 35) == calculate_crop(
        600, 900, subject, config
    )
