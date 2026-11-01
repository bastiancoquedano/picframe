"""Correcciones humanas sobre los contratos geométricos del motor."""

from copy import deepcopy
from dataclasses import asdict
from math import ceil, floor

from raceframe.core.cropping import calculate_focal_crop
from raceframe.core.models import Box


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
    selected = next((d for d in row["detections"] if d["detection_id"] == detection_id), None)
    if selected is None or "invalid_detection" in selected.get("reasons", []):
        raise ValueError("La detección elegida no es válida")
    box = Box(**selected["box"])
    width, height = row["source"]["oriented_dimensions"]
    if not box.valid or not Box(0, 0, width, height).contains(box):
        raise ValueError("La persona no tiene una región válida")
    result = deepcopy(row)
    comp = calculate_focal_crop(width, height, box, config, row["source"].get("focal_length_mm"))
    result.update(
        selected_detection_id=detection_id,
        selection_status="selected",
        manual_selection=True,
        manual_crop=False,
        composition=asdict(comp),
        crop_xyxy=list(comp.crop.as_tuple()),
    )
    result["composition"]["crop"] = list(comp.crop.as_tuple())
    result["warnings"] = [*comp.reasons, "manual_selection"]
    result["source"]["subject_height_fraction_original"] = box.height / height
    result["source"]["subject_height_fraction_output"] = box.height / comp.crop.height
    result["source"]["estimated_head_fraction_output"] = (box.y1 - comp.crop.y1) / comp.crop.height
    return result


def manual_crop(row, box, config):
    width, height = row["source"]["oriented_dimensions"]
    if row.get("selected_detection_id") is None or not row.get("composition"):
        raise ValueError("Selecciona una persona antes de ajustar el recorte")
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
    selected = next(
        d for d in row["detections"] if d["detection_id"] == row["selected_detection_id"]
    )
    subject = Box(**selected["box"])
    result["source"]["subject_height_fraction_output"] = subject.height / box.height
    result["source"]["estimated_head_fraction_output"] = (subject.y1 - box.y1) / box.height
    result["warnings"] = ["manual_crop"]
    return result
