"""Página de marcas de agua, independiente del análisis de encuadre."""

from datetime import date
from pathlib import Path
from time import monotonic

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QImage
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from raceframe.core.watermark_models import (
    SignatureConfig,
    WatermarkConfig,
    WatermarkLayer,
)
from raceframe.core.watermark_processing import process_watermark_folder
from raceframe.export.directory import validate_job_name
from raceframe.imaging.discovery import discover
from raceframe.imaging.loader import load_image
from raceframe.ui.preview import PhotoView
from raceframe.ui.workers import TaskWorker

ANCHOR_OPTIONS = (
    ("Centro", "center"),
    ("Arriba izquierda", "top_left"),
    ("Arriba centro", "top_center"),
    ("Arriba derecha", "top_right"),
    ("Centro izquierda", "center_left"),
    ("Centro derecha", "center_right"),
    ("Abajo izquierda", "bottom_left"),
    ("Abajo centro", "bottom_center"),
    ("Abajo derecha", "bottom_right"),
)


class WatermarkPage(QWidget):
    def __init__(self, parent=None, *, preset_store_factory=None):
        super().__init__(parent)
        self.preset_store_factory = preset_store_factory
        self.worker = None
        self.threads = []
        self.last_result = None
        self.selected_assets = []
        self.layer_settings = []
        self._loading_layer_settings = False
        self.started = None
        self.close_when_finished = False
        self._closing_main_window = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 8)

        paths = QGridLayout()
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Carpeta con fotografías JPG/JPEG")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Carpeta donde se guardarán los trabajos")
        self.folder_name_edit = QLineEdit(f"Picframe_Marcas_{date.today().isoformat()}")
        for row, (label, edit, button_text, callback) in enumerate(
            (
                ("Origen", self.source_edit, "Elegir origen…", self.pick_source),
                ("Destino", self.output_edit, "Elegir destino…", self.pick_output),
            )
        ):
            button = QPushButton(button_text)
            button.clicked.connect(callback)
            paths.addWidget(QLabel(label), row, 0)
            paths.addWidget(edit, row, 1)
            paths.addWidget(button, row, 2)
        paths.addWidget(QLabel("Nombre de carpeta"), 2, 0)
        paths.addWidget(self.folder_name_edit, 2, 1, 1, 2)
        self.recursive = QCheckBox("Incluir subcarpetas")
        paths.addWidget(self.recursive, 3, 1)
        self.file_count = QLabel("Sin carpeta seleccionada")
        self.file_count.setObjectName("muted")
        paths.addWidget(self.file_count, 3, 2)
        layout.addLayout(paths)

        settings = QGridLayout()
        self.mode = self._combo(
            (("Tradicional", "traditional"), ("Smart · detrás de personas", "smart"))
        )
        self.layers_combo = QComboBox()
        self.layers_combo.setPlaceholderText("No hay PNG seleccionados")
        self.add_layer_button = QPushButton("Añadir PNG…")
        self.add_layer_button.clicked.connect(self.pick_assets)
        self.remove_layer_button = QPushButton("Quitar")
        self.remove_layer_button.clicked.connect(self.remove_layer)
        self.layer_up_button = QPushButton("↑")
        self.layer_up_button.setToolTip("Mover marca hacia delante")
        self.layer_up_button.clicked.connect(lambda: self.move_layer(-1))
        self.layer_down_button = QPushButton("↓")
        self.layer_down_button.setToolTip("Mover marca hacia atrás")
        self.layer_down_button.clicked.connect(lambda: self.move_layer(1))
        self.layers_combo.currentIndexChanged.connect(self.load_layer_settings)
        self.anchor = self._combo(ANCHOR_OPTIONS)
        self.width_fraction = self._double(65, 1, 200, 1, "% del ancho", 100)
        self.opacity = self._double(30, 1, 100, 1, "% opacidad", 100)
        self.repeat = QCheckBox("Repetir en patrón")
        self.quality = QSpinBox()
        self.quality.setRange(1, 95)
        self.quality.setValue(95)
        self.quality.setSuffix(" %")
        self.signature_enabled = QCheckBox("Añadir identificación")
        self.signature_kind = self._combo((("Texto", "text"), ("PNG", "png")))
        self.signature_text = QLineEdit()
        self.signature_text.setPlaceholderText("Nombre, web o cuenta")
        self.signature_asset = None
        self.signature_asset_label = QLabel("Sin PNG de identificación")
        self.signature_asset_label.setObjectName("muted")
        self.signature_asset_button = QPushButton("Elegir PNG de identificación…")
        self.signature_asset_button.clicked.connect(self.pick_signature_asset)
        self.signature_anchor = self._combo(ANCHOR_OPTIONS)
        self.signature_anchor.setCurrentIndex(self.signature_anchor.findData("bottom_center"))
        self.signature_size = self._double(3.5, 0.5, 50, 0.5, "% tamaño", 100)
        self.signature_opacity = self._double(90, 1, 100, 1, "% opacidad ID", 100)
        self.signature_margin = self._double(2, 0, 20, 0.5, "% margen", 100)
        self.signature_enabled.toggled.connect(self.update_signature_controls)
        self.signature_enabled.toggled.connect(self.invalidate_preview)
        self.signature_text.textChanged.connect(self.invalidate_preview)
        self.signature_kind.currentIndexChanged.connect(self.update_signature_controls)
        self.signature_kind.currentIndexChanged.connect(self.invalidate_preview)
        for widget in (
            self.signature_anchor,
            self.signature_size,
            self.signature_opacity,
            self.signature_margin,
        ):
            self._change_signal(widget).connect(self.invalidate_preview)
        for widget in (self.anchor, self.width_fraction, self.opacity):
            self._change_signal(widget).connect(self.save_layer_settings)
        self.repeat.toggled.connect(self.save_layer_settings)
        self.fallback = self._combo(
            (
                ("Anteponer marca y enviar a revisión", "traditional_foreground"),
                ("Copiar original sin cambios y revisar", "copy_original"),
                ("Omitir foto y registrar error", "skip_image"),
            )
        )
        for row, label, widget in (
            (0, "Modo", self.mode),
            (2, "Posición de la marca", self.anchor),
            (3, "Ancho", self.width_fraction),
            (4, "Opacidad", self.opacity),
            (5, "Calidad JPEG", self.quality),
            (6, "Si Smart requiere fallback", self.fallback),
        ):
            settings.addWidget(QLabel(label), row, 0)
            settings.addWidget(widget, row, 1)
        settings.addWidget(QLabel("Marcas principales"), 1, 0)
        settings.addWidget(self.layers_combo, 1, 1)
        settings.addWidget(self.add_layer_button, 1, 2)
        layer_actions = QHBoxLayout()
        layer_actions.addWidget(self.remove_layer_button)
        layer_actions.addWidget(self.layer_up_button)
        layer_actions.addWidget(self.layer_down_button)
        settings.addLayout(layer_actions, 1, 3)
        settings.addWidget(self.repeat, 2, 2)
        settings.addWidget(self.signature_enabled, 0, 4, 1, 3)
        settings.addWidget(QLabel("Tipo de identificación"), 1, 4)
        settings.addWidget(self.signature_kind, 1, 5, 1, 2)
        settings.addWidget(self.signature_text, 2, 4, 1, 3)
        settings.addWidget(self.signature_asset_label, 3, 4)
        settings.addWidget(self.signature_asset_button, 3, 5, 1, 2)
        settings.addWidget(QLabel("Posición ID"), 4, 4)
        settings.addWidget(self.signature_anchor, 4, 5, 1, 2)
        settings.addWidget(QLabel("Tamaño ID"), 5, 4)
        settings.addWidget(self.signature_size, 5, 5, 1, 2)
        settings.addWidget(QLabel("Opacidad / margen"), 6, 4)
        settings.addWidget(self.signature_opacity, 6, 5)
        settings.addWidget(self.signature_margin, 6, 6)
        self.mode.currentIndexChanged.connect(self.update_controls)
        layout.addLayout(settings)

        presets = QHBoxLayout()
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(220)
        self.refresh_presets_button = QPushButton("Actualizar presets")
        self.save_preset_button = QPushButton("Guardar preset…")
        self.load_preset_button = QPushButton("Cargar preset")
        self.refresh_presets_button.clicked.connect(self.refresh_presets)
        self.save_preset_button.clicked.connect(self.save_preset)
        self.load_preset_button.clicked.connect(self.load_preset)
        presets.addWidget(QLabel("Preset local"))
        presets.addWidget(self.preset_combo, 1)
        presets.addWidget(self.refresh_presets_button)
        presets.addWidget(self.save_preset_button)
        presets.addWidget(self.load_preset_button)
        layout.addLayout(presets)

        actions = QHBoxLayout()
        self.preview_button = QPushButton("Previsualizar primera foto")
        self.run_button = QPushButton("Aplicar a la carpeta")
        self.run_button.setObjectName("primary")
        self.cancel_button = QPushButton("Cancelar")
        self.open_button = QPushButton("Abrir último resultado")
        self.preview_button.clicked.connect(self.start_preview)
        self.run_button.clicked.connect(self.start_run)
        self.cancel_button.clicked.connect(self.cancel_work)
        self.open_button.clicked.connect(self.open_results)
        actions.addWidget(self.preview_button)
        actions.addWidget(self.run_button)
        actions.addWidget(self.cancel_button)
        actions.addStretch()
        actions.addWidget(self.open_button)
        layout.addLayout(actions)

        preview_row = QHBoxLayout()
        self.before_view = PhotoView()
        self.after_view = PhotoView()
        for title, view in (("Original", self.before_view), ("Vista previa", self.after_view)):
            column = QVBoxLayout()
            caption = QLabel(title)
            caption.setObjectName("muted")
            column.addWidget(caption)
            column.addWidget(view, 1)
            preview_row.addLayout(column, 1)
        layout.addLayout(preview_row, 1)

        self.result_list = QListWidget()
        self.result_list.setMaximumHeight(115)
        layout.addWidget(self.result_list)
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        footer = QHBoxLayout()
        self.status = QLabel(
            "Elige una carpeta y un PNG. La pestaña Encuadre mantiene su estado separado."
        )
        self.status.setWordWrap(True)
        self.elapsed = QLabel("")
        footer.addWidget(self.status, 1)
        footer.addWidget(self.elapsed)
        layout.addLayout(footer)
        self.source_edit.editingFinished.connect(self.update_file_count)
        self.output_edit.editingFinished.connect(self.update_file_count)
        self.recursive.toggled.connect(self.on_recursive)
        self.refresh_presets()
        self.update_controls()
        self.update_signature_controls()
        self.update_layer_controls()

    @staticmethod
    def _combo(options):
        value = QComboBox()
        for label, data in options:
            value.addItem(label, data)
        return value

    @staticmethod
    def _double(value, low, high, step, suffix, scale):
        spin = QDoubleSpinBox()
        spin.setRange(low, high)
        spin.setSingleStep(step)
        spin.setValue(value)
        spin.setSuffix(" " + suffix)
        spin.setDecimals(0 if scale == 100 else 2)
        spin.setProperty("fraction_scale", scale)
        return spin

    @staticmethod
    def _change_signal(widget):
        return widget.currentIndexChanged if isinstance(widget, QComboBox) else widget.valueChanged

    def set_source(self, path):
        path = Path(path)
        self.source_edit.setText(str(path))
        default_output = (
            path.parent / "Picframe_Output"
            if self.recursive.isChecked()
            else path / "exportaciones"
        )
        self.output_edit.setText(str(default_output))
        self.update_file_count()

    def pick_source(self):
        path = QFileDialog.getExistingDirectory(self, "Elegir fotografías", self.source_edit.text())
        if path:
            self.set_source(path)

    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, "Elegir destino", self.output_edit.text())
        if path:
            self.output_edit.setText(path)
            self.update_file_count()

    def pick_assets(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Elegir marcas PNG", "", "PNG (*.png)")
        if paths:
            self.set_layers(
                (*self.selected_assets, *(Path(path) for path in paths)),
                (*self.layer_settings, *(self._default_layer_settings() for _ in paths)),
            )

    @staticmethod
    def _default_layer_settings():
        return {
            "width_fraction": 0.65,
            "opacity": 0.30,
            "anchor": "center",
            "repeat": False,
        }

    def set_layers(self, paths, settings=None):
        self.selected_assets = [Path(path) for path in paths]
        self.layer_settings = [
            dict(item) for item in (settings or [self._default_layer_settings() for _ in paths])
        ]
        self._loading_layer_settings = True
        self.layers_combo.blockSignals(True)
        self.layers_combo.clear()
        for path in self.selected_assets:
            self.layers_combo.addItem(path.name)
        self.layers_combo.setCurrentIndex(0 if self.selected_assets else -1)
        self.layers_combo.blockSignals(False)
        self._loading_layer_settings = False
        self.load_layer_settings(self.layers_combo.currentIndex())
        self.update_layer_controls()
        self.update_controls()
        self.invalidate_preview()

    def load_layer_settings(self, index):
        if self._loading_layer_settings:
            return
        self._loading_layer_settings = True
        if 0 <= index < len(self.layer_settings):
            values = self.layer_settings[index]
        else:
            values = self._default_layer_settings()
        self.width_fraction.setValue(values["width_fraction"] * 100)
        self.opacity.setValue(values["opacity"] * 100)
        self.anchor.setCurrentIndex(self.anchor.findData(values["anchor"]))
        self.repeat.setChecked(values["repeat"])
        self._loading_layer_settings = False
        self.update_layer_controls()

    def save_layer_settings(self, *unused):
        if self._loading_layer_settings:
            return
        index = self.layers_combo.currentIndex()
        if index < 0 or index >= len(self.layer_settings):
            return
        self.layer_settings[index] = {
            "width_fraction": self.width_fraction.value() / 100,
            "opacity": self.opacity.value() / 100,
            "anchor": self.anchor.currentData(),
            "repeat": self.repeat.isChecked(),
        }
        self.invalidate_preview()

    def update_layer_controls(self):
        busy = self.worker is not None
        index = self.layers_combo.currentIndex()
        selected = index >= 0
        smart = self.mode.currentData() == "smart"
        self.layers_combo.setEnabled(not busy)
        self.remove_layer_button.setEnabled(selected and not busy)
        self.layer_up_button.setEnabled(selected and index > 0 and not busy)
        self.layer_down_button.setEnabled(
            selected and index < len(self.selected_assets) - 1 and not busy
        )
        for widget in (self.width_fraction, self.opacity, self.anchor):
            widget.setEnabled(selected and not busy)
        self.repeat.setEnabled(selected and not smart and not busy)

    def remove_layer(self):
        index = self.layers_combo.currentIndex()
        if index < 0:
            return
        paths = self.selected_assets.copy()
        settings = self.layer_settings.copy()
        paths.pop(index)
        settings.pop(index)
        self.set_layers(paths, settings)

    def move_layer(self, delta):
        index = self.layers_combo.currentIndex()
        target = index + delta
        if not 0 <= target < len(self.selected_assets):
            return
        paths = self.selected_assets.copy()
        settings = self.layer_settings.copy()
        paths[index], paths[target] = paths[target], paths[index]
        settings[index], settings[target] = settings[target], settings[index]
        self.set_layers(paths, settings)
        self.layers_combo.setCurrentIndex(target)

    def pick_signature_asset(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Elegir PNG de identificación", "", "PNG (*.png)"
        )
        if path:
            self.signature_asset = Path(path)
            self.signature_asset_label.setText(self.signature_asset.name)
            self.invalidate_preview()

    def on_recursive(self):
        source = self.source_edit.text()
        if source:
            current = Path(self.output_edit.text()) if self.output_edit.text() else None
            old = Path(source) / "exportaciones"
            if current == old:
                self.output_edit.setText(str(Path(source).parent / "Picframe_Output"))
            self.update_file_count()

    def update_file_count(self):
        try:
            inventory = discover(
                Path(self.source_edit.text()),
                Path(self.output_edit.text()) if self.output_edit.text() else None,
                recursive=self.recursive.isChecked(),
            )
            self.file_count.setText(f"{len(inventory.images)} fotos JPG/JPEG")
        except (ValueError, OSError) as exc:
            self.file_count.setText(str(exc))

    def build_config(self):
        if not self.selected_assets:
            raise ValueError("Selecciona al menos un PNG para la marca principal")
        mode = self.mode.currentData()
        if mode == "smart" and len(self.selected_assets) != 1:
            raise ValueError("Smart usa un solo PNG principal; elige una marca")
        layers = tuple(
            WatermarkLayer(
                path,
                width_fraction=settings["width_fraction"],
                opacity=settings["opacity"],
                anchor=settings["anchor"],
                repeat=settings["repeat"],
            )
            for path, settings in zip(self.selected_assets, self.layer_settings, strict=True)
        )
        signature_kind = self.signature_kind.currentData()
        signature = SignatureConfig(
            enabled=self.signature_enabled.isChecked(),
            kind=signature_kind,
            text=self.signature_text.text() if signature_kind == "text" else "",
            asset_path=self.signature_asset if signature_kind == "png" else None,
            size_fraction=self.signature_size.value() / 100,
            opacity=self.signature_opacity.value() / 100,
            anchor=self.signature_anchor.currentData(),
            margin_fraction=self.signature_margin.value() / 100,
        )
        return WatermarkConfig(
            mode=mode,
            layers=layers,
            signature=signature,
            quality=self.quality.value(),
            fallback_policy=self.fallback.currentData(),
            recursive=self.recursive.isChecked(),
        )

    def update_controls(self, *unused):
        busy = self.worker is not None
        smart = self.mode.currentData() == "smart"
        self.fallback.setEnabled(smart and not busy)
        for widget in (
            self.source_edit,
            self.output_edit,
            self.folder_name_edit,
            self.recursive,
            self.mode,
            self.quality,
            self.signature_enabled,
            self.preset_combo,
            self.add_layer_button,
            self.refresh_presets_button,
            self.save_preset_button,
            self.load_preset_button,
            self.signature_anchor,
            self.signature_size,
            self.signature_opacity,
            self.signature_margin,
        ):
            widget.setEnabled(not busy)
        self.preview_button.setEnabled(not busy and bool(self.source_edit.text()))
        self.run_button.setEnabled(
            not busy and bool(self.source_edit.text()) and bool(self.selected_assets)
        )
        self.cancel_button.setEnabled(busy and not self.worker.cancel.is_set() if busy else False)
        self.open_button.setEnabled(self.last_result is not None)
        self.update_layer_controls()
        self.update_signature_controls()

    def update_signature_controls(self, *unused):
        enabled = self.signature_enabled.isChecked()
        is_text = self.signature_kind.currentData() == "text"
        available = self.worker is None
        self.signature_kind.setEnabled(available)
        self.signature_text.setEnabled(enabled and is_text and available)
        self.signature_asset_button.setEnabled(enabled and not is_text and available)
        for widget in (
            self.signature_anchor,
            self.signature_size,
            self.signature_opacity,
            self.signature_margin,
        ):
            widget.setEnabled(enabled and available)
        self.signature_asset_label.setVisible(not is_text)
        self.signature_asset_button.setVisible(not is_text)

    def _launch(self, function, on_result):
        worker = TaskWorker(function, self)
        self.worker = worker
        self.threads.append(worker)
        worker.progress.connect(self.on_progress)
        worker.result.connect(on_result)
        worker.failed.connect(self.on_failed)
        worker.finished.connect(lambda: self.worker_finished(worker))
        self.started = monotonic()
        self.progress_bar.setRange(0, 0)
        self.status.setText("Procesando localmente…")
        self.update_controls()
        worker.start()

    def start_preview(self):
        try:
            config = self.build_config()
            inventory = discover(
                Path(self.source_edit.text()),
                Path(self.output_edit.text()) if self.output_edit.text() else None,
                recursive=config.recursive,
            )
            if not inventory.images:
                raise ValueError("No hay fotografías JPG/JPEG en la carpeta")
            item = inventory.images[0]
        except Exception as exc:
            self.on_failed(str(exc))
            return

        def task(progress, record, cancel):
            from raceframe.core.watermark_render import WatermarkRenderer

            with load_image(inventory.root, item) as loaded, WatermarkRenderer(config) as renderer:
                status = "traditional"
                if config.mode == "smart":
                    try:
                        from raceframe.watermark.vision import VisionPersonSegmenter

                        mask = VisionPersonSegmenter().segment(loaded.image)
                        status = mask.status
                        if mask.status in {"ok", "empty"}:
                            after = renderer.render(loaded.image, mask.mask)
                        else:
                            status = "fallback: " + (mask.reason or mask.status)
                            after = self._preview_fallback(renderer, loaded.image, config)
                    except Exception as exc:
                        status = f"fallback: {type(exc).__name__}"
                        after = self._preview_fallback(renderer, loaded.image, config)
                else:
                    after = renderer.render(loaded.image)
                try:
                    return {
                        "width": loaded.image.width,
                        "height": loaded.image.height,
                        "before": loaded.image.tobytes(),
                        "after": after.tobytes(),
                        "status": status,
                        "name": item.relative_path,
                    }
                finally:
                    after.close()

        self._launch(task, self.preview_done)

    @staticmethod
    def _preview_fallback(renderer, image, config):
        if config.fallback_policy == "traditional_foreground":
            return renderer.render(image, None)
        if config.fallback_policy == "copy_original":
            return image.copy()
        return image.copy()

    def preview_done(self, result):
        width, height = result["width"], result["height"]
        before = QImage(
            result["before"], width, height, width * 3, QImage.Format.Format_RGB888
        ).copy()
        after = QImage(
            result["after"], width, height, width * 3, QImage.Format.Format_RGB888
        ).copy()
        self.before_view.show_image(before, (width, height))
        self.after_view.show_image(after, (width, height))
        self.status.setText(f"Vista previa: {result['name']} · {result['status']}")

    def start_run(self):
        try:
            config = self.build_config()
            job_name = validate_job_name(self.folder_name_edit.text())
            source = Path(self.source_edit.text())
            output = Path(self.output_edit.text()) if self.output_edit.text() else None
            inventory = discover(source, output, recursive=config.recursive)
            if not inventory.images:
                raise ValueError("No hay fotografías JPG/JPEG para procesar")
            from raceframe.export.metadata import tool_path

            tool_path()
        except Exception as exc:
            self.on_failed(str(exc))
            return
        self.result_list.clear()
        self._launch(
            lambda progress, record, cancel: process_watermark_folder(
                source,
                output,
                config=config,
                progress=progress,
                cancel=cancel,
                job_name=job_name,
            ),
            self.run_done,
        )

    def run_done(self, result):
        self.last_result = result
        self.result_list.clear()
        for row in result["images"]:
            watermark = row.get("watermark", {})
            state = (
                "Error"
                if row.get("error")
                else (
                    "Para revisar" if watermark.get("review_required") else row["operation_status"]
                )
            )
            item = QListWidgetItem(f"{row['input_relative_path']} · {state}")
            item.setData(Qt.ItemDataRole.UserRole, row["image_id"])
            if watermark.get("review_required"):
                item.setForeground(QColor("#edb965"))
            self.result_list.addItem(item)
        summary = result["summary"]
        self.status.setText(
            f"{result['status']} · {summary['exported']} exportadas · "
            f"{summary['review_required']} para revisar · {summary['errors']} errores · "
            f"{summary['elapsed_seconds']:.1f} s"
        )
        self.update_controls()

    def on_progress(self, n, total):
        self.progress_bar.setRange(0, max(1, total))
        self.progress_bar.setValue(n)
        self.status.setText(f"Procesando fotografía {n} de {total}…")

    def on_failed(self, message):
        self.status.setText("No se completó la operación: " + message)

    def worker_finished(self, worker):
        worker.wait()
        self.worker = None
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        self.update_controls()
        self.threads.remove(worker)
        worker.deleteLater()
        if self.started is not None:
            self.elapsed.setText(f"{monotonic() - self.started:.1f} s")
        if self.close_when_finished:
            self._closing_main_window = True
            self.window().close()

    def cancel_work(self):
        if self.worker is not None:
            self.worker.cancel.set()
            self.status.setText("Cancelando al terminar la fotografía activa…")
            self.update_controls()

    def open_results(self):
        if self.last_result:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(Path(self.last_result["manifest_path"]).parent))
            )

    def refresh_presets(self):
        self.preset_combo.clear()
        try:
            for name in self._preset_store().names():
                self.preset_combo.addItem(name, name)
        except Exception as exc:
            self.status.setText("No se pudieron leer los presets locales: " + str(exc))

    def save_preset(self):
        try:
            config = self.build_config()
        except Exception as exc:
            self.on_failed(str(exc))
            return
        name, accepted = QInputDialog.getText(self, "Guardar preset", "Nombre del preset")
        if not accepted:
            return
        try:
            self._preset_store().save(name, config)
            self.refresh_presets()
            self.status.setText(f"Preset local guardado: {name}")
        except Exception as exc:
            QMessageBox.warning(self, "No se guardó el preset", str(exc))

    def load_preset(self):
        name = self.preset_combo.currentData()
        if not name:
            return
        try:
            _, config = self._preset_store().load(name)
            self.mode.setCurrentIndex(self.mode.findData(config.mode))
            self.set_layers(
                [layer.asset_path for layer in config.layers],
                [
                    {
                        "width_fraction": layer.width_fraction,
                        "opacity": layer.opacity,
                        "anchor": layer.anchor,
                        "repeat": layer.repeat,
                    }
                    for layer in config.layers
                ],
            )
            self.quality.setValue(config.quality)
            self.fallback.setCurrentIndex(self.fallback.findData(config.fallback_policy))
            self.signature_enabled.setChecked(config.signature.enabled)
            self.signature_kind.setCurrentIndex(self.signature_kind.findData(config.signature.kind))
            self.signature_text.setText(config.signature.text)
            self.signature_asset = config.signature.asset_path
            self.signature_anchor.setCurrentIndex(
                self.signature_anchor.findData(config.signature.anchor)
            )
            self.signature_size.setValue(config.signature.size_fraction * 100)
            self.signature_opacity.setValue(config.signature.opacity * 100)
            self.signature_margin.setValue(config.signature.margin_fraction * 100)
            self.signature_asset_label.setText(
                self.signature_asset.name if self.signature_asset else "Sin PNG de identificación"
            )
            self.update_signature_controls()
            self.invalidate_preview()
            self.status.setText(f"Preset cargado: {name}")
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo cargar el preset", str(exc))

    def _preset_store(self):
        if self.preset_store_factory is not None:
            return self.preset_store_factory()
        from raceframe.watermark.presets import WatermarkPresetStore

        return WatermarkPresetStore()

    def invalidate_preview(self, *unused):
        self.before_view.clear_image()
        self.after_view.clear_image()

    def closeEvent(self, event):
        if self.worker is not None and not self._closing_main_window:
            self.close_when_finished = True
            self.cancel_work()
            event.ignore()
            return
        event.accept()
