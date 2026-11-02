"""Diagnóstico reproducible del bundle con datos sintéticos, sin fotografías privadas."""

import json
import tempfile
from pathlib import Path


def run_smoke(report_path):
    from PIL import Image, ImageDraw
    from PySide6.QtWidgets import QApplication

    from raceframe.config import Config
    from raceframe.core.detection import YoloDetector
    from raceframe.core.models import Box, Detection
    from raceframe.core.processing import analyze_image, process_folder
    from raceframe.imaging.discovery import discover
    from raceframe.ui.resources import model_path
    from raceframe.ui.window import MainWindow

    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix="raceframe-bundle-") as name:
        root = Path(name)
        source = root / "input"
        source.mkdir()
        image = Image.new("RGB", (800, 1200), "#b7cfd1")
        draw = ImageDraw.Draw(image)
        draw.rectangle((280, 400, 460, 1000), fill="#d06544")
        exif = Image.Exif()
        exif[271] = "Synthetic"
        exif[34665] = {37386: 100}
        image.save(source / "sample.jpg", exif=exif, quality=95)
        image.close()
        real = YoloDetector(model_path(), Config())
        real_categories = []
        for category in ("people", "animals", "vehicles"):
            real.config = Config(subject_category=category)
            with Image.new("RGB", (120, 80), "black") as empty:
                real.detect(empty)
            real_categories.append(category)

        class Detector:
            def detect(self, image):
                return (Detection(0, Box(280, 400, 460, 1000), 0.99),)

        config = Config(min_long_edge=300)
        inv = discover(source, root / "out")
        detector = Detector()
        row = analyze_image(inv.root, inv.images[0], detector, config)
        result = process_folder(
            source,
            root / "out",
            detector=detector,
            config=config,
            analysis_overrides={row["image_id"]: row},
        )
        synthetic_scenarios = []
        scenarios = [
            (
                "animals",
                "dominant",
                [Detection(0, Box(150, 500, 650, 900), 0.99, class_name="dog")],
            ),
            (
                "vehicles",
                "dominant",
                [Detection(0, Box(100, 600, 700, 900), 0.99, class_name="car")],
            ),
            (
                "people",
                "dominant",
                [
                    Detection(0, Box(280, 200, 460, 800), 0.99),
                    Detection(1, Box(180, 600, 650, 1000), 0.99, class_name="bicycle"),
                ],
            ),
            (
                "people",
                "group",
                [
                    Detection(0, Box(100, 300, 250, 1000), 0.99),
                    Detection(1, Box(500, 300, 650, 1000), 0.99),
                ],
            ),
        ]

        class ScenarioDetector:
            def __init__(self, values):
                self.values = values

            def detect(self, image):
                return tuple(self.values)

        for category, strategy, detections in scenarios:
            scenario_detector = ScenarioDetector(detections)
            scenario_config = Config(
                subject_category=category, selection_strategy=strategy, min_long_edge=300
            )
            scenario_row = analyze_image(
                inv.root, inv.images[0], scenario_detector, scenario_config
            )
            scenario_result = process_folder(
                source,
                root / "out",
                detector=scenario_detector,
                config=scenario_config,
                analysis_overrides={scenario_row["image_id"]: scenario_row},
            )
            if scenario_result["summary"]["exported"] != 1:
                raise RuntimeError("Falló escenario sintético del bundle: " + category)
            synthetic_scenarios.append(
                {
                    "category": category,
                    "strategy": strategy,
                    "kind": scenario_row["subject_kind"],
                    "members": scenario_row["selected_detection_ids"],
                    "metadata_verified": "metadata_verified"
                    in scenario_result["images"][0]["warnings"],
                }
            )
        window = MainWindow()
        window.review_filter.setCurrentIndex(1)
        window.on_record(row)
        window.apply_review_filter()
        if not window.photo_list.item(0).isHidden() or window.selected_id() is not None:
            raise RuntimeError("Falló filtro de revisión del bundle")
        window.review_filter.setCurrentIndex(0)
        if window.photo_list.item(0).isHidden() or len(window.records) != 1:
            raise RuntimeError("El filtro alteró el análisis del bundle")
        window.show()
        app.processEvents()
        window.close()
        record = {
            "bundle": True,
            "qt_window_created": True,
            "review_filter_verified": True,
            "real_inference_cpu": True,
            "real_categories": real_categories,
            "synthetic_scenarios": synthetic_scenarios,
            "status": result["status"],
            "summary": result["summary"],
            "metadata_warnings": result["images"][0]["warnings"],
        }
        Path(report_path).write_text(json.dumps(record, indent=2))
        if result["summary"]["exported"] != 1:
            raise RuntimeError("Falló exportación del bundle")
