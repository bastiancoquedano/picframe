from threading import Event

from PIL import Image

from raceframe.ui.window import MainWindow


def test_window_keeps_framing_page_and_adds_independent_watermark_tab(qtbot, tmp_path):
    from raceframe.watermark.presets import WatermarkPresetStore

    window = MainWindow(
        watermark_preset_store_factory=lambda: WatermarkPresetStore(tmp_path / "presets")
    )
    qtbot.addWidget(window)
    assert window.tabs.count() == 2
    assert window.tabs.tabText(0) == "Encuadre"
    assert window.tabs.tabText(1) == "Marcas de agua"
    assert window.watermark_page.run_button.isEnabled() is False


def test_page_config_supports_traditional_layers_and_limits_smart_to_one(tmp_path, qtbot):
    from raceframe.ui.watermark_page import WatermarkPage
    from raceframe.watermark.presets import WatermarkPresetStore

    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    Image.new("RGBA", (16, 12), (255, 0, 0, 180)).save(first)
    Image.new("RGBA", (16, 12), (0, 0, 255, 180)).save(second)
    page = WatermarkPage(preset_store_factory=lambda: WatermarkPresetStore(tmp_path / "presets"))
    qtbot.addWidget(page)
    page.set_layers([first, second])
    page.width_fraction.setValue(75)
    page.opacity.setValue(42)
    page.anchor.setCurrentIndex(page.anchor.findData("top_left"))
    page.layers_combo.setCurrentIndex(1)
    page.width_fraction.setValue(50)
    page.opacity.setValue(65)
    page.anchor.setCurrentIndex(page.anchor.findData("bottom_right"))
    config = page.build_config()
    assert config.mode == "traditional"
    assert len(config.layers) == 2
    assert config.layers[0].width_fraction == 0.75
    assert config.layers[0].opacity == 0.42
    assert config.layers[0].anchor == "top_left"
    assert config.layers[1].width_fraction == 0.5
    assert config.layers[1].opacity == 0.65
    assert config.layers[1].anchor == "bottom_right"
    page.move_layer(-1)
    assert page.build_config().layers[0].asset_path == second
    page.mode.setCurrentIndex(page.mode.findData("smart"))
    try:
        page.build_config()
    except ValueError as exc:
        assert "un solo PNG" in str(exc)
    else:
        raise AssertionError("Smart debe restringir una sola marca principal")
    page.mode.setCurrentIndex(page.mode.findData("traditional"))
    page.set_layers([first])
    page.signature_enabled.setChecked(True)
    page.signature_kind.setCurrentIndex(page.signature_kind.findData("png"))
    page.signature_asset = second
    page.signature_size.setValue(5)
    page.signature_opacity.setValue(75)
    page.signature_anchor.setCurrentIndex(page.signature_anchor.findData("top_right"))
    signature = page.build_config().signature
    assert signature.asset_path == second
    assert signature.size_fraction == 0.05
    assert signature.opacity == 0.75
    assert signature.anchor == "top_right"
    store = WatermarkPresetStore(tmp_path / "presets")
    store.save("Evento", page.build_config())
    page.refresh_presets()
    page.preset_combo.setCurrentIndex(page.preset_combo.findData("Evento"))
    page.load_preset()
    restored = page.build_config()
    assert restored.layers[0].asset_path == first
    assert restored.signature.asset_path == second


def test_traditional_preview_and_batch_run_use_worker_and_persist_manifest(
    qtbot, photo_factory, tmp_path
):
    from raceframe.ui.watermark_page import WatermarkPage
    from raceframe.watermark.presets import WatermarkPresetStore

    source = photo_factory("input/a.jpg", size=(80, 60))
    logo = tmp_path / "logo.png"
    Image.new("RGBA", (16, 12), (255, 0, 0, 180)).save(logo)
    page = WatermarkPage(preset_store_factory=lambda: WatermarkPresetStore(tmp_path / "presets"))
    qtbot.addWidget(page)
    page.set_source(source.parent)
    page.output_edit.setText(str(tmp_path / "out"))
    page.set_layers([logo])
    page.start_preview()
    qtbot.waitUntil(lambda: page.worker is None, timeout=10000)
    assert page.before_view.original_size == (80, 60)
    assert page.after_view.original_size == (80, 60)
    page.start_run()
    qtbot.waitUntil(lambda: page.worker is None, timeout=15000)
    assert page.last_result["summary"]["exported"] == 1
    assert page.last_result["images"][0]["warnings"].count("metadata_verified") == 1
    assert page.progress_bar.value() == 1
    assert "1 exportadas" in page.status.text()


def test_closing_window_cancels_watermark_worker(qtbot, tmp_path):
    from raceframe.watermark.presets import WatermarkPresetStore

    window = MainWindow(
        watermark_preset_store_factory=lambda: WatermarkPresetStore(tmp_path / "presets")
    )
    qtbot.addWidget(window)
    window.show()
    started = Event()
    results = []

    def wait_until_cancelled(progress, record, cancel):
        started.set()
        cancel.wait(5)
        return {"cancelled": cancel.is_set()}

    window.watermark_page._launch(wait_until_cancelled, results.append)
    qtbot.waitUntil(started.is_set, timeout=5000)
    window.close()
    qtbot.waitUntil(lambda: window.watermark_page.worker is None, timeout=5000)
    qtbot.waitUntil(lambda: not window.isVisible(), timeout=5000)
    assert results == [{"cancelled": True}]
