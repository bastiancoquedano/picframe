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
    window.auto_subjects.setChecked(False)
    for category, checkbox in window.category_checks.items():
        checkbox.setChecked(category == "animals")
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
        loads.append(config.active_categories)
        return fake_detector

    window = MainWindow(detector_factory=factory, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.strategy.setCurrentIndex(window.strategy.findData("group"))
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert window.records["a.jpg"]["selected_detection_ids"] == [0, 1]
    window.auto_subjects.setChecked(False)
    for category, checkbox in window.category_checks.items():
        checkbox.setChecked(category == "vehicles")
    assert not window.records
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert loads == [("people", "animals", "vehicles"), ("vehicles",)]
    assert window.records["a.jpg"]["selection_status"] == "no_subject"


def test_automatic_mixed_batch_needs_no_category_changes(qtbot, photo_factory, tmp_path):
    path = photo_factory("input/a_person.jpg", size=(800, 1200))
    photo_factory("input/b_dog.jpg", size=(1200, 800))
    photo_factory("input/c_car.jpg", size=(1000, 1000))
    model = tmp_path / "model.pt"
    model.write_bytes(b"fake")

    class Detector:
        calls = 0

        def detect(self, image):
            self.calls += 1
            name = {800: "person", 1200: "dog", 1000: "car"}[image.width]
            return (
                Detection(
                    0,
                    Box(
                        image.width * 0.2, image.height * 0.2, image.width * 0.8, image.height * 0.8
                    ),
                    0.95,
                    class_name=name,
                ),
            )

    detector = Detector()
    window = MainWindow(detector_factory=lambda *a: detector, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.min_edge.setValue(300)
    assert window.auto_subjects.isChecked()
    assert window.current_config().active_categories == ("people", "animals", "vehicles")
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert all(row["selection_status"] == "selected" for row in window.records.values())
    assert [row["detections"][0]["class_name"] for row in window.records.values()] == [
        "person",
        "dog",
        "car",
    ]
    window.start_export()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert window.last_result["summary"]["exported"] == 3
    assert window.last_result["config"]["subject_categories"] == ("people", "animals", "vehicles")
    assert detector.calls == 3
    window.auto_subjects.setChecked(False)
    window.category_checks["vehicles"].setChecked(False)
    assert window.current_config().active_categories == ("people", "animals")
    assert not window.analysis_complete
    for checkbox in window.category_checks.values():
        checkbox.setChecked(False)
    assert not window.analyze_button.isEnabled()
    assert "al menos" in window.status.text()
    window.auto_subjects.setChecked(True)
    assert window.analyze_button.isEnabled()
    assert window.current_config().active_categories == ("people", "animals", "vehicles")
