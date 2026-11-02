from raceframe.core.models import Box, Detection
from raceframe.ui.window import MainWindow


def test_ui_animal_selection_labels_export_and_policy_invalidation(
    qtbot, photo_factory, tmp_path, fake_detector
):
    path = photo_factory("input/a.jpg", size=(1600, 1000))
    fake_detector.detections = [Detection(0, Box(200, 200, 1100, 800), 0.95, class_name="dog")]
    model = tmp_path / "model.pt"
    model.write_bytes(b"fake")
    window = MainWindow(detector_factory=lambda *a: fake_detector, initial_model=model)
    qtbot.addWidget(window)
    assert "Picframe" in window.windowTitle()
    assert window.strategy.currentData() == "dominant"
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.category.setCurrentIndex(window.category.findData("animals"))
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert window.records["a.jpg"]["selection_status"] == "selected"
    assert "Perro" in window.person_combo.itemText(1)
    window.choose_person(0)
    assert window.records["a.jpg"]["manual_selection"]
    window.start_export()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert window.last_result["summary"]["exported"] == 1
    assert fake_detector.calls == 1
    window.strategy.setCurrentIndex(window.strategy.findData("group"))
    assert not window.analysis_complete and not window.export_button.isEnabled()


def test_ui_group_preserves_members_and_category_reloads_detector(
    qtbot, photo_factory, tmp_path, fake_detector
):
    path = photo_factory("input/a.jpg", size=(800, 1200))
    fake_detector.detections = [
        Detection(0, Box(100, 300, 250, 900), 0.95),
        Detection(1, Box(500, 300, 650, 900), 0.95),
    ]
    model = tmp_path / "model.pt"
    model.write_bytes(b"fake")
    loads = []

    def factory(weights, config):
        loads.append(config.subject_category)
        return fake_detector

    window = MainWindow(detector_factory=factory, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.strategy.setCurrentIndex(window.strategy.findData("group"))
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert window.records["a.jpg"]["selected_detection_ids"] == [0, 1]
    window.category.setCurrentIndex(window.category.findData("vehicles"))
    assert not window.records
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert loads == ["people", "vehicles"]
    assert window.records["a.jpg"]["selection_status"] == "no_subject"
