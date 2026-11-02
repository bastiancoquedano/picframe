from copy import deepcopy

import pytest

from raceframe.core.models import Box, Detection
from raceframe.ui.decisions import needs_review
from raceframe.ui.window import MainWindow


@pytest.mark.parametrize(
    "selection,composition,error,expected",
    [
        ("selected", "cropped", None, False),
        ("selected", "unchanged", None, False),
        ("ambiguous", "review_required", None, True),
        ("no_subject", "review_required", None, True),
        ("low_confidence", "review_required", None, True),
        ("selected", "review_required", None, True),
        ("selected", "cropped", {"code": "metadata_error"}, True),
        ("not_analyzed", None, {"code": "analysis_error"}, True),
    ],
)
def test_review_criteria(selection, composition, error, expected):
    row = {
        "selection_status": selection,
        "composition": {"status": composition} if composition else None,
        "error": error,
    }
    assert needs_review(row) is expected


def visible_ids(window):
    from PySide6.QtCore import Qt

    return [
        window.photo_list.item(i).data(Qt.ItemDataRole.UserRole)
        for i in range(window.photo_list.count())
        if not window.photo_list.item(i).isHidden()
    ]


@pytest.fixture
def analyzed_window(qtbot, photo_factory, tmp_path, fake_detector):
    source = photo_factory("input/a.jpg", size=(800, 1200)).parent
    photo_factory("input/b.jpg", size=(800, 1200))
    detector = fake_detector
    detector.detections = [
        Detection(0, Box(100, 300, 250, 900), 0.9),
        Detection(1, Box(500, 300, 650, 900), 0.9),
    ]
    model = tmp_path / "fake.pt"
    model.write_bytes(b"fake")
    window = MainWindow(detector_factory=lambda *a: detector, initial_model=model)
    qtbot.addWidget(window)
    window.set_source(source)
    window.output_edit.setText(str(tmp_path / "out"))
    window.min_edge.setValue(300)
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    return window, detector


def test_filter_tracks_corrections_reset_and_empty_preview(analyzed_window):
    window, detector = analyzed_window
    window.review_filter.setCurrentIndex(1)
    assert visible_ids(window) == ["a.jpg", "b.jpg"]
    assert "2 de 2" in window.filter_count.text()
    window.choose_person(0)
    assert visible_ids(window) == ["b.jpg"]
    assert window.selected_id() == "b.jpg"
    assert window.records["a.jpg"]["manual_selection"]
    window.choose_person(0)
    assert visible_ids(window) == []
    assert window.selected_id() is None
    assert window.preview_image is None
    assert window.person_combo.count() == 0
    assert not window.manual_button.isEnabled()
    assert "No hay fotografías" in window.filter_count.text()
    assert window.export_button.isEnabled()
    window.review_filter.setCurrentIndex(0)
    assert visible_ids(window) == ["a.jpg", "b.jpg"]
    window.photo_list.setCurrentRow(0)
    window.reset_decision()
    window.review_filter.setCurrentIndex(1)
    assert visible_ids(window) == ["a.jpg"]
    assert detector.calls == 2
    assert window.analysis_complete


def test_filter_does_not_limit_export_and_shows_export_errors(analyzed_window, qtbot):
    window, detector = analyzed_window
    window.choose_person(0)
    window.review_filter.setCurrentIndex(1)
    assert visible_ids(window) == ["b.jpg"]
    window.start_export()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert window.last_result["summary"]["exported"] == 2
    assert detector.calls == 2
    assert visible_ids(window) == ["b.jpg"]
    failed = deepcopy(window.last_result)
    failed["images"][0]["error"] = {"code": "metadata_error"}
    failed["images"][0]["operation_status"] = "error"
    window.export_done(failed)
    assert visible_ids(window) == ["a.jpg", "b.jpg"]
    window.photo_list.setCurrentRow(0)
    window.choose_person(0)
    assert visible_ids(window) == ["b.jpg"]


def test_filter_updates_during_analysis_and_resets_on_invalidation(analyzed_window, qtbot):
    window, detector = analyzed_window
    window.review_filter.setCurrentIndex(1)
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert visible_ids(window) == ["a.jpg", "b.jpg"]
    detector.detections = detector.detections[:1]
    window.start_analysis()
    qtbot.waitUntil(lambda: window.worker is None, timeout=5000)
    assert visible_ids(window) == []
    assert window.selected_id() is None
    assert "No hay fotografías" in window.filter_count.text()
    window.quality.setValue(90)
    assert visible_ids(window) == []
    assert window.preview_image is None
    assert not window.export_button.isEnabled()
