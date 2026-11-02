from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image

from raceframe.config import Config
from raceframe.core.models import Box, Detection
from raceframe.core.processing import analyze_image, process_folder
from raceframe.imaging.discovery import discover
from raceframe.ui.decisions import manual_crop, select_detection


def prepare(photo_factory, tmp_path, fake_detector, values, config):
    photo = photo_factory("input/subject.jpg", size=(1600, 1000))
    with Image.open(photo) as image:
        exif = image.getexif()
        exif[34665] = {37386: 100}
        image.save(tmp_path / "edited.jpg", quality=95, exif=exif)
    photo.write_bytes((tmp_path / "edited.jpg").read_bytes())
    fake_detector.detections = values
    inv = discover(photo.parent, tmp_path / "out")
    row = analyze_image(inv.root, inv.images[0], fake_detector, config)
    return photo, inv, row


@pytest.mark.parametrize("category,name", [("animals", "dog"), ("vehicles", "car")])
def test_nonhuman_composition_export_and_metadata(
    photo_factory, tmp_path, fake_detector, category, name
):
    config = Config(subject_category=category, selection_strategy="dominant", min_long_edge=300)
    subject = Box(300, 550, 1200, 850)
    photo, inv, row = prepare(
        photo_factory,
        tmp_path,
        fake_detector,
        [Detection(0, subject, 0.95, class_name=name)],
        config,
    )
    original = photo.read_bytes()
    assert row["source"]["head_reference"] is None
    assert row["source"]["estimated_head_fraction_output"] is None
    crop = Box(*row["crop_xyxy"])
    assert crop.contains(subject)
    assert abs(max(subject.width / crop.width, subject.height / crop.height) - 0.75) < 0.01
    result = process_folder(
        inv.root,
        inv.destination,
        detector=fake_detector,
        config=config,
        analysis_overrides={row["image_id"]: row},
    )
    out = result["images"][0]
    assert "metadata_verified" in out["warnings"]
    assert out["selected_detection_ids"] == [0] and out["subject_kind"] == "individual"
    with Image.open(Path(result["manifest_path"]).parent / out["output_relative_path"]) as image:
        assert image.getexif()[271] == "Synthetic Camera"
    assert photo.read_bytes() == original
    assert fake_detector.calls == 1
    import json

    import jsonschema

    schema = Path(__file__).parents[2] / "specs/001-reencuadre-cli/contracts/manifest.schema.json"
    jsonschema.validate(result, json.loads(schema.read_text()))


def test_manual_selection_and_crop_keep_associated_members(photo_factory, tmp_path, fake_detector):
    config = Config(selection_strategy="dominant", min_long_edge=300)
    person = Detection(0, Box(500, 100, 700, 650), 0.95)
    bicycle = Detection(1, Box(350, 450, 1000, 900), 0.95, class_name="bicycle")
    photo, inv, row = prepare(photo_factory, tmp_path, fake_detector, [person, bicycle], config)
    manual = select_detection(row, 0, config)
    assert manual["subject_kind"] == "associated"
    assert manual["selected_detection_ids"] == [0, 1]
    assert Box(**manual["composition"]["protected"]).contains(bicycle.box)
    with pytest.raises(ValueError, match="sujeto"):
        manual_crop(manual, Box(400, 0, 1200, 500), config)
    result = process_folder(
        inv.root,
        inv.destination,
        detector=fake_detector,
        config=config,
        analysis_overrides={row["image_id"]: manual},
    )
    assert result["images"][0]["selected_detection_ids"] == [0, 1]
    assert result["summary"]["exported"] == 1
    assert fake_detector.calls == 1
    import json

    import jsonschema

    schema = Path(__file__).parents[2] / "specs/001-reencuadre-cli/contracts/manifest.schema.json"
    jsonschema.validate(result, json.loads(schema.read_text()))


def test_group_export_protects_members_and_rejects_stale_category(
    photo_factory, tmp_path, fake_detector
):
    config = Config(selection_strategy="group", min_long_edge=300)
    values = [
        Detection(0, Box(50, 200, 350, 900), 0.95),
        Detection(1, Box(1100, 200, 1500, 900), 0.95),
    ]
    photo, inv, row = prepare(photo_factory, tmp_path, fake_detector, values, config)
    assert row["subject_kind"] == "group"
    assert all(Box(*row["crop_xyxy"]).contains(d.box) for d in values)
    result = process_folder(
        inv.root,
        inv.destination,
        detector=fake_detector,
        config=config,
        analysis_overrides={row["image_id"]: row},
    )
    assert result["images"][0]["selected_detection_ids"] == [0, 1]
    stale = process_folder(
        inv.root,
        inv.destination,
        detector=fake_detector,
        config=replace(config, subject_category="animals"),
        analysis_overrides={row["image_id"]: row},
    )
    assert stale["summary"]["exported"] == 0 and stale["summary"]["errors"] == 1
    broken = deepcopy(row)
    broken["composition"]["protected"] = {"x1": 50, "y1": 200, "x2": 350, "y2": 900}
    rejected = process_folder(
        inv.root,
        inv.destination,
        detector=fake_detector,
        config=config,
        analysis_overrides={row["image_id"]: broken},
    )
    assert rejected["summary"]["exported"] == 0


def test_context_minimum_resolution_and_infeasible_group_copy_original(
    photo_factory, tmp_path, fake_detector
):
    config = Config(selection_strategy="group", min_long_edge=1600, aspect="4:5")
    values = [
        Detection(0, Box(0, 100, 300, 900), 0.95),
        Detection(1, Box(1200, 100, 1600, 900), 0.95),
    ]
    photo, inv, row = prepare(photo_factory, tmp_path, fake_detector, values, config)
    assert row["composition"]["status"] == "review_required"
    result = process_folder(
        inv.root,
        inv.destination,
        detector=fake_detector,
        config=config,
        analysis_overrides={row["image_id"]: row},
    )
    exported = Path(result["manifest_path"]).parent / result["images"][0]["output_relative_path"]
    assert exported.read_bytes() == photo.read_bytes()
