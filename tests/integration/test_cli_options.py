import json
from pathlib import Path

from raceframe.cli.main import main
from raceframe.core.models import Box, Detection


def test_all_options_and_report(photo_factory, tmp_path, fake_detector, capsys):
    path = photo_factory("input/a.jpg", size=(600, 400))
    fake_detector.detections = [Detection(0, Box(200, 50, 300, 350), 0.99)]
    model = tmp_path / "model.pt"
    model.write_bytes(b"test")
    config = tmp_path / "config.json"
    config.write_text('{"quality":80,"margin":0.1}')
    args = [
        "process",
        str(path.parent),
        "--output",
        str(tmp_path / "out"),
        "--model",
        str(model),
        "--subject-category",
        "people",
        "--selection-strategy",
        "dominant",
        "--dominance-ratio",
        "1.8",
        "--composition-priority",
        "occupancy",
        "--mode",
        "tight",
        "--aspect",
        "4:5",
        "--quality",
        "90",
        "--config",
        str(config),
    ]
    assert main(args, detector_factory=lambda *a: fake_detector) == 0
    result = json.loads(capsys.readouterr().out)
    manifest = json.loads(Path(result["manifest_path"]).read_text())
    assert manifest["config"]["selection_strategy"] == "dominant"
    assert manifest["config"]["dominance_ratio"] == 1.8
    assert manifest["config"]["composition_priority"] == "occupancy"
    assert manifest["config"]["quality"] == 90
    assert manifest["config"]["margin"] == 0.1
    assert main(["report", str(Path(result["manifest_path"]).parent)]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "completed"


def test_cli_bad_margin_is_preparation_error(photo_factory, tmp_path, capsys):
    path = photo_factory("input/a.jpg")
    model = tmp_path / "local.pt"
    model.write_bytes(b"test")
    assert main(["process", str(path.parent), "--model", str(model), "--margin", "nan"]) == 2
    assert "error" in json.loads(capsys.readouterr().out)


def test_cli_automatic_categories_and_exclusive_options(
    photo_factory, tmp_path, fake_detector, capsys
):
    path = photo_factory("input/a.jpg", size=(1200, 800))
    fake_detector.detections = [Detection(0, Box(200, 200, 1000, 600), 0.95, class_name="dog")]
    model = tmp_path / "model.pt"
    model.write_bytes(b"model")
    args = [
        "process",
        str(path.parent),
        "--model",
        str(model),
        "--output",
        str(tmp_path / "out"),
        "--selection-strategy",
        "dominant",
    ]
    assert main([*args, "--auto-subjects"], detector_factory=lambda *a: fake_detector) == 0
    result = json.loads(capsys.readouterr().out)
    manifest = json.loads(Path(result["manifest_path"]).read_text())
    assert manifest["config"]["subject_categories"] == ["people", "animals", "vehicles"]
    assert manifest["images"][0]["selection_status"] == "selected"
    assert (
        main(
            [*args, "--subject-categories", "people", "animals"],
            detector_factory=lambda *a: fake_detector,
        )
        == 0
    )
    result = json.loads(capsys.readouterr().out)
    assert json.loads(Path(result["manifest_path"]).read_text())["config"][
        "subject_categories"
    ] == ["people", "animals"]
    assert main([*args, "--auto-subjects", "--subject-category", "people"]) == 2
