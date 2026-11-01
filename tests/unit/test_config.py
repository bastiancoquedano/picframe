import json
from dataclasses import FrozenInstanceError

import pytest

from raceframe.config import Config


def test_defaults_and_serialization():
    c = Config()
    assert c.mode == "conservative"
    assert c.aspect == "original"
    assert c.quality == 95
    assert c.recursive is False
    assert c.weights == (0.35, 0.25, 0.25, 0.15)
    assert Config.from_sources(c.to_dict()) == c
    assert json.loads(json.dumps(c.to_dict(), allow_nan=False))["margin"] == 0.08


def test_precedence_and_no_mutation():
    source = {"quality": 80, "margin": 0.1}
    c = Config.from_sources(source, {"quality": 90})
    assert c.quality == 90 and c.margin == 0.1
    assert source["quality"] == 80
    with pytest.raises(FrozenInstanceError):
        c.quality = 40


@pytest.mark.parametrize(
    "data",
    [
        {"unknown": 1},
        {"quality": 0},
        {"quality": 96},
        {"quality": True},
        {"quality": 90.5},
        {"margin": -1},
        {"margin": 0.51},
        {"margin": float("nan")},
        {"margin": float("inf")},
        {"margin": "0.1"},
        {"recursive": "false"},
        {"recursive": 1},
        {"mode": "portrait"},
        {"aspect": "2:3"},
        {"device": "cuda"},
        {"weights": [1, 1, 1, 1]},
        {"weights": [-0.1, 0.5, 0.3, 0.3]},
        {"weights": [1]},
        {"retentions": [0.5, 0.7, 0.85]},
        {"retentions": [1.1, 0.7, 0.5]},
        {"retentions": [0, 0, 0]},
        {"score_threshold": float("nan")},
        {"detection_confidence": -0.01},
        {"ambiguity_tolerance": 2},
        {"min_area": True},
        {"center_tolerance": -0.1},
    ],
)
def test_invalid(data):
    with pytest.raises(ValueError):
        Config.from_sources(data)


def test_json_config_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text('{"quality": 82}')
    assert Config.from_file(path, {"quality": 88}).quality == 88
    for text in ["null", "true", "[]", '{"margin": NaN}', '{"quality": 70, "quality": 80}', "{bad"]:
        path.write_text(text)
        with pytest.raises(ValueError):
            Config.from_file(path)


def test_unbounded_integer_is_rejected_without_overflow():
    with pytest.raises(ValueError):
        Config(margin=10**1000)
