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
    subject_category: str = "people"
    subject_categories: tuple[str, ...] | None = None
    selection_strategy: str = "manual"
    dominance_ratio: float = 1.5
    recursive: bool = False
    mode: str = "conservative"
    aspect: str = "original"
    framing_policy: str = "focal"
    focal_threshold: float = 70.0
    target_occupancy: float = 0.75
    composition_priority: str = "headroom"
    head_fraction: float = 1 / 3
    min_long_edge: int = 3000
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

    @property
    def active_categories(self):
        return (
            self.subject_categories
            if self.subject_categories is not None
            else (self.subject_category,)
        )

    def __post_init__(self):
        if self.subject_categories is not None:
            values = self.subject_categories
            if (
                not isinstance(values, (list, tuple))
                or not values
                or any(
                    not isinstance(v, str) or v not in ("people", "animals", "vehicles")
                    for v in values
                )
            ):
                raise ValueError("Selecciona al menos una categoría válida de sujetos")
            object.__setattr__(
                self,
                "subject_categories",
                tuple(
                    category for category in ("people", "animals", "vehicles") if category in values
                ),
            )
        if self.subject_category not in ("people", "animals", "vehicles"):
            raise ValueError("Categoría de sujeto inválida")
        if self.selection_strategy not in ("manual", "dominant", "group"):
            raise ValueError("Estrategia de selección inválida")
        if not _number(self.dominance_ratio, 1.01, 100):
            raise ValueError("La ventaja de tamaño debe estar entre 1,01 y 100")
        if type(self.recursive) is not bool:
            raise ValueError("recursive debe ser booleano")
        for name, choices in (
            ("mode", ("conservative", "balanced", "tight")),
            ("aspect", ("original", "3:2", "4:5")),
            ("device", ("cpu", "mps", "auto")),
        ):
            if getattr(self, name) not in choices:
                raise ValueError(f"{name} no válido")
        if self.composition_priority not in ("headroom", "occupancy"):
            raise ValueError("Prioridad de composición inválida")
        if not _number(self.head_fraction, 0.1, 0.5):
            raise ValueError("La posición de cabeza debe estar entre 0,1 y 0,5")
        if self.framing_policy not in ("focal", "context"):
            raise ValueError("Política de encuadre inválida")
        if not _number(self.focal_threshold, 1, 2000) or not _number(
            self.target_occupancy, 0.1, 0.9
        ):
            raise ValueError("Umbral focal u ocupación inválidos")
        if type(self.min_long_edge) is not int or self.min_long_edge < 1:
            raise ValueError("La resolución mínima debe ser un entero positivo")
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
            if "subject_category" in source and "subject_categories" not in source:
                merged.pop("subject_categories", None)
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
