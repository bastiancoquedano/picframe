"""Lote local independiente de encuadre para aplicar marcas de agua."""

import errno
from dataclasses import asdict
from datetime import UTC, datetime
from functools import partial
from hashlib import file_digest
from pathlib import Path
from time import monotonic
from uuid import uuid4

from raceframe import __version__
from raceframe.core.processing import blank_result
from raceframe.core.watermark_models import WatermarkConfig
from raceframe.export.directory import create_job_directory
from raceframe.export.jpeg import (
    export_original_copy,
    export_rendered_jpeg,
    validate_volume,
)
from raceframe.export.manifest import AuditError, Journal, atomic_json, summarize
from raceframe.imaging.discovery import discover
from raceframe.imaging.loader import load_image


def _config_dict(config):
    value = asdict(config)
    for layer in value["layers"]:
        if layer["asset_sha256"] is None:
            with Path(layer["asset_path"]).open("rb") as handle:
                layer["asset_sha256"] = file_digest(handle, "sha256").hexdigest()
        layer["asset_path"] = str(layer["asset_path"])
    if value["signature"]["asset_path"] is not None:
        if value["signature"]["enabled"] and value["signature"]["kind"] == "png":
            if value["signature"]["asset_sha256"] is None:
                with Path(value["signature"]["asset_path"]).open("rb") as handle:
                    value["signature"]["asset_sha256"] = file_digest(handle, "sha256").hexdigest()
        value["signature"]["asset_path"] = str(value["signature"]["asset_path"])
    return value


def _blank_watermark_result(item, mode):
    row = blank_result(item)
    row["watermark"] = {
        "mode": mode,
        "segmentation_status": "not_attempted",
        "segmentation_reason": None,
        "fallback_policy": None,
        "fallback_applied": None,
        "review_required": False,
        "backend": None,
        "backend_version": None,
        "compute_device": None,
        "quality": None,
        "vision_revision": None,
    }
    return row


def _journal_prepared(journal, row, intent):
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


def process_watermark_folder(
    source,
    output=None,
    *,
    config,
    progress=None,
    cancel=None,
    job_name=None,
    segmenter_factory=None,
):
    """Aplica un preset a un inventario con una sola imagen/máscara en RAM."""
    if not isinstance(config, WatermarkConfig):
        raise ValueError("La configuración de marca de agua no es válida")
    config.validate_for_run()
    config_value = _config_dict(config)
    inventory = discover(
        Path(source),
        None if output is None else Path(output),
        recursive=config.recursive,
    )
    job_id = str(uuid4())
    destination = create_job_directory(inventory.destination, job_name, job_id)
    validate_volume(destination)
    started = monotonic()
    header = {
        "schema_version": 1,
        "job_type": "watermark",
        "job_id": job_id,
        "created_at": datetime.now(UTC).isoformat(),
        "finished_at": None,
        "status": "running",
        "input_root": str(inventory.root),
        "output_root": str(inventory.destination),
        "config": config_value,
        "runtime": {
            "app_version": __version__,
            "workflow": "watermark",
            "segmentation_backend": "apple_vision" if config.mode == "smart" else None,
        },
        "warnings": list(inventory.warnings),
    }
    rows = [_blank_watermark_result(item, config.mode) for item in inventory.images]
    status = "completed"
    segmenter = None
    segmenter_initialization_error = None
    from raceframe.core.watermark_render import WatermarkRenderer

    with WatermarkRenderer(config) as renderer, Journal(destination, header, rows) as journal:
        for index, (item, row) in enumerate(zip(inventory.images, rows, strict=True)):
            if cancel is not None and cancel.is_set():
                journal.record("cancel_requested")
                status = "cancelled"
                break
            journal.record("image_started", image_id=item.image_id)
            fatal = False
            prepared = partial(_journal_prepared, journal, row)
            try:
                with load_image(inventory.root, item) as loaded:
                    row["source"] = {
                        "stored_dimensions": list(loaded.stored_size),
                        "oriented_dimensions": list(loaded.image.size),
                        "exif_orientation": loaded.source_orientation,
                    }
                    row["warnings"].extend(loaded.warnings)
                    mask = None
                    use_fallback = False
                    if config.mode == "smart":
                        try:
                            if segmenter is None:
                                if segmenter_initialization_error is not None:
                                    raise RuntimeError(
                                        "No se pudo inicializar Apple Vision"
                                    ) from segmenter_initialization_error
                                if segmenter_factory is None:
                                    from raceframe.watermark.vision import VisionPersonSegmenter

                                    segmenter_factory = VisionPersonSegmenter
                                segmenter = segmenter_factory()
                            result = segmenter.segment(loaded.image)
                            row["watermark"].update(
                                segmentation_status=result.status,
                                segmentation_reason=result.reason,
                                backend=result.backend,
                                backend_version=result.backend_version,
                                compute_device=getattr(result, "compute_device", None),
                                quality=result.quality,
                                vision_revision=result.revision,
                            )
                            if result.status in {"ok", "empty"}:
                                from raceframe.watermark.vision import classify_person_mask

                                classified, reason = classify_person_mask(result.mask)
                                if result.mask.shape != (loaded.image.height, loaded.image.width):
                                    row["watermark"].update(
                                        segmentation_status="error",
                                        segmentation_reason="mask_dimensions_mismatch",
                                    )
                                    use_fallback = True
                                elif classified != result.status:
                                    row["watermark"].update(
                                        segmentation_status="error",
                                        segmentation_reason=reason or "mask_status_mismatch",
                                    )
                                    use_fallback = True
                                else:
                                    mask = result.mask
                            else:
                                use_fallback = True
                        except Exception as exc:
                            if segmenter is None:
                                segmenter_initialization_error = exc
                            use_fallback = True
                            row["watermark"].update(
                                segmentation_status="error",
                                segmentation_reason=f"{type(exc).__name__}: {exc}",
                            )

                    if use_fallback:
                        row["warnings"].append("segmentation_fallback")
                        row["watermark"].update(
                            fallback_policy=config.fallback_policy,
                            fallback_applied=config.fallback_policy,
                            review_required=True,
                        )
                        if config.fallback_policy == "skip_image":
                            row.update(
                                operation_status="omitted",
                                error={
                                    "code": "segmentation_failed",
                                    "stage": "segmentation",
                                    "message": row["watermark"]["segmentation_reason"]
                                    or "No se obtuvo una máscara confiable",
                                },
                            )
                            exported = None
                        elif config.fallback_policy == "copy_original":
                            exported = export_original_copy(
                                inventory.root,
                                item,
                                destination,
                                loaded.image.size,
                                before_publish=prepared,
                            )
                        else:
                            with renderer.render(loaded.image, None) as rendered:
                                exported = export_rendered_jpeg(
                                    inventory.root,
                                    item,
                                    loaded,
                                    rendered,
                                    destination,
                                    quality=config.quality,
                                    before_publish=prepared,
                                )
                    else:
                        if (
                            config.mode == "smart"
                            and row["watermark"]["segmentation_status"] == "empty"
                        ):
                            row["warnings"].append("no_people_detected")
                        with renderer.render(loaded.image, mask) as rendered:
                            exported = export_rendered_jpeg(
                                inventory.root,
                                item,
                                loaded,
                                rendered,
                                destination,
                                quality=config.quality,
                                before_publish=prepared,
                            )
                    if exported is not None:
                        row.update(
                            operation_status="exported",
                            output_relative_path=exported.path.name,
                            output_sha256=exported.sha256,
                            final_dimensions=list(exported.dimensions),
                        )
                        row["warnings"].extend(exported.warnings)
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
            elif any(row.get("error") for row in rows):
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
