import json

import pytest
from PIL import Image

from raceframe.core.watermark_models import (
    SignatureConfig,
    WatermarkConfig,
    WatermarkLayer,
    validate_assets,
)
from raceframe.watermark.presets import WatermarkPresetStore


def test_preset_is_local_versioned_and_round_trips(tmp_path):
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (80, 40), (255, 0, 0, 220)).save(logo)
    config = WatermarkConfig(
        mode="smart",
        layers=(WatermarkLayer(logo, width_fraction=0.75),),
        signature=SignatureConfig(enabled=True, kind="text", text="@picframe"),
    )
    store = WatermarkPresetStore(tmp_path / "application-support")
    saved = store.save("Carrera Ñandú", config)
    assert saved.is_relative_to(tmp_path)
    assert store.names() == ("Carrera Ñandú",)
    name, restored = store.load("Carrera Ñandú")
    assert name == "Carrera Ñandú"
    assert restored.mode == "smart"
    assert restored.layers[0].asset_path == logo
    assert len(restored.layers[0].asset_sha256) == 64
    assert "Carrera Ñandú" == json.loads(saved.read_text())["name"]
    assert validate_assets(restored)


def test_preset_warns_when_png_was_replaced_after_saving(tmp_path):
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (80, 40), (255, 0, 0, 220)).save(logo)
    store = WatermarkPresetStore(tmp_path / "presets")
    store.save("Final", WatermarkConfig(layers=(WatermarkLayer(logo),)))
    Image.new("RGBA", (80, 40), (0, 255, 0, 220)).save(logo)
    _, config = store.load("Final")
    with pytest.raises(ValueError, match="cambió"):
        validate_assets(config)


def test_missing_png_is_identified_when_loading_preset(tmp_path):
    store = WatermarkPresetStore(tmp_path / "presets")
    missing = tmp_path / "missing.png"
    # Create a temporary valid asset, save its identity, then remove it.
    Image.new("RGBA", (16, 16), (0, 0, 255, 255)).save(missing)
    store.save("Broken", WatermarkConfig(layers=(WatermarkLayer(missing),)))
    missing.unlink()
    _, config = store.load("Broken")
    with pytest.raises(ValueError, match="No existe"):
        validate_assets(config)
