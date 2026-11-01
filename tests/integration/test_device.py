from types import SimpleNamespace

import pytest

import raceframe.core.detection as module
from raceframe.config import Config


@pytest.mark.parametrize(
    "requested,available,expected",
    [("auto", False, "cpu"), ("auto", True, "mps"), ("mps", True, "mps")],
)
def test_device_selection(tmp_path, monkeypatch, requested, available, expected):
    path = tmp_path / "local.pt"
    path.write_bytes(b"model")
    backend = SimpleNamespace(mps_available=lambda: available, versions={})
    monkeypatch.setattr(module, "_load_backend", lambda *a: backend)
    monkeypatch.setattr(module.YoloDetector, "_predict", lambda *a: [])
    detector = module.YoloDetector(path, Config(device=requested))
    assert detector.device == expected


def test_explicit_mps_failure_and_auto_fallback(tmp_path, monkeypatch):
    path = tmp_path / "local.pt"
    path.write_bytes(b"model")
    backend = SimpleNamespace(mps_available=lambda: True, versions={})
    monkeypatch.setattr(module, "_load_backend", lambda *a: backend)

    def predict(self, image):
        if self.device == "mps":
            raise RuntimeError("unsupported operation")
        return []

    monkeypatch.setattr(module.YoloDetector, "_predict", predict)
    assert module.YoloDetector(path, Config(device="auto")).device == "cpu"
    with pytest.raises(RuntimeError):
        module.YoloDetector(path, Config(device="mps"))
