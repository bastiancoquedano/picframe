from dataclasses import replace

import pytest

from raceframe.config import Config
from raceframe.core.models import Box, Detection
from raceframe.core.selection import select_subject


def d(i, box, name="person", confidence=0.95):
    return Detection(i, Box(*box), confidence, class_name=name)


@pytest.mark.parametrize(
    "settings",
    [
        {"subject_category": "food"},
        {"selection_strategy": "largest"},
        {"dominance_ratio": 1},
        {"dominance_ratio": float("nan")},
    ],
)
def test_general_configuration_rejects_invalid(settings):
    with pytest.raises(ValueError):
        Config(**settings)


def test_category_excludes_large_parked_car():
    values = [d(0, (0, 0, 900, 500), "car"), d(1, (450, 100, 550, 500))]
    cfg = Config(selection_strategy="dominant")
    assert select_subject(values, 1000, 600, cfg).selected_id == 1
    assert (
        select_subject(values, 1000, 600, replace(cfg, subject_category="vehicles")).selected_id
        == 0
    )
    assert (
        select_subject(values, 1000, 600, replace(cfg, subject_category="animals")).status
        == "no_subject"
    )


def test_dominant_prefers_clearly_larger_side_subject_and_ties_remain_ambiguous():
    cfg = Config(selection_strategy="dominant")
    a = d(0, (0, 0, 300, 500))
    b = d(1, (450, 100, 550, 500))
    result = select_subject([a, b], 1000, 600, cfg)
    assert result.selected_id == 0
    assert result.metrics["dominance_ratio_observed"] == 3.75
    for values in ([a, d(1, (700, 0, 1000, 500))], [d(1, (700, 0, 1000, 500)), a]):
        assert select_subject(values, 1000, 600, cfg).status == "ambiguous"


def test_group_protects_all_eligible_targets():
    values = [d(0, (0, 100, 200, 500)), d(1, (700, 80, 980, 550))]
    result = select_subject(values, 1000, 600, Config(selection_strategy="group"))
    assert result.status == "selected" and result.subject_kind == "group"
    assert result.selected_ids == (0, 1)
    assert result.subject_box == Box(0, 80, 980, 550)


@pytest.mark.parametrize(
    "companion,category", [("bicycle", "people"), ("horse", "animals"), ("motorcycle", "vehicles")]
)
def test_associated_subject_contains_both_members(companion, category):
    person = d(0, (220, 100, 420, 550))
    partner = d(1, (100, 350, 650, 650), companion)
    cfg = Config(subject_category=category, selection_strategy="dominant")
    result = select_subject([person, partner], 1000, 800, cfg)
    assert result.status == "selected"
    assert result.subject_kind == "associated"
    assert set(result.selected_ids) == {0, 1}
    assert result.subject_box.contains(person.box) and result.subject_box.contains(partner.box)
    assert result.associations


def test_competing_associations_require_review_but_manual_keeps_companions():
    values = [
        d(0, (220, 100, 420, 550)),
        d(1, (100, 350, 650, 650), "bicycle"),
        d(2, (300, 350, 800, 650), "bicycle"),
    ]
    cfg = Config(selection_strategy="dominant")
    assert select_subject(values, 1000, 800, cfg).status == "ambiguous"
    manual = select_subject(values, 1000, 800, cfg, forced_id=0)
    assert manual.status == "selected"
    assert set(manual.selected_ids) == {0, 1, 2}
    assert "ambiguous_association" in manual.reasons


def test_nearby_nonoverlapping_bike_is_not_associated():
    result = select_subject(
        [d(0, (100, 100, 250, 600)), d(1, (500, 350, 900, 700), "bicycle")],
        1000,
        800,
        Config(selection_strategy="dominant"),
    )
    assert result.subject_kind == "individual"
    assert result.selected_ids == (0,)


def test_group_ignores_low_confidence_targets():
    values = [d(0, (100, 100, 300, 500)), d(1, (600, 100, 800, 500), confidence=0.4)]
    result = select_subject(values, 1000, 600, Config(selection_strategy="group"))
    assert result.selected_ids == (0,)
