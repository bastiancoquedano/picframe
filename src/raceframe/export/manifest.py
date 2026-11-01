"""Diario durable, bloqueo por trabajo y reconstrucción sin modificar fotografías."""

import fcntl
import json
import os
import tempfile
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from raceframe.export.jpeg import file_hash, sync_directory


class AuditError(RuntimeError):
    pass


class JobActiveError(RuntimeError):
    pass


def atomic_json(path, value):
    fd, name = tempfile.mkstemp(prefix=".json-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as output:
            json.dump(value, output, ensure_ascii=False, allow_nan=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
        sync_directory(path.parent)
    finally:
        Path(name).unlink(missing_ok=True)


def summarize(rows, elapsed):
    result = {
        "total": len(rows),
        "exported": 0,
        "omitted": 0,
        "errors": 0,
        "not_attempted": 0,
        "cropped": 0,
        "unchanged": 0,
        "review_required": 0,
        "elapsed_seconds": elapsed,
    }
    for row in rows:
        key = "errors" if row["operation_status"] == "error" else row["operation_status"]
        result[key] += 1
        if row["composition"] is not None:
            result[row["composition"]["status"]] += 1
    return result


class Journal:
    def __init__(self, directory, header, rows):
        self.directory = Path(directory)
        self.job_id = header["job_id"]
        self.seq = 0
        self.lock = (self.directory / ".lock").open("xb")
        self.events = None
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atomic_json(self.directory / "job.json", header)
            atomic_json(
                self.directory / "inventory.json",
                {"schema_version": 1, "job_id": self.job_id, "images": rows},
            )
            self.events = (self.directory / "events.jsonl").open("xb", buffering=0)
            sync_directory(self.directory)
        except Exception:
            self.close()
            raise

    def record(self, kind, **payload):
        event = {
            "schema_version": 1,
            "job_id": self.job_id,
            "seq": self.seq + 1,
            "timestamp": datetime.now(UTC).isoformat(),
            "type": kind,
            **payload,
        }
        try:
            data = (json.dumps(event, ensure_ascii=False, allow_nan=False) + "\n").encode()
            if self.events.write(data) != len(data):
                raise OSError("Escritura parcial del diario")
            os.fsync(self.events.fileno())
            self.seq += 1
        except (OSError, ValueError, TypeError) as exc:
            raise AuditError("No se pudo confirmar el diario del trabajo") from exc

    def close(self):
        if self.events is not None:
            self.events.close()
        self.lock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _safe_output(directory, relative):
    if not isinstance(relative, str) or Path(relative).name != relative or relative in (".", ".."):
        raise ValueError("Ruta de salida no válida en diario")
    path = directory / relative
    if path.is_symlink() or not path.resolve().is_relative_to(directory):
        raise ValueError("La salida del diario sale del directorio de trabajo")
    return path


def read_report(directory, *, recover=False):
    directory = Path(directory).resolve(strict=True)
    with (directory / ".lock").open("rb") as lock:
        try:
            fcntl.flock(lock, (fcntl.LOCK_EX if recover else fcntl.LOCK_SH) | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise JobActiveError(
                "El trabajo sigue activo; no se puede recuperar ni declarar interrumpido"
            ) from exc
        header = json.loads((directory / "job.json").read_text())
        inventory = json.loads((directory / "inventory.json").read_text())
        if header["schema_version"] != 1 or inventory["job_id"] != header["job_id"]:
            raise ValueError("Versión o identidad de trabajo no válida")
        rows = {row["image_id"]: deepcopy(row) for row in inventory["images"]}
        pending = {}
        terminal = set()
        warnings = list(header.get("warnings", []))
        finished = None
        elapsed = 0.0
        lines = (directory / "events.jsonl").read_bytes().splitlines(keepends=True)
        for index, line in enumerate(lines):
            if not line.endswith(b"\n") and index == len(lines) - 1:
                warnings.append("truncated_journal_tail")
                break
            event = json.loads(line)
            if event["seq"] != index + 1 or event.get("job_id") != header["job_id"]:
                raise ValueError("Secuencia o identidad de diario no válida")
            kind = event["type"]
            image_id = event.get("image_id")
            if image_id is not None and image_id not in rows:
                raise ValueError("Imagen desconocida en el diario")
            elapsed = event.get("elapsed_seconds", elapsed)
            if kind == "export_prepared":
                pending[image_id] = event
            elif kind == "export_aborted":
                pending.pop(image_id, None)
            elif kind in ("image_completed", "image_failed"):
                if image_id in terminal:
                    raise ValueError("Resultado terminal duplicado")
                if event["result"]["image_id"] != image_id:
                    raise ValueError("Identidad de resultado no válida")
                rows[image_id] = event["result"]
                terminal.add(image_id)
                pending.pop(image_id, None)
            elif kind == "job_finished":
                finished = event
            elif kind not in ("image_started", "cancel_requested"):
                raise ValueError("Evento de diario desconocido")
        if recover and finished is None:
            for image_id, event in pending.items():
                row = deepcopy(event["result"])
                target = _safe_output(directory, event["intent"]["output_relative_path"])
                if target.is_file() and file_hash(target) == event["intent"]["sha256"]:
                    row["warnings"].append("recovered_publication")
                else:
                    row.update(
                        operation_status="error",
                        output_relative_path=None,
                        output_sha256=None,
                        error={
                            "code": "interrupted_export",
                            "stage": "export",
                            "message": "No se confirmó una salida íntegra con el hash esperado",
                        },
                    )
                rows[image_id] = row
        result = {
            **header,
            "status": finished["status"] if finished else "interrupted",
            "finished_at": finished["timestamp"] if finished else None,
            "images": list(rows.values()),
            "warnings": warnings,
        }
        result["summary"] = summarize(result["images"], elapsed)
        output = directory / "manifest.json"
        if recover and (finished is None or not output.exists()):
            output = directory / f"manifest-recovered-{uuid4()}.json"
            result["manifest_path"] = str(output)
            atomic_json(output, result)
        else:
            result["manifest_path"] = str(output) if output.exists() else None
        return result
