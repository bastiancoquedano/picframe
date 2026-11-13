import json
from contextlib import contextmanager
from pathlib import Path
from threading import Event

import numpy as np
import pytest
from PIL import Image

from raceframe.core.models import InputImage, Inventory
from raceframe.core.watermark_models import WatermarkConfig, WatermarkLayer
from raceframe.core.watermark_processing import process_watermark_folder
from raceframe.export.jpeg import ExportResult
from raceframe.export.manifest import read_report


def make_logo(path):
    Image.new("RGBA", (18, 12), (255, 0, 0, 190)).save(path)
    return path


class Segmenter:
    def __init__(self, status="ok"):
        self.status = status
        self.calls = 0

    def segment(self, image):
        self.calls += 1
        mask = np.zeros((image.height, image.width), dtype=np.uint8)
        if self.status == "ok":
            mask[5:20, 5:15] = 255
        return type(
            "Result",
            (),
            {
                "mask": mask,
                "status": self.status,
                "reason": "synthetic_failure" if self.status == "error" else None,
                "backend": "fake",
                "backend_version": "test",
                "quality": "accurate",
                "revision": 1,
            },
        )()


def smart_config(logo, fallback="traditional_foreground"):
    return WatermarkConfig(
        mode="smart",
        layers=(WatermarkLayer(logo, width_fraction=0.7),),
        fallback_policy=fallback,
    )


def test_traditional_never_initializes_or_calls_person_segmenter(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(40, 30))
    logo = make_logo(tmp_path / "logo.png")

    def forbidden():
        raise AssertionError("Traditional no debe iniciar Vision")

    result = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=WatermarkConfig(layers=(WatermarkLayer(logo),)),
        segmenter_factory=forbidden,
    )
    assert result["status"] == "completed"
    assert result["job_type"] == "watermark"
    assert len(result["config"]["layers"][0]["asset_sha256"]) == 64
    assert result["summary"]["exported"] == 1
    assert result["images"][0]["watermark"]["segmentation_status"] == "not_attempted"
    assert result["images"][0]["warnings"].count("metadata_verified") == 1
    import jsonschema

    schema_path = (
        Path(__file__).parents[2] / "specs/001-reencuadre-cli/contracts/manifest.schema.json"
    )
    jsonschema.validate(result, json.loads(schema_path.read_text()))
    report = read_report(Path(result["manifest_path"]).parent)
    assert report["status"] == "completed"


@pytest.mark.parametrize(
    "policy,expected_status,expected_bytes",
    [
        ("traditional_foreground", "exported", False),
        ("copy_original", "exported", True),
        ("skip_image", "omitted", None),
    ],
)
def test_smart_segmentation_failure_applies_configured_fallback_and_flags_review(
    photo_factory, tmp_path, policy, expected_status, expected_bytes
):
    source = photo_factory("input/a.jpg", size=(40, 30))
    original = source.read_bytes()
    logo = make_logo(tmp_path / "logo.png")
    segmenter = Segmenter("error")
    result = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=smart_config(logo, policy),
        segmenter_factory=lambda: segmenter,
    )
    row = result["images"][0]
    assert row["operation_status"] == expected_status
    assert row["watermark"]["review_required"] is True
    assert row["watermark"]["fallback_applied"] == policy
    assert "segmentation_fallback" in row["warnings"]
    if expected_bytes is True:
        output = Path(result["manifest_path"]).parent / row["output_relative_path"]
        assert output.read_bytes() == original
        assert "source_bytes_preserved" in row["warnings"]
    elif expected_bytes is False:
        output = Path(result["manifest_path"]).parent / row["output_relative_path"]
        assert output.read_bytes() != original
    else:
        assert row["error"]["code"] == "segmentation_failed"
        assert row["output_relative_path"] is None
        assert not list(Path(result["manifest_path"]).parent.glob("*.jpg"))
        assert result["status"] == "completed_with_errors"
        assert result["summary"]["omitted"] == 1
        assert result["summary"]["errors"] == 1
    recovered = read_report(Path(result["manifest_path"]).parent)
    assert recovered["images"][0]["watermark"]["review_required"] is True


