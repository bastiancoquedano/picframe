from raceframe.ui.window import MainWindow


def test_window_analysis_and_parameter_invalidation(qtbot, photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    model = tmp_path / "fake.pt"
    model.write_bytes(b"fake")
    window = MainWindow(detector_factory=lambda *a: fake_detector, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(path.parent)
    window.output_edit.setText(str(tmp_path / "out"))
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert len(window.records) == 1
    assert window.export_button.isEnabled()
    assert fake_detector.calls == 1
    window.quality.setValue(90)
    assert not window.export_button.isEnabled()
    assert not window.analysis_complete


def test_source_focus_keeps_chosen_destination(qtbot, tmp_path):
    window = MainWindow()
    qtbot.addWidget(window)
    window.set_source(tmp_path)
    window.output_edit.setText(str(tmp_path.parent / "chosen-output"))
    window.source_edited()
    assert window.output_edit.text() == str(tmp_path.parent / "chosen-output")
