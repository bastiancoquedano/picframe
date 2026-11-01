import random

from raceframe.config import Config
from raceframe.core.cropping import calculate_crop
from raceframe.core.models import Box


def test_modes_preserve_nested_areas():
    rng = random.Random(13)
    for _ in range(80):
        x = rng.randint(0, 500)
        box = Box(x, 80, x + 80, 320)
        results = [
            calculate_crop(600, 400, box, Config(mode=mode))
            for mode in ("conservative", "balanced", "tight")
        ]
        assert results[0].crop.area >= results[1].crop.area >= results[2].crop.area
        assert all(result.crop.contains(result.protected) for result in results)


def test_explicit_portrait_aspect_uses_format_reference_area():
    result = calculate_crop(600, 400, Box(200, 50, 300, 350), Config(aspect="4:5"))
    assert result.status == "cropped"
    assert abs(result.crop.height - result.crop.width / 0.8) <= 1
    assert result.retained_area < 0.85
    assert result.retained_reference_area >= 0.85
    assert result.requested_aspect == result.effective_aspect == "4:5"


def test_impossible_format_marks_review():
    result = calculate_crop(600, 400, Box(0, 0, 600, 400), Config(aspect="4:5"))
    assert result.status == "review_required"
    assert result.effective_aspect == "original"
    assert result.requested_aspect == "4:5"
    assert result.crop == Box(0, 0, 600, 400)
