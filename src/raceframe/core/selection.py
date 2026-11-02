"""Selección explicable por categoría: manual conservadora, dominante o grupo."""

from dataclasses import replace
from math import hypot, isfinite, sqrt

from raceframe.config import Config
from raceframe.core.categories import CLASSES
from raceframe.core.models import Box, Selection, SelectionStatus
from raceframe.core.subjects import build_candidates, union_boxes


def _iou(a, b):
    intersection = max(0, min(a.x2, b.x2) - max(a.x1, b.x1)) * max(
        0, min(a.y2, b.y2) - max(a.y1, b.y1)
    )
    return intersection / (a.area + b.area - intersection) if intersection else 0


def select_subject(detections, width, height, config=None, *, forced_id=None):
    config = config or Config()
    if width <= 0 or height <= 0:
        raise ValueError("Dimensiones inválidas para seleccionar sujeto")
    clean, rejected = [], []
    for d in detections:
        if (
            not d.box.valid
            or not isfinite(d.confidence)
            or not 0 <= d.confidence <= 1
            or d.class_name not in CLASSES.values()
        ):
            rejected.append(replace(d, score=None, eligible=False, reasons=("invalid_detection",)))
            continue
        b = d.box
        clipped = Box(max(0, b.x1), max(0, b.y1), min(width, b.x2), min(height, b.y2))
        if not clipped.valid or d.confidence < config.detection_confidence:
            rejected.append(replace(d, score=None, eligible=False, reasons=("low_confidence",)))
            continue
        clean.append(replace(d, box=clipped, reasons=("box_clipped",) if clipped != b else ()))
    candidates, associations = build_candidates(clean, config)
    by_primary = {c.primary_id: c for c in candidates}
    scored = []
    for d in clean:
        candidate = by_primary.get(d.detection_id)
        if candidate is None:
            scored.append(
                replace(
                    d,
                    score=None,
                    eligible=False,
                    reasons=(
                        *d.reasons,
                        "associated_member"
                        if any(d.detection_id in c.member_ids for c in candidates)
                        else "category_filtered",
                    ),
                )
            )
            continue
        box = candidate.box
        cx, cy = box.center
        factors = {
            "centrality": max(
                0, 1 - hypot(cx - width / 2, cy - height / 2) / hypot(width / 2, height / 2)
            ),
            "size": sqrt(box.area / (width * height)),
            "confidence": d.confidence,
            "isolation": 1
            - max((_iou(box, c.box) for c in candidates if c is not candidate), default=0),
        }
        score = sum(w * v for w, v in zip(config.weights, factors.values(), strict=True))
        eligible = (
            d.confidence >= config.selection_confidence
            and box.area / (width * height) >= config.min_area
        )
        if config.selection_strategy == "manual" and forced_id is None:
            eligible = eligible and score >= config.score_threshold
        scored.append(replace(d, score=score, factors=factors, eligible=eligible))
    all_detections = tuple(scored + rejected)
    primary = [d for d in scored if d.detection_id in by_primary]
    eligible = [d for d in primary if d.eligible]
    metrics = {
        "candidate_count": len(primary),
        "eligible_count": len(eligible),
        "dominance_ratio_required": config.dominance_ratio,
    }

    def result(status, chosen=(), reasons=(), group=False):
        ids = tuple(sorted({i for c in chosen for i in c.member_ids}))
        box = union_boxes(c.box for c in chosen) if chosen else None
        return Selection(
            status,
            all_detections,
            chosen[0].primary_id if chosen else None,
            tuple(reasons),
            ids,
            box,
            "group" if group else (chosen[0].kind if chosen else None),
            metrics,
            tuple(associations),
        )

    if forced_id is not None:
        candidate = by_primary.get(forced_id)
        if candidate is None:
            matches = [c for c in candidates if forced_id in c.member_ids]
            candidate = matches[0] if len(matches) == 1 else None
        if candidate is None:
            raise ValueError("La detección elegida no pertenece a la categoría o no es válida")
        return result(
            SelectionStatus.SELECTED,
            (candidate,),
            ("manual_selection", "ambiguous_association")
            if candidate.ambiguous
            else ("manual_selection",),
        )
    if not primary:
        status = (
            SelectionStatus.LOW_CONFIDENCE
            if rejected
            else (
                SelectionStatus.NO_PERSON
                if config.active_categories == ("people",)
                else SelectionStatus.NO_SUBJECT
            )
        )
        return result(status, reasons=(status.value,))
    if config.selection_strategy == "group":
        if not eligible:
            return result(SelectionStatus.LOW_CONFIDENCE, reasons=("low_confidence",))
        chosen = tuple(
            by_primary[d.detection_id] for d in sorted(eligible, key=lambda d: d.detection_id)
        )
        return result(SelectionStatus.SELECTED, chosen, ("group_selected",), group=True)
    if config.selection_strategy == "dominant":
        ordered = sorted(
            primary,
            key=lambda d: (-by_primary[d.detection_id].box.area, -d.confidence, d.detection_id),
        )
        first = ordered[0]
        if not first.eligible:
            return result(SelectionStatus.LOW_CONFIDENCE, reasons=("low_confidence",))
        # Comparar también candidatos detectados no elegibles evita ignorar un rival grande dudoso.
        if len(ordered) > 1:
            ratio = (
                by_primary[first.detection_id].box.area
                / by_primary[ordered[1].detection_id].box.area
            )
            metrics["dominance_ratio_observed"] = ratio
            if ratio < config.dominance_ratio:
                return result(SelectionStatus.AMBIGUOUS, reasons=("insufficient_size_dominance",))
        reasons = ("dominant_subject",)
    else:
        ordered = sorted(
            primary, key=lambda d: (-d.score, -d.confidence, *d.box.as_tuple(), d.detection_id)
        )
        first = ordered[0]
        if not first.eligible:
            return result(SelectionStatus.LOW_CONFIDENCE, reasons=("low_confidence",))
        if len(ordered) > 1 and first.score - ordered[1].score <= config.ambiguity_tolerance:
            return result(SelectionStatus.AMBIGUOUS, reasons=("ambiguous_subject",))
        reasons = ()
    chosen = by_primary[first.detection_id]
    if chosen.ambiguous:
        return result(SelectionStatus.AMBIGUOUS, reasons=("ambiguous_association",))
    if chosen.kind == "associated":
        reasons = (*reasons, "associated_subject")
    return result(SelectionStatus.SELECTED, (chosen,), reasons)
