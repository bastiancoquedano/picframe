"""Correcciones humanas sobre los contratos geométricos del motor."""

from copy import deepcopy
from math import ceil, floor

from raceframe.core.models import Box, Detection
from raceframe.core.processing import apply_selection
from raceframe.core.selection import select_subject


def needs_review(row):
    return (
        bool(row.get("error"))
        or row.get("operation_status") == "error"
        or row.get("selection_status") != "selected"
        or (row.get("composition") or {}).get("status") not in {"cropped", "unchanged"}
    )


def aspect_box(start, end, size, ratio):
    width, height = size
    ax, ay = (max(0, min(start[0], width)), max(0, min(start[1], height)))
    dx, dy = end[0] - ax, end[1] - ay
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    roomx = width - ax if sx > 0 else ax
    roomy = height - ay if sy > 0 else ay
    w = floor(min(max(abs(dx), abs(dy) * ratio), roomx, roomy * ratio))
    h = floor(w / ratio + 0.5)
    x1, x2 = sorted((round(ax), round(ax + sx * w)))
    y1, y2 = sorted((round(ay), round(ay + sy * h)))
    return Box(x1, y1, x2, y2)


def select_detection(row, detection_id, config):
    values = [Detection(**{**d, "box": Box(**d["box"])}) for d in row["detections"]]
    width, height = row["source"]["oriented_dimensions"]
    selection = select_subject(values, width, height, config, forced_id=detection_id)
    result = deepcopy(row)
    apply_selection(result, selection, config)
    result.update(manual_selection=True, manual_crop=False)
    return result


def manual_crop(row, box, config):
    width, height = row["source"]["oriented_dimensions"]
    if row.get("selected_detection_id") is None or not row.get("composition"):
        raise ValueError("Selecciona un sujeto antes de ajustar el recorte")
    protected = row["composition"].get("protected")
    if (
        not box.valid
        or any(int(v) != v for v in box.as_tuple())
        or not Box(0, 0, width, height).contains(box)
    ):
        raise ValueError("El recorte debe estar dentro de la fotografía")
    ratio = {"original": width / height, "3:2": 1.5, "4:5": 0.8}[config.aspect]
    if abs(box.height - box.width / ratio) > 1:
        raise ValueError("El recorte debe conservar la proporción elegida")
    if protected and not box.contains(Box(**protected)):
        raise ValueError("El recorte debe incluir al sujeto y su margen de seguridad")
    if max(box.width, box.height) < min(config.min_long_edge, max(width, height)):
        raise ValueError("El recorte no alcanza la resolución mínima elegida")
    result = deepcopy(row)
    result["manual_crop"] = True
    result["crop_xyxy"] = list(box.as_tuple())
    result["composition"].update(
        crop=list(box.as_tuple()),
        status="unchanged" if box == Box(0, 0, width, height) else "cropped",
        reasons=["manual_crop"],
        retained_area=box.area / (width * height),
    )
    result["composition"]["effective_aspect"] = config.aspect
    reference_width = min(width, ceil((height + 0.5) * ratio) - 1)
    reference_height = min(height, floor(reference_width / ratio + 0.5))
    result["composition"]["retained_reference_area"] = box.area / (
        reference_width * reference_height
    )
    if row.get("subject_box"):
        subject = Box(*row["subject_box"])
    else:
        selected = next(
            d for d in row["detections"] if d["detection_id"] == row["selected_detection_id"]
        )
        subject = Box(**selected["box"])
    result["source"]["subject_height_fraction_output"] = subject.height / box.height
    result["source"]["estimated_head_fraction_output"] = (
        (subject.y1 - box.y1) / box.height if row["source"].get("head_reference") else None
    )
    result["warnings"] = ["manual_crop"]
    return result
