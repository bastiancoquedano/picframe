from raceframe.core.models import Box, Detection
from raceframe.ui.window import MainWindow


def test_ui_selection_and_manual_review(qtbot, photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg", size=(800, 1200))
    fake_detector.detections = [
        Detection(0, Box(100, 300, 250, 900), 0.9),
        Detection(1, Box(500, 300, 650, 900), 0.9),
    ]
    model = tmp_path / "model.pt"
    model.write_bytes(b"fake")
    window = MainWindow(detector_factory=lambda *a: fake_detector, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.min_edge.setValue(300)
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    window.choose_person(0)
    row = window.records["a.jpg"]
    assert row["manual_selection"] and row["selected_detection_id"] == 0
    window.apply_manual_crop(Box(0, 0, 800, 1200))
    assert window.records["a.jpg"]["manual_crop"]
    assert window.original_view.original_size == (800, 1200)


def test_click_person_and_drag_crop(qtbot, photo_factory, tmp_path, fake_detector):
    from PySide6.QtCore import QPointF, Qt

    path = photo_factory("input/a.jpg", size=(800, 1200))
    fake_detector.detections = [
        Detection(0, Box(100, 300, 250, 900), 0.9),
        Detection(1, Box(500, 300, 650, 900), 0.9),
    ]
    model = tmp_path / "model.pt"
    model.write_bytes(b"fake")
    window = MainWindow(detector_factory=lambda *a: fake_detector, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.min_edge.setValue(300)
    window.show()
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    view = window.original_view
    qtbot.mouseClick(
        view.viewport(), Qt.MouseButton.LeftButton, pos=view.mapFromScene(QPointF(175, 550))
    )
    assert window.records["a.jpg"]["selected_detection_id"] == 0
    qtbot.mouseClick(window.manual_button, Qt.MouseButton.LeftButton)
    qtbot.mousePress(
        view.viewport(), Qt.MouseButton.LeftButton, pos=view.mapFromScene(QPointF(20, 20))
    )
    qtbot.mouseMove(view.viewport(), pos=view.mapFromScene(QPointF(780, 1160)))
    qtbot.mouseRelease(
        view.viewport(), Qt.MouseButton.LeftButton, pos=view.mapFromScene(QPointF(780, 1160))
    )
    assert window.records["a.jpg"]["manual_crop"] is True
