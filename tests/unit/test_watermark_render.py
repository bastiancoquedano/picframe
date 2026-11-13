import numpy as np
import pytest
from PIL import Image

from raceframe.core.watermark_models import SignatureConfig, WatermarkConfig, WatermarkLayer
from raceframe.core.watermark_render import WatermarkRenderer


@pytest.fixture
def watermark_png(tmp_path):
    path = tmp_path / "stamp.png"
    stamp = Image.new("RGBA", (10, 10), (220, 20, 150, 255))
    stamp.save(path)
    stamp.close()
    return path


def test_traditional_composes_transparency_on_full_resolution(watermark_png):
    original = Image.new("RGB", (40, 30), (10, 40, 90))
    config = WatermarkConfig(
        mode="traditional", layers=(WatermarkLayer(watermark_png, opacity=0.5, width_fraction=0.5),)
    )
    with WatermarkRenderer(config) as renderer:
        result = renderer.render(original)
    assert result.size == original.size
    assert result.mode == "RGB"
    assert result.getpixel((0, 0)) == original.getpixel((0, 0))
    assert result.getpixel((20, 15)) != original.getpixel((20, 15))
    original.close()
    result.close()


def test_traditional_render_does_not_require_numpy(watermark_png, monkeypatch):
    import builtins

    original_import = builtins.__import__

    def import_without_numpy(name, *args, **kwargs):
        if name == "numpy":
            raise AssertionError("Tradicional no debe importar NumPy")
        return original_import(name, *args, **kwargs)

    image = Image.new("RGB", (40, 30), (10, 40, 90))
    monkeypatch.setattr(builtins, "__import__", import_without_numpy)
    config = WatermarkConfig(layers=(WatermarkLayer(watermark_png),))
    with WatermarkRenderer(config) as renderer:
        rendered = renderer.render(image)
    assert rendered.size == image.size
    rendered.close()
    image.close()


def test_smart_mask_preserves_confident_person_pixels_before_signature(watermark_png):
    original = Image.new("RGB", (40, 30), (10, 40, 90))
    mask = np.zeros((30, 40), dtype=np.uint8)
    mask[7:23, 14:27] = 255
    config = WatermarkConfig(
        mode="smart", layers=(WatermarkLayer(watermark_png, width_fraction=0.9),)
    )
    with WatermarkRenderer(config) as renderer:
        background = renderer.render(original, mask, include_signature=False)
    source = np.asarray(original)
    output = np.asarray(background)
    assert np.array_equal(output[mask == 255], source[mask == 255])
    assert np.any(np.any(output[mask == 0] != source[mask == 0], axis=1))
    original.close()
    background.close()


def test_signature_is_drawn_after_person_mask(watermark_png):
    original = Image.new("RGB", (120, 80), (10, 40, 90))
    mask = np.ones((80, 120), dtype=np.uint8) * 255
    config = WatermarkConfig(
        mode="smart",
        layers=(WatermarkLayer(watermark_png),),
        signature=SignatureConfig(enabled=True, kind="text", text="PICFRAME", size_fraction=0.15),
    )
    with WatermarkRenderer(config) as renderer:
        before_id = renderer.render(original, mask, include_signature=False)
        result = renderer.render(original, mask, include_signature=True)
    assert np.array_equal(np.asarray(before_id), np.asarray(original))
    assert np.any(np.asarray(result) != np.asarray(original))
    original.close()
    before_id.close()
    result.close()


def test_empty_mask_displays_main_watermark_as_normal_traditional_layer(watermark_png):
    original = Image.new("RGB", (40, 30), (10, 40, 90))
    config = WatermarkConfig(mode="smart", layers=(WatermarkLayer(watermark_png),))
    with WatermarkRenderer(config) as renderer:
        result = renderer.render(original, np.zeros((30, 40), dtype=np.uint8))
        unmasked = renderer.render(original, None)
    assert np.array_equal(np.asarray(result), np.asarray(unmasked))
    original.close()
    result.close()
    unmasked.close()
