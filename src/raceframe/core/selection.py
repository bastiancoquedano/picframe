"""Puntuación configurable; no interpreta tamaño o aislamiento como identidad deportiva."""

from dataclasses import replace
from math import hypot, isfinite, sqrt

from raceframe.config import Config
from raceframe.core.models import Box, Selection, SelectionStatus


def _iou(a, b):
    intersection = max(0, min(a.x2, b.x2) - max(a.x1, b.x1)) * max(
        0, min(a.y2, b.y2) - max(a.y1, b.y1)
    )
    return intersection / (a.area + b.area - intersection) if intersection else 0


def select_subject(detections, width, height, config=None):
    config = config or Config()
    if width <= 0 or height <= 0:
        raise ValueError("Dimensiones inválidas para seleccionar sujeto")
    candidates = []
    rejected = []
    for detection in detections:
        box = detection.box
        if (
            not box.valid
            or not isfinite(detection.confidence)
            or not 0 <= detection.confidence <= 1
            or detection.class_name != "person"
        ):
            rejected.append(
                replace(detection, score=None, eligible=False, reasons=("invalid_detection",))
            )
            continue
        clipped = Box(max(0, box.x1), max(0, box.y1), min(width, box.x2), min(height, box.y2))
        if not clipped.valid or detection.confidence < config.detection_confidence:
            rejected.append(
                replace(detection, score=None, eligible=False, reasons=("low_confidence",))
            )
            continue
        notes = ("box_clipped",) if clipped != box else ()
        candidates.append(replace(detection, box=clipped, reasons=notes))
    scored = []
    for d in candidates:
        cx, cy = d.box.center
        factors = {
            "centrality": max(
                0, 1 - hypot(cx - width / 2, cy - height / 2) / hypot(width / 2, height / 2)
            ),
            "size": sqrt(d.box.area / (width * height)),
            "confidence": d.confidence,
            "isolation": 1
            - max((_iou(d.box, other.box) for other in candidates if other is not d), default=0),
        }
        score = sum(
            weight * value for weight, value in zip(config.weights, factors.values(), strict=True)
        )
        eligible = (
            d.confidence >= config.selection_confidence
            and d.box.area / (width * height) >= config.min_area
            and score >= config.score_threshold
        )
        scored.append(replace(d, score=score, factors=factors, eligible=eligible))
    ordered = sorted(
        scored, key=lambda d: (-d.score, -d.confidence, *d.box.as_tuple(), d.detection_id)
    )
    all_detections = tuple(scored + rejected)
    if not ordered:
        status = SelectionStatus.LOW_CONFIDENCE if rejected else SelectionStatus.NO_PERSON
        return Selection(status, all_detections, reasons=(status.value,))
    first = ordered[0]
    if not first.eligible:
        return Selection(
            SelectionStatus.LOW_CONFIDENCE, all_detections, reasons=("low_confidence",)
        )
    if len(ordered) > 1 and first.score - ordered[1].score <= config.ambiguity_tolerance:
        return Selection(SelectionStatus.AMBIGUOUS, all_detections, reasons=("ambiguous_subject",))
    return Selection(SelectionStatus.SELECTED, all_detections, first.detection_id)
