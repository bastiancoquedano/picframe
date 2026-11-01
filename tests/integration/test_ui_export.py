from raceframe.ui.window import MainWindow


def test_ui_exports_cached_decisions(qtbot, photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    model = tmp_path / "fake.pt"
    model.write_bytes(b"fake")
    window = MainWindow(detector_factory=lambda *a: fake_detector, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    window.start_export()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert window.last_result["summary"]["exported"] == 1
    assert fake_detector.calls == 1
    assert window.results_button.isEnabled()


def test_close_cancels_cooperatively_without_destroying_worker(qtbot):
    from PySide6.QtCore import QTimer

    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    window.launch(lambda progress, record, cancel: cancel.wait(5), lambda value: None)
    QTimer.singleShot(20, window.close)
    qtbot.waitUntil(lambda: window.worker is None, timeout=2000)
    assert not window.isVisible()


def test_manual_crop_is_the_exported_decision(qtbot, photo_factory, tmp_path, fake_detector):
    from pathlib import Path

    from PIL import Image

    from raceframe.core.models import Box, Detection

    path = photo_factory("input/a.jpg", size=(800, 1200))
    fake_detector.detections = [Detection(0, Box(100, 300, 250, 900), 0.95)]
    model = tmp_path / "fake.pt"
    model.write_bytes(b"fake")
    window = MainWindow(detector_factory=lambda *a: fake_detector, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.min_edge.setValue(300)
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    window.choose_person(0)
    window.apply_manual_crop(Box(0, 0, 760, 1140))
    window.start_export()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    result = window.last_result
    row = result["images"][0]
    assert row["manual_selection"] and row["manual_crop"]
    assert row["crop_xyxy"] == [0, 0, 760, 1140]
    assert fake_detector.calls == 1
    with Image.open(Path(result["manifest_path"]).parent / row["output_relative_path"]) as output:
        assert output.size == (760, 1140)
        assert output.getexif()[271] == "Synthetic Camera"
