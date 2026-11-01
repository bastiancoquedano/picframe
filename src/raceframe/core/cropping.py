"""Optimización geométrica conservadora; no carga imágenes ni modelos."""

from math import ceil, floor

from raceframe.config import Config
from raceframe.core.models import Box, Composition, CompositionStatus


def _nearest(value: float, low: int, high: int) -> int:
    return max(low, min(high, floor(value + 0.5)))


def calculate_crop(
    width: int,
    height: int,
    subject: Box | None,
    config: Config | None = None,
) -> Composition:
    """Recorta solo si mejora el centrado sin sacrificar la región protegida.

    Este primer incremento admite únicamente modo conservador y proporción original.
    Las otras opciones se rechazan explícitamente hasta completar US4.
    """
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("Las dimensiones deben ser enteros positivos")
    config = config or Config()
    if config.mode != "conservative" or config.aspect != "original":
        raise NotImplementedError("Este incremento solo admite conservador y proporción original")
    frame = Box(0, 0, width, height)
    if subject is None:
        return Composition(CompositionStatus.REVIEW_REQUIRED, frame, reasons=("no_subject",))
    if not subject.valid or not frame.contains(subject):
        raise ValueError("La caja del sujeto debe ser válida y estar dentro de la imagen")

    mx, my = config.margin * subject.width, config.margin * subject.height
    expanded = Box(subject.x1 - mx, subject.y1 - my, subject.x2 + mx, subject.y2 + my)
    protected = Box(
        floor(max(0, expanded.x1)),
        floor(max(0, expanded.y1)),
        ceil(min(width, expanded.x2)),
        ceil(min(height, expanded.y2)),
    )
    notes = () if frame.contains(expanded) else ("margin_clipped",)
    cx, _ = subject.center
    original_error = abs(cx - width / 2) / width
    if original_error <= config.center_tolerance:
        return Composition(
            CompositionStatus.UNCHANGED, frame, protected, (*notes, "already_centered")
        )

    min_area = width * height * config.retentions[0]
    best = None
    best_key = None
    # Enumerar un candidato x/y óptimo por tamaño evita barrer todos los píxeles.
    start_width = max(1, ceil(min_area / height), ceil(protected.width))
    for crop_width in range(start_width, width + 1):
        crop_height = floor(crop_width * height / width + 0.5)
        if not 1 <= crop_height <= height or crop_width * crop_height < min_area:
            continue
        xmin = max(0, ceil(protected.x2 - crop_width))
        xmax = min(width - crop_width, floor(protected.x1))
        ymin = max(0, ceil(protected.y2 - crop_height))
        ymax = min(height - crop_height, floor(protected.y1))
        if xmin > xmax or ymin > ymax:
            continue
        x = _nearest(cx - crop_width / 2, xmin, xmax)
        y = _nearest(height / 2 - crop_height / 2, ymin, ymax)
        error = abs(cx - (x + crop_width / 2)) / crop_width
        key = (
            round(error, 12),
            -crop_width * crop_height,
            abs(y + crop_height / 2 - height / 2),
            x,
            y,
        )
        if best_key is None or key < best_key:
            best_key = key
            best = Box(x, y, x + crop_width, y + crop_height)

    if best is None:
        return Composition(
            CompositionStatus.REVIEW_REQUIRED, frame, protected, (*notes, "infeasible_crop")
        )
    improvement = original_error - abs(cx - best.center[0]) / best.width
    if best == frame or improvement < config.min_improvement:
        return Composition(
            CompositionStatus.UNCHANGED, frame, protected, (*notes, "insufficient_improvement")
        )
    return Composition(
        CompositionStatus.CROPPED, best, protected, notes, retained_area=best.area / frame.area
    )
