"""Recursos locales y del bundle; nunca descarga durante el uso."""

import sys
from pathlib import Path


def resource_root():
    return (
        Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[3]
    )


def model_path():
    return resource_root() / "models/yolo11n.pt"
