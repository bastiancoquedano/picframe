import os
from pathlib import Path

import pytest
from PIL import Image

from raceframe.core.detection import YoloDetector


@pytest.mark.real_model
def test_real_cpu_inference(tmp_path, monkeypatch):
    model = os.environ.get("RACEFRAME_TEST_MODEL")
    if not model:
        pytest.skip("Inferencia real no ejecutada: falta RACEFRAME_TEST_MODEL")
    monkeypatch.setenv("RACEFRAME_RUNTIME_DIR", str(tmp_path / "runtime"))
    detector = YoloDetector(Path(model))
    with Image.new("RGB", (120, 80), "black") as image:
        assert detector.detect(image) == ()
    assert detector.runtime["device_effective"] == "cpu"
    assert len(detector.runtime["model_sha256"]) == 64


@pytest.mark.real_model
def test_real_people_and_original_coordinates(tmp_path, monkeypatch):
    model = os.environ.get("RACEFRAME_TEST_MODEL")
    if not model:
        pytest.skip("Inferencia real no ejecutada: falta RACEFRAME_TEST_MODEL")
    from importlib.metadata import distribution

    asset = Path(distribution("ultralytics").locate_file("ultralytics/assets/bus.jpg"))
    assert asset.is_file(), "Falta la muestra pública incluida por Ultralytics"
    monkeypatch.setenv("RACEFRAME_RUNTIME_DIR", str(tmp_path / "runtime"))
    detector = YoloDetector(Path(model))
    with Image.open(asset) as image:
        detections = detector.detect(image)
        assert detections
        assert all(
            d.class_name == "person"
            and 0 <= d.box.x1 < d.box.x2 <= image.width
            and 0 <= d.box.y1 < d.box.y2 <= image.height
            for d in detections
        )
