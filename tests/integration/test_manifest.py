import json
from pathlib import Path

from raceframe.core.processing import process_folder
from raceframe.export.manifest import read_report


def test_manifest_inventory_and_accounting(photo_factory, tmp_path, fake_detector):
    path = photo_factory("input/a.jpg")
    (path.parent / "broken.jpg").write_bytes(b"broken")
    result = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    directory = Path(result["manifest_path"]).parent
    assert {"job.json", "inventory.json", "events.jsonl", "manifest.json"} <= {
        p.name for p in directory.iterdir()
    }
    report = read_report(directory)
    assert report["summary"]["total"] == 2
    assert report["summary"]["exported"] == 1
    assert report["summary"]["errors"] == 1
    assert len({row["image_id"] for row in report["images"]}) == 2
    assert report["images"][0]["source"]["oriented_dimensions"] == [120, 80]
    assert json.loads((directory / "inventory.json").read_text())["schema_version"] == 1


def test_manifest_matches_schema(photo_factory, tmp_path, fake_detector):
    import jsonschema

    path = photo_factory("input/a.jpg")
    result = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    schema = Path(__file__).parents[2] / "specs/001-reencuadre-cli/contracts/manifest.schema.json"
    jsonschema.validate(result, json.loads(schema.read_text()))
