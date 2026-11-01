"""Adaptador local de import tardío: un modelo por trabajo y ningún servicio externo."""

import os
import sys
from contextlib import redirect_stdout
from importlib.metadata import version
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol

from raceframe.config import Config
from raceframe.core.models import Box, Detection
from raceframe.export.jpeg import file_hash


class Detector(Protocol):
    def detect(self, image) -> tuple[Detection, ...]: ...


def _load_backend(model_path, runtime_dir):
    runtime_dir.mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_OFFLINE"] = "true"
    os.environ["YOLO_AUTOINSTALL"] = "false"
    os.environ["YOLO_CONFIG_DIR"] = str(runtime_dir / "ultralytics")
    os.environ["MPLCONFIGDIR"] = str(runtime_dir / "matplotlib")
    with redirect_stdout(sys.stderr):
        import cv2
        import numpy as np
        import torch
        from ultralytics import YOLO, settings
        from ultralytics.utils import ONLINE

        if ONLINE:
            raise RuntimeError(
                "Ultralytics fue importado previamente con red habilitada; reinicia el proceso"
            )
        disable = {
            key: False
            for key in (
                "sync",
                "clearml",
                "comet",
                "dvc",
                "mlflow",
                "raytune",
                "tensorboard",
                "wandb",
                "vscode_msg",
                "openvino_msg",
            )
            if key in settings
        }
        settings.update(disable)
        torch.set_num_threads(min(4, os.cpu_count() or 1))
        model = YOLO(str(model_path), task="detect")

    def convert(image):
        with image.convert("RGB") as rgb:
            return cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)

    return SimpleNamespace(
        model=model,
        convert_image=convert,
        mps_available=torch.backends.mps.is_available,
        versions={
            name: version(name)
            for name in ("ultralytics", "torch", "torchvision", "opencv-python", "numpy", "pillow")
        },
    )


class YoloDetector:
    def __init__(self, model_path, config=None, *, runtime_dir=None):
        config = config or Config()
        path = Path(model_path).expanduser().resolve(strict=False)
        if not path.is_file() or path.suffix.lower() != ".pt":
            raise ValueError("Se requieren pesos .pt locales existentes")
        self.config = config
        directory = Path(
            runtime_dir
            or os.environ.get(
                "RACEFRAME_RUNTIME_DIR", Path.home() / "Library/Application Support/Raceframe"
            )
        )
        self.backend = _load_backend(path, directory)
        self.device = "cpu"
        self.warnings = []
        if config.device in ("auto", "mps"):
            if self.backend.mps_available():
                self.device = "mps"
            elif config.device == "mps":
                raise RuntimeError("MPS no está disponible; utiliza CPU o auto")
            else:
                self.warnings.append("cpu_fallback")
        from PIL import Image

        try:
            with Image.new("RGB", (32, 32)) as probe:
                self._predict(probe)
        except Exception:
            if config.device != "auto" or self.device == "cpu":
                raise
            self.device = "cpu"
            self.warnings.append("cpu_fallback")
            with Image.new("RGB", (32, 32)) as probe:
                self._predict(probe)
        self.runtime = {
            "model": path.name,
            "model_sha256": file_hash(path),
            "model_path": str(path),
            "device_requested": config.device,
            "device_effective": self.device,
            "inference_size": 640,
            "versions": self.backend.versions,
            "warnings": self.warnings,
        }

    def _predict(self, image):
        source = self.backend.convert_image(image)
        with redirect_stdout(sys.stderr):
            return self.backend.model.predict(
                source=source,
                device=self.device,
                imgsz=640,
                classes=[0],
                conf=self.config.detection_confidence,
                verbose=False,
                save=False,
                show=False,
            )

    def detect(self, image):
        results = self._predict(image)
        if len(results) != 1 or tuple(results[0].orig_shape) != (image.height, image.width):
            raise ValueError("El detector devolvió dimensiones de coordenadas inesperadas")
        boxes = results[0].boxes
        detections = []
        for coords, confidence, class_id in zip(
            boxes.xyxy.tolist(), boxes.conf.tolist(), boxes.cls.tolist(), strict=True
        ):
            if int(class_id) == 0:
                detections.append(Detection(len(detections), Box(*coords), float(confidence)))
        return tuple(detections)
