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
    """Prioriza integridad y contexto con un solo motor para todos los modos."""
    if type(width) is not int or type(height) is not int or width <= 0 or height <= 0:
        raise ValueError("Las dimensiones deben ser enteros positivos")
    config = config or Config()
    frame = Box(0, 0, width, height)
    ratio = {"original": width / height, "3:2": 1.5, "4:5": 0.8}[config.aspect]
    reference_width = min(width, ceil((height + 0.5) * ratio) - 1)
    reference_height = min(height, floor(reference_width / ratio + 0.5))
    reference_area = max(1, reference_width * reference_height)

    def result(status, crop, protected=None, reasons=()):
        margins = (
            ()
            if subject is None or protected is None
            else (
                subject.x1 - protected.x1,
                subject.y1 - protected.y1,
                protected.x2 - subject.x2,
                protected.y2 - subject.y2,
            )
        )
        return Composition(
            status=status,
            crop=crop,
            protected=protected,
            reasons=reasons,
            retained_area=crop.area / frame.area,
            retained_reference_area=crop.area
            / (frame.area if status == CompositionStatus.REVIEW_REQUIRED else reference_area),
            margin_requested=config.margin,
            margin_effective_pixels=margins,
            mode=config.mode,
            requested_aspect=config.aspect,
            effective_aspect="original"
            if status == CompositionStatus.REVIEW_REQUIRED
            else config.aspect,
        )

    if subject is None:
        return result(CompositionStatus.REVIEW_REQUIRED, frame, reasons=("no_subject",))
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
    if config.aspect == "original" and original_error <= config.center_tolerance:
        return result(CompositionStatus.UNCHANGED, frame, protected, (*notes, "already_centered"))

    mode_index = ("conservative", "balanced", "tight").index(config.mode)
    min_area = reference_area * config.retentions[mode_index]
    best = None
    best_key = None
    # Enumerar un candidato x/y óptimo por tamaño evita barrer todos los píxeles.
    start_width = max(1, ceil(min_area / height), ceil(protected.width))
    for crop_width in range(start_width, reference_width + 1):
        crop_height = floor(crop_width / ratio + 0.5)
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
        return result(
            CompositionStatus.REVIEW_REQUIRED, frame, protected, (*notes, "infeasible_crop")
        )
    improvement = original_error - abs(cx - best.center[0]) / best.width
    if best == frame or (config.aspect == "original" and improvement < config.min_improvement):
        return result(
            CompositionStatus.UNCHANGED, frame, protected, (*notes, "insufficient_improvement")
        )
    return result(CompositionStatus.CROPPED, best, protected, notes)


def calculate_focal_crop(width, height, subject, config, focal_mm=None, *, person=True):
    """Teleobjetivo: ocupación objetivo; angular/focal ausente: contexto."""
    if (
        subject is None
        or config.framing_policy == "context"
        or focal_mm is None
        or focal_mm < config.focal_threshold
    ):
        return calculate_crop(width, height, subject, config)
    if not subject.valid or not Box(0, 0, width, height).contains(subject):
        raise ValueError("Caja fuera de imagen")
    ratio = {"original": width / height, "3:2": 1.5, "4:5": 0.8}[config.aspect]
    protected = Box(
        floor(max(0, subject.x1 - subject.width * config.margin)),
        floor(max(0, subject.y1 - subject.height * config.margin)),
        ceil(min(width, subject.x2 + subject.width * config.margin)),
        ceil(min(height, subject.y2 + subject.height * config.margin)),
    )
    max_width = min(width, ceil((height + 0.5) * ratio) - 1)
    min_edge = min(config.min_long_edge, max(width, height))
    start = max(1, ceil(protected.width), ceil(min_edge / max(1, 1 / ratio)))
    best = None
    best_key = None
    for w in range(start, max_width + 1):
        h = floor(w / ratio + 0.5)
        if h < protected.height or h > height or max(w, h) < min_edge:
            continue
        xmin = max(0, ceil(protected.x2 - w))
        xmax = min(width - w, floor(protected.x1))
        ymin = max(0, ceil(protected.y2 - h))
        ymax = min(height - h, floor(protected.y1))
        if xmin > xmax or ymin > ymax:
            continue
        x = _nearest(subject.center[0] - w / 2, xmin, xmax)
        target_y = (
            subject.y1 - config.head_fraction * h
            if person and config.composition_priority == "headroom"
            else subject.center[1] - h / 2
        )
        y = _nearest(target_y, ymin, ymax)
        head_error = abs(subject.y1 - y - config.head_fraction * h)
        occupancy = subject.height / h if person else max(subject.width / w, subject.height / h)
        key = (
            abs(occupancy - config.target_occupancy),
            abs(subject.center[0] - (x + w / 2)) / w,
            -w * h,
            x,
            y,
        )
        if person and config.composition_priority == "headroom":
            key = (0 if head_error <= 1 else 1, 0 if head_error <= 1 else head_error / h, *key)
        if best_key is None or key < best_key:
            best_key = key
            best = Box(x, y, x + w, y + h)
    if best is None:
        return Composition(
            CompositionStatus.REVIEW_REQUIRED,
            Box(0, 0, width, height),
            protected,
            ("focal_framing_infeasible",),
            mode=config.mode,
            requested_aspect=config.aspect,
            effective_aspect="original",
        )
    notes = ["focal_subject_priority" if person else "object_axis_occupancy_priority"]
    if person and config.composition_priority == "headroom":
        notes.append("head_upper_third_priority")
        if abs(subject.y1 - best.y1 - config.head_fraction * best.height) > 1:
            notes.append("headroom_limited_by_safety_or_bounds")
        if subject.height / best.height < config.target_occupancy - 0.05:
            notes.append("occupancy_yielded_to_headroom")
    elif (
        subject.height / best.height
        if person
        else max(subject.width / best.width, subject.height / best.height)
    ) < config.target_occupancy - 0.05:
        notes.append("occupancy_limited_by_resolution_or_safety")
    return Composition(
        status=CompositionStatus.UNCHANGED
        if best == Box(0, 0, width, height)
        else CompositionStatus.CROPPED,
        crop=best,
        protected=protected,
        reasons=tuple(notes),
        retained_area=best.area / (width * height),
        margin_requested=config.margin,
        mode=config.mode,
        requested_aspect=config.aspect,
        effective_aspect=config.aspect,
    )
