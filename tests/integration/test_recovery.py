from copy import deepcopy
from pathlib import Path

import pytest

from raceframe.core.processing import blank_result
from raceframe.export.jpeg import file_hash
from raceframe.export.manifest import JobActiveError, Journal, read_report
from raceframe.imaging.discovery import discover


def build_job(photo_factory, tmp_path):
    path = photo_factory("input/a.jpg")
    inv = discover(path.parent)
    directory = tmp_path / "job"
    directory.mkdir()
    header = {
        "schema_version": 1,
        "job_id": "test",
        "created_at": "2026-11-01T12:00:00+00:00",
        "finished_at": None,
        "status": "running",
        "input_root": str(inv.root),
        "output_root": str(tmp_path),
        "config": {},
        "runtime": {},
        "warnings": [],
    }
    rows = [blank_result(inv.images[0])]
    return directory, header, rows, path


def test_active_job_and_truncated_tail(photo_factory, tmp_path):
    directory, header, rows, path = build_job(photo_factory, tmp_path)
    with Journal(directory, header, rows) as journal:
        journal.record("image_started", image_id=rows[0]["image_id"])
        with pytest.raises(JobActiveError):
            read_report(directory, recover=True)
    with (directory / "events.jsonl").open("ab") as out:
        out.write(b'{"partial":')
    report = read_report(directory, recover=True)
    assert report["status"] == "interrupted"
    assert report["summary"]["not_attempted"] == 1
    assert "truncated_journal_tail" in report["warnings"]
    assert Path(report["manifest_path"]).exists()
    assert not (directory / "manifest.json").exists()


@pytest.mark.parametrize("matching", [True, False])
def test_reconcile_publication_without_confirmation(photo_factory, tmp_path, matching):
    directory, header, rows, path = build_job(photo_factory, tmp_path)
    target = directory / "a.jpg"
    target.write_bytes(path.read_bytes() if matching else b"wrong")
    row = deepcopy(rows[0])
    row.update(
        operation_status="exported",
        output_relative_path="a.jpg",
        output_sha256=file_hash(path),
        final_dimensions=[120, 80],
    )
    with Journal(directory, header, rows) as journal:
        journal.record(
            "export_prepared",
            image_id=row["image_id"],
            result=row,
            intent={"output_relative_path": "a.jpg", "sha256": file_hash(path)},
        )
    report = read_report(directory, recover=True)
    assert report["images"][0]["operation_status"] == ("exported" if matching else "error")
    assert target.read_bytes() == (path.read_bytes() if matching else b"wrong")


def test_sequence_corruption_is_not_silently_ignored(photo_factory, tmp_path):
    directory, header, rows, path = build_job(photo_factory, tmp_path)
    with Journal(directory, header, rows) as journal:
        journal.record("image_started", image_id=rows[0]["image_id"])
    with (directory / "events.jsonl").open("ab") as out:
        out.write(b'{"seq":99,"type":"bad"}\n')
    with pytest.raises(ValueError):
        read_report(directory, recover=True)
