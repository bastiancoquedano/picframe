"""Datos sintéticos; nunca incorporar fotografías privadas al repositorio."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest


@dataclass
class FakeDetector:
    detections: list = field(default_factory=list)
    calls: int = 0

    def detect(self, image):
        self.calls += 1
        return tuple(self.detections)


@pytest.fixture
def fake_detector():
    return FakeDetector()


@pytest.fixture
def photo_factory(tmp_path):
    def make(name="photo.jpg", *, size=(120, 80), orientation=None):
        from PIL import Image, ImageDraw

        path: Path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        image = Image.new("RGB", size, "black")
        draw = ImageDraw.Draw(image)
        w, h = size
        draw.rectangle((0, 0, w // 2 - 1, h // 2 - 1), fill="red")
        draw.rectangle((w // 2, 0, w - 1, h // 2 - 1), fill="green")
        draw.rectangle((0, h // 2, w // 2 - 1, h - 1), fill="blue")
        draw.rectangle((w // 2, h // 2, w - 1, h - 1), fill="white")
        exif = Image.Exif()
        if orientation is not None:
            exif[274] = orientation
        exif[271] = "Synthetic Camera"
        image.save(path, quality=95, exif=exif)
        image.close()
        return path

    return make
