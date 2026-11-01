import pytest

from raceframe.config import Config
from raceframe.core.models import Box
from raceframe.ui.decisions import aspect_box, manual_crop, select_detection


def row():
    return {
        "image_id": "synthetic.jpg",
        "source": {"oriented_dimensions": [800, 1200], "focal_length_mm": 100},
        "detections": [
            {
                "detection_id": 0,
                "box": {"x1": 300, "y1": 400, "x2": 450, "y2": 900},
                "confidence": 0.9,
                "reasons": [],
            },
            {
                "detection_id": 1,
                "box": {"x1": 100, "y1": 300, "x2": 250, "y2": 800},
                "confidence": 0.8,
                "reasons": [],
            },
        ],
        "selection_status": "ambiguous",
        "selected_detection_id": None,
        "warnings": ["ambiguous_subject"],
        "composition": None,
    }


def test_select_and_manual_crop_safe():
    config = Config(min_long_edge=300)
    original = row()
    selected = select_detection(original, 0, config)
    assert original["selected_detection_id"] is None
    assert selected["selected_detection_id"] == 0
    assert selected["manual_selection"] is True
    revised = manual_crop(selected, Box(0, 0, 800, 1200), config)
    assert revised["manual_crop"] is True
    assert revised["crop_xyxy"] == [0, 0, 800, 1200]
    assert revised["source"]["subject_height_fraction_output"] == 500 / 1200
    assert revised["source"]["estimated_head_fraction_output"] == 400 / 1200
    for crop in [Box(-1, 0, 799, 1200), Box(0, 0, 200, 300), Box(0, 0, 800, 800)]:
        with pytest.raises(ValueError):
            manual_crop(selected, crop, config)
    with pytest.raises(ValueError):
        manual_crop(original, Box(0, 0, 800, 1200), config)


def test_aspect_drag_is_bounded_in_both_directions():
    for start, end in [
        ((100, 100), (700, 1000)),
        ((700, 1000), (100, 100)),
        ((600, 900), (1000, 1500)),
    ]:
        box = aspect_box(start, end, (800, 1200), 2 / 3)
        assert Box(0, 0, 800, 1200).contains(box)
        assert abs(box.height - box.width * 1.5) <= 1
