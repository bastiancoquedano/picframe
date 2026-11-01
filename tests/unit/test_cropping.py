import json
import random
import subprocess
import sys

import pytest

from raceframe.config import Config
from raceframe.core.cropping import calculate_crop
from raceframe.core.models import Box, CompositionStatus


def error(subject, crop):
    return abs(subject.center[0] - crop.center[0]) / crop.width


def test_centered_unchanged():
    result = calculate_crop(600, 400, Box(270, 40, 330, 360))
    assert result.status == CompositionStatus.UNCHANGED
    assert result.crop == Box(0, 0, 600, 400)


@pytest.mark.parametrize("subject", [Box(120, 80, 180, 320), Box(420, 80, 480, 320)])
def test_lateral_improves_with_context(subject):
    result = calculate_crop(600, 400, subject)
    assert result.status == CompositionStatus.CROPPED
    assert result.retained_area >= 0.85
    assert error(subject, result.crop) < error(subject, Box(0, 0, 600, 400))
    assert result.crop.contains(result.protected)
    assert abs(result.crop.height - result.crop.width / 1.5) <= 1


def test_full_height_near_border_has_priority_over_centering():
    subject = Box(0, 0, 90, 400)
    result = calculate_crop(600, 400, subject)
    assert result.crop == Box(0, 0, 600, 400)
    assert result.crop.contains(subject)
    assert "margin_clipped" in result.reasons


def test_partial_body_not_forced_to_full_body():
    subject = Box(120, 0, 200, 210)
    result = calculate_crop(600, 400, subject)
    assert result.crop.contains(subject)
    assert result.crop.contains(result.protected)
    assert result.crop.y1 == 0


def test_safety_region_rounds_outward():
    result = calculate_crop(600, 400, Box(120.1, 70.1, 179.9, 320.3))
    assert result.protected.x1 == 115
    assert result.protected.x2 == 185
    assert result.crop.contains(result.protected)


def test_missing_subject_requires_review():
    result = calculate_crop(600, 400, None)
    assert result.status == CompositionStatus.REVIEW_REQUIRED
    assert result.crop == Box(0, 0, 600, 400)
    assert "no_subject" in result.reasons


@pytest.mark.parametrize("width,height", [(400, 600), (601, 399), (7, 9), (1, 1)])
def test_portrait_odd_and_small_dimensions(width, height):
    subject = Box(0, 0, width, height)
    result = calculate_crop(width, height, subject)
    assert result.crop == Box(0, 0, width, height)


@pytest.mark.parametrize(
    "box",
    [
        Box(0, 0, 0, 30),
        Box(-1, 0, 40, 50),
        Box(0, 0, 601, 30),
        Box(0, 0, float("nan"), 30),
        Box(0, 0, float("inf"), 40),
    ],
)
def test_invalid_box(box):
    with pytest.raises(ValueError):
        calculate_crop(600, 400, box)


@pytest.mark.parametrize("width,height", [(0, 10), (-1, 10), (10, 0), (True, 2), (1.5, 3)])
def test_invalid_dimensions(width, height):
    with pytest.raises(ValueError):
        calculate_crop(width, height, None)


def test_many_boxes_respect_geometry_and_context():
    rng = random.Random(52)
    for _ in range(200):
        w, h = rng.randint(20, 800), rng.randint(20, 800)
        x1, x2 = sorted(rng.sample(range(w + 1), 2))
        y1, y2 = sorted(rng.sample(range(h + 1), 2))
        subject = Box(x1, y1, x2, y2)
        result = calculate_crop(w, h, subject)
        frame = Box(0, 0, w, h)
        assert frame.contains(result.crop)
        assert result.crop.contains(result.protected)
        assert result.retained_area >= 0.85
        assert all(int(v) == v for v in result.crop.as_tuple())
        assert abs(result.crop.height - result.crop.width * h / w) <= 1
        assert error(subject, result.crop) <= error(subject, frame) + 1e-12


def test_mirrored_inputs_produce_mirrored_crops():
    left = calculate_crop(600, 400, Box(120, 80, 180, 320)).crop
    right = calculate_crop(600, 400, Box(420, 80, 480, 320)).crop
    assert left.x1 == 600 - right.x2
    assert left.x2 == 600 - right.x1


def test_import_does_not_load_image_or_detector_libraries():
    code = "import sys,json; import raceframe.core.cropping; print(json.dumps(sorted(sys.modules)))"
    modules = json.loads(subprocess.check_output([sys.executable, "-c", code], text=True))
    for prefix in ["PIL", "cv2", "torch", "ultralytics", "PySide6"]:
        assert not any(m == prefix or m.startswith(prefix + ".") for m in modules)


def test_rounding_does_not_exclude_valid_narrower_sizes():
    result = calculate_crop(1000, 1, Box(100, 0, 200, 1), Config(margin=0))
    assert result.crop.width == 850
    assert result.retained_area == 0.85