def test_segmenter_initialization_failure_falls_back_for_each_photo(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(40, 30))
    photo_factory("input/b.jpg", size=(40, 30))
    logo = make_logo(tmp_path / "logo.png")
    attempts = []

    def unavailable_segmenter():
        attempts.append(True)
        raise RuntimeError("Vision framework unavailable")

    result = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=smart_config(logo),
        segmenter_factory=unavailable_segmenter,
    )
    assert result["summary"]["exported"] == 2
    assert result["summary"]["review_required"] == 2
    assert len(attempts) == 1
    assert all(
        row["watermark"]["fallback_applied"] == "traditional_foreground" for row in result["images"]
    )


def test_smart_mask_marks_behind_subject_and_empty_mask_is_valid(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(40, 30))
    logo = make_logo(tmp_path / "logo.png")
    segmenter = Segmenter("ok")
    config = smart_config(logo)
    result = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=config,
        segmenter_factory=lambda: segmenter,
    )
    row = result["images"][0]
    assert row["operation_status"] == "exported"
    assert row["watermark"]["segmentation_status"] == "ok"
    assert not row["watermark"]["review_required"]
    assert segmenter.calls == 1

    empty = Segmenter("empty")
    second = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=config,
        segmenter_factory=lambda: empty,
    )
    assert second["images"][0]["operation_status"] == "exported"
    assert second["images"][0]["watermark"]["segmentation_status"] == "empty"
    assert second["images"][0]["watermark"]["review_required"] is False


def test_mask_dimensions_mismatch_uses_the_selected_fallback(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(40, 30))
    logo = make_logo(tmp_path / "logo.png")

    class BadSegmenter:
        def segment(self, image):
            return type(
                "Result",
                (),
                {
                    "mask": np.ones((3, 3), dtype=np.uint8) * 255,
                    "status": "ok",
                    "reason": None,
                    "backend": "fake",
                    "backend_version": "test",
                    "quality": "accurate",
                    "revision": 1,
                },
            )()

    result = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=smart_config(logo),
        segmenter_factory=BadSegmenter,
    )
    watermark = result["images"][0]["watermark"]
    assert watermark["segmentation_status"] == "error"
    assert watermark["segmentation_reason"] == "mask_dimensions_mismatch"
    assert watermark["fallback_applied"] == "traditional_foreground"
    assert watermark["review_required"]


def test_copy_original_fallback_reports_oriented_dimensions(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(600, 400), orientation=6)
    original = source.read_bytes()
    logo = make_logo(tmp_path / "logo.png")
    result = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=smart_config(logo, "copy_original"),
        segmenter_factory=lambda: Segmenter("error"),
    )
    row = result["images"][0]
    assert row["final_dimensions"] == [400, 600]
    output = Path(result["manifest_path"]).parent / row["output_relative_path"]
    assert output.read_bytes() == original


def test_smart_segmenter_receives_exif_oriented_pixels(photo_factory, tmp_path):
    source = photo_factory("input/a.jpg", size=(600, 400), orientation=6)
    logo = make_logo(tmp_path / "logo.png")
    seen_sizes = []

    class CaptureOrientation:
        def segment(self, image):
            seen_sizes.append(image.size)
            return type(
                "Result",
                (),
                {
                    "mask": np.zeros((image.height, image.width), dtype=np.uint8),
                    "status": "error",
                    "reason": "synthetic_failure",
                    "backend": "fake",
                    "backend_version": "test",
                    "quality": "accurate",
                    "revision": 1,
                },
            )()

    process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=smart_config(logo),
        segmenter_factory=CaptureOrientation,
    )
    assert seen_sizes == [(400, 600)]


