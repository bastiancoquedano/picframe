import pytest

from raceframe.config import Config
from raceframe.ui.workers import TaskWorker, analyze_folder


def test_worker_analysis_and_cancel(photo_factory, tmp_path, fake_detector, qtbot):
    path = photo_factory("input/a.jpg")
    photo_factory("input/b.jpg")
    records = []
    worker = TaskWorker(
        lambda progress, record, cancel: analyze_folder(
            path.parent, tmp_path / "out", Config(), fake_detector, progress, record, cancel
        )
    )
    worker.record.connect(records.append)
    with qtbot.waitSignal(worker.finished, timeout=5000):
        worker.start()
    assert len(records) == 2
    assert fake_detector.calls == 2
    worker.wait()


@pytest.mark.real_model
def test_real_detector_runs_in_ui_thread_worker(qtbot, photo_factory, tmp_path, monkeypatch):
    import os
    from pathlib import Path

    from PySide6.QtCore import QTimer

    from raceframe.ui.window import MainWindow

    model = os.environ.get("RACEFRAME_TEST_MODEL")
    if not model:
        pytest.skip("Prueba de worker real pendiente: falta RACEFRAME_TEST_MODEL")
    monkeypatch.setenv("RACEFRAME_RUNTIME_DIR", str(tmp_path / "runtime"))
    path = photo_factory("input/a.jpg")
    window = MainWindow(initial_model=Path(model))
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    ticks = []
    timer = QTimer(window)
    timer.setInterval(10)
    timer.timeout.connect(lambda: ticks.append(True))
    timer.start()
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=60000)
    timer.stop()
    assert ticks
    assert window.analysis_complete
    assert window.detector.runtime["device_effective"] == "cpu"
    window.start_export()
    qtbot.waitUntil(lambda: window.worker is None, timeout=10000)
    assert window.last_result["summary"]["exported"] == 1
