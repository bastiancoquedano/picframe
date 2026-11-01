import errno

import pytest

from raceframe.core.processing import process_folder
from raceframe.export.manifest import AuditError


def test_audit_failure_stops_before_publication(
    photo_factory, tmp_path, fake_detector, monkeypatch
):
    path = photo_factory("input/a.jpg")
    import raceframe.export.manifest as manifest

    record = manifest.Journal.record

    def fail(self, kind, **kwargs):
        if kind == "export_prepared":
            raise AuditError("audit failed")
        return record(self, kind, **kwargs)

    monkeypatch.setattr(manifest.Journal, "record", fail)
    with pytest.raises(AuditError):
        process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    assert not list((tmp_path / "out").glob("job-*/*.jpg"))


def test_disk_full_fails_globally(photo_factory, tmp_path, fake_detector, monkeypatch):
    path = photo_factory("input/a.jpg")
    photo_factory("input/b.jpg")
    import raceframe.core.processing as processing

    def fail(*args, **kwargs):
        raise OSError(errno.ENOSPC, "full")

    monkeypatch.setattr(processing, "export_image", fail)
    result = process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    assert result["status"] == "failed"
    assert result["summary"]["not_attempted"] == 1
    assert result["summary"]["errors"] == 1
    assert fake_detector.calls == 1


def test_destination_without_exclusive_publication_is_rejected(
    photo_factory, tmp_path, fake_detector, monkeypatch
):
    path = photo_factory("input/a.jpg")
    import raceframe.core.processing as processing

    def fail(*args, **kwargs):
        raise OSError("unsupported volume")

    monkeypatch.setattr(processing, "validate_volume", fail)
    with pytest.raises(OSError):
        process_folder(path.parent, tmp_path / "out", detector=fake_detector)
    assert fake_detector.calls == 0
    assert not list((tmp_path / "out").glob("job-*/*.jpg"))
