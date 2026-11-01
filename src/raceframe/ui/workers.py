"""Tareas cooperativas con señales; no crean widgets ni QPixmap."""

from threading import Event

from PySide6.QtCore import QThread, Signal

from raceframe.core.processing import analyze_image, blank_result
from raceframe.imaging.discovery import discover


class TaskWorker(QThread):
    progress = Signal(int, int)
    record = Signal(object)
    result = Signal(object)
    failed = Signal(str)

    def __init__(self, function, parent=None):
        super().__init__(parent)
        self.function = function
        self.cancel = Event()

    def run(self):
        try:
            value = self.function(self.progress.emit, self.record.emit, self.cancel)
            self.result.emit(value)
        except Exception as exc:
            self.failed.emit(str(exc))


def analyze_folder(source, output, config, detector, progress, record, cancel):
    inventory = discover(source, output, recursive=config.recursive)
    rows = []
    for index, item in enumerate(inventory.images):
        if cancel.is_set():
            break
        try:
            row = analyze_image(inventory.root, item, detector, config)
        except Exception as exc:
            row = blank_result(item)
            row.update(
                operation_status="error",
                error={"code": "analysis_error", "stage": "analysis", "message": str(exc)},
            )
        rows.append(row)
        record(row)
        progress(index + 1, len(inventory.images))
    return {
        "inventory": inventory,
        "records": rows,
        "cancelled": cancel.is_set(),
        "detector": detector,
    }
