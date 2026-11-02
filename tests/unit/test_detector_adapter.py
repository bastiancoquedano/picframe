from types import SimpleNamespace

import pytest
from PIL import Image

import raceframe.core.detection as module
from raceframe.config import Config


class Values:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


class Model:
    def __init__(self):
        self.calls = []
        self.names = dict(module.CLASSES)

    def predict(self, source, **kwargs):
        self.calls.append(kwargs)
        w, h = source
        boxes = SimpleNamespace(
            cls=Values([0, 2]),
            conf=Values([0.9, 0.8]),
            xyxy=Values([[1, 2, w - 1, h - 1], [0, 0, 5, 5]]),
        )
        return [SimpleNamespace(orig_shape=(h, w), boxes=boxes)]


def test_adapter_coordinates_class_and_load_once(tmp_path, monkeypatch):
    path = tmp_path / "local.pt"
    path.write_bytes(b"model")
    model = Model()
    calls = []
    backend = SimpleNamespace(
        model=model,
        convert_image=lambda image: image.size,
        mps_available=lambda: False,
        versions={},
    )

    def load(*args):
        calls.append(args)
        return backend

    monkeypatch.setattr(module, "_load_backend", load)
    detector = module.YoloDetector(path, Config(), runtime_dir=tmp_path / "runtime")
    with Image.new("RGB", (120, 80)) as image:
        detections = detector.detect(image)
    assert len(calls) == 1
    assert len(detections) == 1
    assert detections[0].box.as_tuple() == (1, 2, 119, 79)
    assert len(model.calls) == 2  # preparación + fotografía
    assert all(call["classes"] == [0, 1, 3, 17] and call["device"] == "cpu" for call in model.calls)


def test_missing_model_before_backend(tmp_path, monkeypatch):
    def fail(*args):
        raise AssertionError("no debe cargar backend")

    monkeypatch.setattr(module, "_load_backend", fail)
    with pytest.raises(ValueError):
        module.YoloDetector(tmp_path / "missing.pt")


def test_adapter_preserves_vehicle_class_and_rejects_custom_names(tmp_path, monkeypatch):
    path = tmp_path / "model.pt"
    path.write_bytes(b"model")
    model = Model()
    backend = SimpleNamespace(
        model=model,
        convert_image=lambda image: image.size,
        mps_available=lambda: False,
        versions={},
    )
    monkeypatch.setattr(module, "_load_backend", lambda *a: backend)
    detector = module.YoloDetector(path, Config(subject_category="vehicles"), runtime_dir=tmp_path)
    with Image.new("RGB", (120, 80)) as image:
        values = detector.detect(image)
    assert [(v.class_id, v.class_name) for v in values] == [(0, "person"), (2, "car")]
    assert model.calls[-1]["classes"] == list(range(9))
    model.names[2] = "custom_label"
    with pytest.raises(ValueError, match="COCO"):
        module.YoloDetector(path, Config(subject_category="vehicles"), runtime_dir=tmp_path)


def test_adapter_automatic_and_combined_class_filters(tmp_path, monkeypatch):
    path = tmp_path / "model.pt"
    path.write_bytes(b"model")
    model = Model()
    backend = SimpleNamespace(
        model=model,
        convert_image=lambda image: image.size,
        mps_available=lambda: False,
        versions={},
    )
    monkeypatch.setattr(module, "_load_backend", lambda *a: backend)
    module.YoloDetector(
        path, Config(subject_categories=("people", "animals", "vehicles")), runtime_dir=tmp_path
    )
    assert model.calls[-1]["classes"] == list(module.CLASSES)
    module.YoloDetector(
        path, Config(subject_categories=("people", "animals")), runtime_dir=tmp_path
    )
    assert 16 in model.calls[-1]["classes"]  # perro activo
    assert 2 not in model.calls[-1]["classes"]  # auto excluido
    assert 1 in model.calls[-1]["classes"]  # bicicleta auxiliar protegida
