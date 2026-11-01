"""Orquestación secuencial; el detector se inyecta y las imágenes se liberan por archivo."""

import errno
from dataclasses import asdict
from datetime import UTC, datetime
from math import isfinite
from pathlib import Path
from time import monotonic
from uuid import uuid4

from raceframe import __version__
from raceframe.config import Config
from raceframe.core.cropping import calculate_focal_crop
from raceframe.core.models import SelectionStatus
from raceframe.core.selection import select_subject
from raceframe.export.jpeg import export_image, validate_volume
from raceframe.export.manifest import AuditError, Journal, atomic_json, summarize
from raceframe.imaging.discovery import discover
from raceframe.imaging.loader import load_image


def sanitize(value):
    if isinstance(value, float) and not isfinite(value):
        return None
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(v) for v in value]
    return value


def blank_result(item):
    return {
        "image_id": item.image_id,
        "input_relative_path": item.relative_path,
        "source": {
            "stored_dimensions": None,
            "oriented_dimensions": None,
            "exif_orientation": None,
        },
        "detections": [],
        "selection_status": "not_analyzed",
        "selected_detection_id": None,
        "composition": None,
        "crop_xyxy": None,
        "final_dimensions": None,
        "operation_status": "not_attempted",
        "output_relative_path": None,
        "output_sha256": None,
        "warnings": [],
        "error": None,
    }


def analyze_item(root, item, row, detector, config, destination, on_prepared=None):
    with load_image(root, item) as loaded:
        width, height = loaded.image.size
        row["source"] = {
            "stored_dimensions": list(loaded.stored_size),
            "oriented_dimensions": [width, height],
            "exif_orientation": loaded.source_orientation,
        }
        selection = select_subject(detector.detect(loaded.image), width, height, config)
        row["selection_status"] = selection.status
        row["selected_detection_id"] = selection.selected_id
        row["detections"] = [sanitize(asdict(d)) for d in selection.detections]
        subject = next(
            (d.box for d in selection.detections if d.detection_id == selection.selected_id), None
        )
        if selection.status != SelectionStatus.SELECTED:
            subject = None
        focal = loaded.exif.get_ifd(34665).get(37386)
        try:
            focal = float(focal) if focal is not None else None
            if focal is not None and (not isfinite(focal) or focal <= 0):
                focal = None
        except (ValueError, TypeError, ZeroDivisionError):
            focal = None
        row["source"]["focal_length_mm"] = focal
        comp = calculate_focal_crop(width, height, subject, config, focal)
        row["source"]["subject_height_fraction_original"] = (
            None if subject is None else subject.height / height
        )
        row["source"]["subject_height_fraction_output"] = (
            None if subject is None else subject.height / comp.crop.height
        )
        row["source"]["head_reference"] = "detection_top" if subject is not None else None
        row["source"]["estimated_head_fraction_output"] = (
            None if subject is None else (subject.y1 - comp.crop.y1) / comp.crop.height
        )
        row["composition"] = asdict(comp)
        row["composition"]["crop"] = list(comp.crop.as_tuple())
        row["crop_xyxy"] = list(comp.crop.as_tuple())
        row["warnings"] = list(dict.fromkeys((*loaded.warnings, *selection.reasons, *comp.reasons)))
        callback = None if on_prepared is None else lambda intent: on_prepared(row, intent)
        exported = export_image(
            root, item, loaded, comp, destination, quality=config.quality, before_publish=callback
        )
        row.update(
            operation_status="exported",
            output_relative_path=exported.path.name,
            output_sha256=exported.sha256,
            final_dimensions=list(exported.dimensions),
        )
        row["warnings"].extend(exported.warnings)


def process_folder(source, output=None, *, detector, config=None, progress=None, cancel=None):
    config = config or Config()
    inventory = discover(
        Path(source), None if output is None else Path(output), recursive=config.recursive
    )
    inventory.destination.mkdir(parents=True, exist_ok=True)
    destination = inventory.destination / f"job-{uuid4()}"
    destination.mkdir()
    validate_volume(destination)
    started = monotonic()
    header = {
        "schema_version": 1,
        "job_id": destination.name[4:],
        "created_at": datetime.now(UTC).isoformat(),
        "finished_at": None,
        "status": "running",
        "input_root": str(inventory.root),
        "output_root": str(inventory.destination),
        "config": config.to_dict(),
        "runtime": {"app_version": __version__, **getattr(detector, "runtime", {})},
        "warnings": list(inventory.warnings),
    }
    rows = [blank_result(item) for item in inventory.images]
    status = "completed"
    with Journal(destination, header, rows) as journal:

        def prepared(row, intent):
            from copy import deepcopy

            recovered = deepcopy(row)
            recovered.update(
                operation_status="exported",
                output_relative_path=intent["output_relative_path"],
                output_sha256=intent["sha256"],
                final_dimensions=list(intent["dimensions"]),
            )
            recovered["warnings"].extend(intent.get("warnings", []))
            kind = "export_aborted" if intent.get("aborted") else "export_prepared"
            journal.record(kind, image_id=row["image_id"], result=recovered, intent=intent)

        for index, (item, row) in enumerate(zip(inventory.images, rows, strict=True)):
            if cancel is not None and cancel.is_set():
                journal.record("cancel_requested")
                status = "cancelled"
                break
            journal.record("image_started", image_id=item.image_id)
            fatal = False
            try:
                analyze_item(inventory.root, item, row, detector, config, destination, prepared)
            except AuditError:
                raise
            except Exception as exc:
                row.update(
                    operation_status="error",
                    error={"code": "image_error", "stage": "processing", "message": str(exc)},
                )
                fatal = isinstance(exc, OSError) and exc.errno in (
                    errno.ENOSPC,
                    errno.EROFS,
                    errno.ENODEV,
                    errno.EIO,
                )
            journal.record(
                "image_completed" if row["operation_status"] == "exported" else "image_failed",
                image_id=item.image_id,
                result=row,
                elapsed_seconds=monotonic() - started,
            )
            if progress:
                progress(index + 1, len(rows))
            if fatal:
                status = "failed"
                break
        if status == "completed":
            if cancel is not None and cancel.is_set():
                status = "cancelled"
            elif any(row["operation_status"] == "error" for row in rows):
                status = "completed_with_errors"
        elapsed = monotonic() - started
        journal.record("job_finished", status=status, elapsed_seconds=elapsed)
        result = {
            **header,
            "status": status,
            "finished_at": datetime.now(UTC).isoformat(),
            "summary": summarize(rows, elapsed),
            "images": rows,
            "manifest_path": str(destination / "manifest.json"),
        }
        atomic_json(destination / "manifest.json", result)
    return result
