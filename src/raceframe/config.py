"""Configuración inmutable y reproducible; no realiza operaciones de salida."""

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields
from math import isclose, isfinite
from pathlib import Path


def _number(value: object, low: float, high: float) -> bool:
    return type(value) in (int, float) and low <= value <= high and isfinite(value)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Clave de configuración repetida: {key}")
        result[key] = value
    return result


@dataclass(frozen=True)
class Config:
    recursive: bool = False
    mode: str = "conservative"
    aspect: str = "original"
    margin: float = 0.08
    quality: int = 95
    device: str = "cpu"
    detection_confidence: float = 0.35
    selection_confidence: float = 0.50
    min_area: float = 0.005
    score_threshold: float = 0.55
    ambiguity_tolerance: float = 0.08
    center_tolerance: float = 0.03
    min_improvement: float = 0.005
    weights: tuple[float, ...] = (0.35, 0.25, 0.25, 0.15)
    retentions: tuple[float, ...] = (0.85, 0.70, 0.50)

    def __post_init__(self):
        if type(self.recursive) is not bool:
            raise ValueError("recursive debe ser booleano")
        for name, choices in (
            ("mode", ("conservative", "balanced", "tight")),
            ("aspect", ("original", "3:2", "4:5")),
            ("device", ("cpu", "mps", "auto")),
        ):
            if getattr(self, name) not in choices:
                raise ValueError(f"{name} no válido")
        if type(self.quality) is not int or not 1 <= self.quality <= 95:
            raise ValueError("quality debe ser un entero entre 1 y 95")
        if not _number(self.margin, 0, 0.5):
            raise ValueError("margin debe estar entre 0 y 0,5")
        for name in (
            "detection_confidence",
            "selection_confidence",
            "min_area",
            "score_threshold",
            "ambiguity_tolerance",
            "center_tolerance",
            "min_improvement",
        ):
            if not _number(getattr(self, name), 0, 1):
                raise ValueError(f"{name} debe ser un número finito entre 0 y 1")
        for name, length in (("weights", 4), ("retentions", 3)):
            values = getattr(self, name)
            if (
                not isinstance(values, (tuple, list))
                or len(values) != length
                or not all(_number(v, 0, 1) for v in values)
            ):
                raise ValueError(f"{name} tiene valores inválidos")
            object.__setattr__(self, name, tuple(values))
        if not isclose(sum(self.weights), 1, abs_tol=1e-9):
            raise ValueError("Los pesos deben sumar 1")
        a, b, c = self.retentions
        if not a >= b >= c > 0:
            raise ValueError("Las retenciones deben ser positivas y decrecientes")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_sources(cls, file_settings=None, overrides=None):
        merged = {}
        allowed = {f.name for f in fields(cls)}
        for source in (file_settings, overrides):
            if source is None:
                continue
            if not isinstance(source, Mapping) or any(k not in allowed for k in source):
                raise ValueError("Configuración no válida o con claves desconocidas")
            merged.update(source)
        return cls(**merged)

    @classmethod
    def from_file(cls, path: Path, overrides=None):
        try:
            values = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
        except (OSError, UnicodeError, ValueError) as exc:
            raise ValueError("No se pudo leer una configuración JSON válida") from exc
        if not isinstance(values, Mapping):
            raise ValueError("El archivo de configuración debe contener un objeto JSON")
        return cls.from_sources(values, overrides)
