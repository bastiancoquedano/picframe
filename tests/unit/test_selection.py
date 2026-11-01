import pytest

from raceframe.config import Config
from raceframe.core.models import Box, Detection
from raceframe.core.selection import select_subject


def test_explained_selection_and_not_always_largest():
    detections = [
        Detection(0, Box(0, 0, 300, 400), 0.9),
        Detection(1, Box(450, 100, 550, 500), 0.98),
    ]
    result = select_subject(detections, 1000, 600)
    assert result.status == "selected"
    assert result.selected_id == 1
    assert set(result.detections[1].factors) == {"centrality", "size", "confidence", "isolation"}
    assert result.detections[1].eligible


def test_tie_and_order_invariance():
    a = Detection(0, Box(100, 100, 200, 500), 0.9)
    b = Detection(1, Box(800, 100, 900, 500), 0.9)
    for values in [(a, b), (b, a)]:
        result = select_subject(values, 1000, 600)
        assert result.status == "ambiguous"
        assert result.selected_id is None


@pytest.mark.parametrize(
    "values,status",
    [
        ([], "no_person"),
        ([Detection(0, Box(100, 100, 200, 400), 0.4)], "low_confidence"),
        ([Detection(0, Box(0, 0, float("nan"), 4), 0.9)], "low_confidence"),
        ([Detection(0, Box(0, 0, 0, 4), 0.9)], "low_confidence"),
    ],
)
def test_uncertainty(values, status):
    result = select_subject(values, 600, 400)
    assert result.status == status and result.selected_id is None


def test_clipping_and_configurable_score():
    result = select_subject(
        [Detection(0, Box(-10, 10, 300, 400), 0.99)], 600, 400, Config(score_threshold=0)
    )
    assert result.detections[0].box.x1 == 0
    assert "box_clipped" in result.detections[0].reasons