def test_metadata_verification_failure_does_not_publish_a_jpeg(
    photo_factory, tmp_path, monkeypatch
):
    import raceframe.export.metadata as metadata

    source = photo_factory("input/a.jpg", size=(40, 30))
    logo = make_logo(tmp_path / "logo.png")

    def unavailable():
        raise metadata.MetadataError("ExifTool missing")

    monkeypatch.setattr(metadata, "tool_path", unavailable)
    result = process_watermark_folder(
        source.parent,
        tmp_path / "out",
        config=WatermarkConfig(layers=(WatermarkLayer(logo),)),
    )
    row = result["images"][0]
    job_dir = Path(result["manifest_path"]).parent
    assert row["operation_status"] == "error"
    assert row["output_relative_path"] is None
    assert not list(job_dir.glob("*.jpg"))


def test_batch_continues_after_bad_image_and_cancel_leaves_remaining_unattempted(
    photo_factory, tmp_path
):
    good = photo_factory("input/a.jpg", size=(40, 30))
    photo_factory("input/b.jpg", size=(40, 30))
    (good.parent / "broken.jpg").write_bytes(b"not jpeg")
    logo = make_logo(tmp_path / "logo.png")
    progress = []
    result = process_watermark_folder(
        good.parent,
        tmp_path / "out",
        config=WatermarkConfig(layers=(WatermarkLayer(logo),)),
        progress=lambda n, total: progress.append((n, total)),
    )
    assert result["summary"]["exported"] == 2
    assert result["summary"]["errors"] == 1
    assert progress[-1] == (3, 3)

    cancel = Event()

    def stop_after_first(n, total):
        if n == 1:
            cancel.set()

    cancelled = process_watermark_folder(
        good.parent,
        tmp_path / "out-cancel",
        config=WatermarkConfig(layers=(WatermarkLayer(logo),)),
        progress=stop_after_first,
        cancel=cancel,
    )
    assert cancelled["status"] == "cancelled"
    assert cancelled["summary"]["exported"] == 1
    assert cancelled["summary"]["not_attempted"] == 2


def test_thousand_photo_inventory_is_processed_incrementally(tmp_path, monkeypatch):
    import raceframe.core.watermark_processing as processing

    source = tmp_path / "source"
    source.mkdir()
    logo = make_logo(tmp_path / "logo.png")
    image = Image.new("RGB", (20, 15), "blue")
    items = tuple(
        InputImage(
            image_id=f"{index:04}.jpg",
            path=source / f"{index:04}.jpg",
            relative_path=f"{index:04}.jpg",
            size_bytes=1,
            mtime_ns=1,
            device=1,
            inode=index + 1,
        )
        for index in range(1000)
    )
    monkeypatch.setattr(
        processing,
        "discover",
        lambda *args, **kwargs: Inventory(source.resolve(), tmp_path / "out", items),
    )

    @contextmanager
    def fake_load(root, item):
        yield type(
            "Loaded",
            (),
            {
                "image": image,
                "stored_size": image.size,
                "source_orientation": 1,
                "warnings": (),
            },
        )()

    def fake_export(root, item, loaded, rendered, destination, **kwargs):
        if kwargs.get("before_publish"):
            kwargs["before_publish"](
                {
                    "temporary": ".tmp",
                    "output_relative_path": item.relative_path,
                    "sha256": "a" * 64,
                    "dimensions": image.size,
                    "warnings": ["metadata_verified"],
                }
            )
        return ExportResult(
            destination / item.relative_path,
            "a" * 64,
            image.size,
            ("metadata_verified",),
        )

    monkeypatch.setattr(processing, "load_image", fake_load)
    monkeypatch.setattr(processing, "export_rendered_jpeg", fake_export)
    progress = []
    try:
        result = process_watermark_folder(
            source,
            tmp_path / "out",
            config=WatermarkConfig(layers=(WatermarkLayer(logo),)),
            progress=lambda n, total: progress.append(n),
        )
    finally:
        image.close()
    assert result["summary"]["exported"] == 1000
    assert len(progress) == 1000 and progress[-1] == 1000
    assert result["summary"]["not_attempted"] == 0
