"""CLI local: JSON en stdout, progreso y diagnósticos en stderr."""

import argparse
import json
import signal
import sys
from pathlib import Path
from threading import Event

from raceframe import __version__
from raceframe.config import Config


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def _error(code, message, exit_code):
    print(json.dumps({"error": {"code": code, "message": str(message)}}, ensure_ascii=False))
    print(str(message), file=sys.stderr)
    return exit_code


def main(argv=None, *, detector_factory=None):
    parser = Parser(prog="picframe", description="Reencuadre fotográfico local")
    parser.add_argument("--version", action="version", version=f"Picframe {__version__}")
    sub = parser.add_subparsers(dest="command")
    process = sub.add_parser("process", help="Analizar y exportar una carpeta JPEG")
    process.add_argument("input", type=Path)
    process.add_argument("--output", type=Path)
    process.add_argument("--model", required=True, type=Path)
    process.add_argument("--config", type=Path)
    process.add_argument("--recursive", action="store_true", default=None)
    process.add_argument("--mode", choices=("conservative", "balanced", "tight"))
    process.add_argument("--aspect", choices=("original", "3:2", "4:5"))
    process.add_argument("--margin", type=float)
    process.add_argument("--quality", type=int)
    process.add_argument("--device", choices=("cpu", "mps", "auto"))
    process.add_argument("--framing-policy", choices=("focal", "context"))
    process.add_argument("--focal-threshold", type=float)
    process.add_argument("--target-occupancy", type=float)
    process.add_argument("--min-long-edge", type=int)
    process.add_argument("--composition-priority", choices=("headroom", "occupancy"))
    process.add_argument("--head-fraction", type=float)
    process.add_argument("--subject-category", choices=("people", "animals", "vehicles"))
    process.add_argument("--selection-strategy", choices=("manual", "dominant", "group"))
    process.add_argument("--dominance-ratio", type=float)
    report = sub.add_parser("report", help="Consultar o recuperar un trabajo local")
    report.add_argument("directory", type=Path)
    report.add_argument("--recover", action="store_true")
    try:
        args = parser.parse_args(argv)
    except ValueError as exc:
        return _error("invalid_arguments", exc, 2)
    if args.command is None:
        parser.print_help()
        return 0
    if args.command == "report":
        if not args.directory.is_dir():
            return _error("invalid_directory", "No existe el trabajo", 2)
        try:
            from raceframe.export.manifest import read_report

            result = read_report(args.directory, recover=args.recover)
        except Exception as exc:
            return _error("report_failed", exc, 3)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0 if result["status"] == "completed" else 1
    try:
        overrides = {
            name: getattr(args, name)
            for name in (
                "recursive",
                "mode",
                "aspect",
                "margin",
                "quality",
                "device",
                "framing_policy",
                "focal_threshold",
                "target_occupancy",
                "min_long_edge",
                "composition_priority",
                "head_fraction",
                "subject_category",
                "selection_strategy",
                "dominance_ratio",
            )
            if getattr(args, name) is not None
        }
        config = (
            Config.from_file(args.config, overrides)
            if args.config
            else Config.from_sources(overrides=overrides)
        )
        if not args.model.is_file():
            raise ValueError(
                "El modelo debe ser un archivo local existente; no se descarga durante process"
            )
        from raceframe.imaging.discovery import discover

        discover(args.input, args.output, recursive=config.recursive)
        if detector_factory is None:
            from raceframe.core.detection import YoloDetector

            detector_factory = YoloDetector
        from raceframe.export.metadata import tool_path

        tool_path()
        detector = detector_factory(args.model, config)
    except KeyboardInterrupt:
        return _error("cancelled", "Preparación cancelada", 130)
    except Exception as exc:
        return _error("preparation_error", exc, 2)
    from raceframe.core.processing import process_folder

    cancel = Event()
    previous = signal.signal(signal.SIGINT, lambda *unused: cancel.set())
    try:
        result = process_folder(
            args.input,
            args.output,
            detector=detector,
            config=config,
            cancel=cancel,
            progress=lambda n, total: print(f"Procesadas {n}/{total}", file=sys.stderr),
        )
    except Exception as exc:
        return _error("job_failed", exc, 3)
    finally:
        signal.signal(signal.SIGINT, previous)
    print(
        json.dumps(
            {k: result[k] for k in ("job_id", "status", "summary", "manifest_path")},
            ensure_ascii=False,
            allow_nan=False,
        )
    )
    return {"completed": 0, "completed_with_errors": 1, "cancelled": 130, "failed": 3}[
        result["status"]
    ]
