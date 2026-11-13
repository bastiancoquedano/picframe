import pytest
from PIL import Image

from raceframe.core.watermark_models import (
    SignatureConfig,
    WatermarkConfig,
    WatermarkLayer,
    preset_from_dict,
    preset_to_dict,
    validate_assets,
)


def test_traditional_allows_multiple_layers_and_smart_requires_one(tmp_path):
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGBA", (20, 10), (255, 0, 0, 128)).save(first)
    Image.new("RGBA", (10, 10), (0, 255, 0, 128)).save(second)
    traditional = WatermarkConfig(
        mode="traditional", layers=(WatermarkLayer(first), WatermarkLayer(second))
    )
    smart = WatermarkConfig(mode="smart", layers=(WatermarkLayer(first),))
    assert len(validate_assets(traditional)) == 2
    assert len(validate_assets(smart)) == 1
    empty = WatermarkConfig(mode="smart")
    with pytest.raises(ValueError, match="una marca PNG"):
        empty.validate_for_run()


def test_preset_round_trip_and_signature_fallbacks(tmp_path):
    image = tmp_path / "logo.png"
    Image.new("RGBA", (32, 20), (20, 50, 90, 180)).save(image)
    config = WatermarkConfig(
        mode="smart",
        layers=(WatermarkLayer(image, width_fraction=0.7, opacity=0.42),),
        signature=SignatureConfig(enabled=True, kind="text", text="@picframe"),
        fallback_policy="copy_original",
    )
    import json

    restored = preset_from_dict(json.loads(json.dumps(preset_to_dict("Carrera", config))))
    assert restored[0] == "Carrera"
    assert restored[1].mode == config.mode
    assert restored[1].layers[0].asset_sha256 is not None
    assert validate_assets(config)


@pytest.mark.parametrize(
    "values",
    [
        {"mode": "unknown"},
        {"mode": "traditional", "layers": [{"asset_path": "logo.jpg"}]},
        {"mode": "traditional", "layers": [{"asset_path": "logo.png", "opacity": 1.4}]},
        {"mode": "smart", "layers": [{"asset_path": "logo.png"}], "fallback_policy": "upload"},
        {
            "mode": "traditional",
            "layers": [],
            "signature": {"enabled": True, "kind": "text", "text": ""},
        },
    ],
)
def test_rejects_invalid_presets(values):
    with pytest.raises(ValueError):
        preset_from_dict({"version": 1, "name": "invalid", "config": values})


def test_missing_png_is_reported_without_substituting_an_asset(tmp_path):
    config = WatermarkConfig(layers=(WatermarkLayer(tmp_path / "missing.png"),))
    with pytest.raises(ValueError, match="No existe la marca"):
        validate_assets(config)


def test_rejects_fully_transparent_png(tmp_path):
    image = tmp_path / "blank.png"
    Image.new("RGBA", (20, 20), (0, 0, 0, 0)).save(image)
    with pytest.raises(ValueError, match="completamente transparente"):
        validate_assets(WatermarkConfig(layers=(WatermarkLayer(image),)))


def test_missing_signature_png_is_reported(tmp_path):
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (16, 12), (255, 0, 0, 180)).save(logo)
    config = WatermarkConfig(
        layers=(WatermarkLayer(logo),),
        signature=SignatureConfig(enabled=True, kind="png", asset_path=tmp_path / "signature.png"),
    )
    with pytest.raises(ValueError, match="No existe la marca PNG: signature.png"):
        validate_assets(config)
