"""Ventana de revisión y exportación local de Raceframe."""

from copy import deepcopy
from pathlib import Path
from time import monotonic

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QImage
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from raceframe import __version__
from raceframe.config import Config
from raceframe.core.processing import process_folder
from raceframe.imaging.discovery import discover
from raceframe.imaging.loader import load_image
from raceframe.ui.decisions import manual_crop, select_detection
from raceframe.ui.preview import PhotoView
from raceframe.ui.resources import model_path
from raceframe.ui.workers import TaskWorker, analyze_folder

STYLE = """
QWidget { background: #111820;
    color: #e9eff5;
    font-size: 12px;
    }
QMainWindow { background: #111820;
    }
QLabel#brand { font-size: 26px;
    font-weight: 700;
    }
QLabel#muted { color: #9baebf;
    }
QGroupBox { border: 1px solid #2a3948;
    border-radius: 8px;
    margin-top: 9px;
    padding: 12px 8px 5px;
    }
QGroupBox::title { subcontrol-origin: margin;
    left: 12px;
    color: #a9bfce;
    }
QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox { background: #1b2632;
    border: 1px solid #354657;
    border-radius: 5px;
    padding: 6px;
    }
QComboBox QAbstractItemView { background: #1b2632;
    color: #e9eff5;
    selection-background-color: #35566b;
    }
QPushButton { background: #263747;
    border: 1px solid #354a5d;
    border-radius: 6px;
    padding: 8px 13px;
    }
QPushButton:hover { background: #354d60;
    }
QPushButton:disabled { color: #657585;
    background: #1a2630;
    }
QPushButton#primary { color: #0e221c;
    background: #87d7b7;
    font-weight: 700;
    }
QPushButton#primary:disabled { color: #667b73;
    background: #263c34;
    }
QPushButton:checked { border: 1px solid #87d7b7;
    }
QListWidget { background: #15202a;
    border: 1px solid #2a3948;
    border-radius: 6px;
    }
QListWidget::item { padding: 9px;
    border-bottom: 1px solid #22303d;
    }
QListWidget::item:selected { background: #2b4658;
    }
QGraphicsView { background: #090f15;
    border: 1px solid #2a3948;
    border-radius: 5px;
    }
QProgressBar { background: #1b2632;
    border: 0;
    border-radius: 4px;
    min-height: 7px;
    max-height: 7px;
    }
QProgressBar::chunk { background: #87d7b7;
    border-radius: 4px;
    }
"""


class MainWindow(QMainWindow):
    def __init__(self, *, detector_factory=None, initial_model=None):
        super().__init__()
        self.detector_factory = detector_factory
        self.detector = None
        self.detector_key = None
        self.worker = None
        self.threads = []
        self.automatic_records = {}
        self._selected_source = None
        self.records = {}
        self.output_states = {}
        self.inventory = None
        self.analysis_complete = False
        self.analysis_config = None
        self.last_result = None
        self.preview_image = None
        self.preview_id = None
        self.close_when_finished = False
        self.started = None
        self.setWindowTitle(f"Raceframe {__version__}")
        self.resize(1260, 900)
        self.setMinimumSize(980, 700)
        self.setStyleSheet(STYLE)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(11)
        header = QHBoxLayout()
        brand = QLabel("Raceframe")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        muted = QLabel(f"Encuadre deportivo · Local · v{__version__}")
        muted.setObjectName("muted")
        header.addWidget(muted)
        root.addLayout(header)
        self.paths_panel = QWidget()
        paths = QGridLayout(self.paths_panel)
        paths.setContentsMargins(0, 0, 0, 0)
        self.source_edit = QLineEdit()
        self.source_edit.setPlaceholderText("Selecciona la carpeta de fotografías")
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("Carpeta para resultados independientes")
        source_button = QPushButton("Elegir origen…")
        output_button = QPushButton("Elegir destino…")
        source_button.clicked.connect(self.pick_source)
        output_button.clicked.connect(self.pick_output)
        for i, (label, edit, button) in enumerate(
            (
                ("Origen", self.source_edit, source_button),
                ("Destino", self.output_edit, output_button),
            )
        ):
            paths.addWidget(QLabel(label), i, 0)
            paths.addWidget(edit, i, 1)
            paths.addWidget(button, i, 2)
        self.recursive = QCheckBox("Incluir subcarpetas")
        self.count_label = QLabel("Sin carpeta seleccionada")
        self.count_label.setObjectName("muted")
        paths.addWidget(self.recursive, 2, 1)
        paths.addWidget(self.count_label, 2, 2)
        root.addWidget(self.paths_panel)
        self.settings_panel = QGroupBox("Encuadre")
        settings = QVBoxLayout(self.settings_panel)
        basic = QHBoxLayout()
        self.mode = self.combo(
            [("Conservador", "conservative"), ("Equilibrado", "balanced"), ("Cerrado", "tight")]
        )
        self.aspect = self.combo([("Original", "original"), ("3:2", "3:2"), ("4:5", "4:5")])
        self.priority = self.combo([("Aire superior", "headroom"), ("Protagonismo", "occupancy")])
        self.margin = QDoubleSpinBox()
        self.margin.setRange(0, 50)
        self.margin.setValue(8)
        self.margin.setSuffix(" %")
        for label, widget in [
            ("Modo", self.mode),
            ("Proporción", self.aspect),
            ("Composición", self.priority),
            ("Margen", self.margin),
        ]:
            basic.addWidget(QLabel(label))
            basic.addWidget(widget)
        self.more_button = QPushButton("Más opciones")
        self.more_button.setCheckable(True)
        basic.addWidget(self.more_button)
        settings.addLayout(basic)
        self.advanced = QWidget()
        advanced = QGridLayout(self.advanced)
        advanced.setContentsMargins(0, 8, 0, 0)
        self.policy = self.combo([("Según focal", "focal"), ("Conservar contexto", "context")])
        self.device = self.combo([("CPU", "cpu"), ("Automático", "auto"), ("MPS", "mps")])
        self.quality = QSpinBox()
        self.quality.setRange(1, 95)
        self.quality.setValue(95)
        self.min_edge = QSpinBox()
        self.min_edge.setRange(1, 20000)
        self.min_edge.setSingleStep(100)
        self.min_edge.setValue(3000)
        self.min_edge.setSuffix(" px")
        self.focal = QDoubleSpinBox()
        self.focal.setRange(1, 2000)
        self.focal.setValue(70)
        self.focal.setSuffix(" mm")
        self.occupancy = QDoubleSpinBox()
        self.occupancy.setRange(10, 90)
        self.occupancy.setValue(75)
        self.occupancy.setSuffix(" %")
        fields = [
            ("Criterio", self.policy),
            ("Dispositivo", self.device),
            ("Calidad JPEG", self.quality),
            ("Lado largo mínimo", self.min_edge),
            ("Umbral focal", self.focal),
            ("Ocupación objetivo", self.occupancy),
        ]
        for i, (label, widget) in enumerate(fields):
            row, col = i // 3, (i % 3) * 2
            advanced.addWidget(QLabel(label), row, col)
            advanced.addWidget(widget, row, col + 1)
        self.model_edit = QLineEdit(str(initial_model or model_path()))
        model_button = QPushButton("Elegir modelo…")
        model_button.clicked.connect(self.pick_model)
        advanced.addWidget(QLabel("Modelo local"), 2, 0)
        advanced.addWidget(self.model_edit, 2, 1, 1, 4)
        advanced.addWidget(model_button, 2, 5)
        self.advanced.hide()
        self.more_button.toggled.connect(self.advanced.setVisible)
        settings.addWidget(self.advanced)
        root.addWidget(self.settings_panel)
        actions = QHBoxLayout()
        self.analyze_button = QPushButton("Analizar fotografías")
        self.analyze_button.setObjectName("primary")
        self.export_button = QPushButton("Exportar resultados")
        self.export_button.setObjectName("primary")
        self.cancel_button = QPushButton("Cancelar")
        self.results_button = QPushButton("Abrir último resultado")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.export_button.clicked.connect(self.start_export)
        self.cancel_button.clicked.connect(self.cancel_work)
        self.results_button.clicked.connect(self.open_results)
        for button in (self.analyze_button, self.export_button, self.cancel_button):
            actions.addWidget(button)
        actions.addStretch()
        actions.addWidget(self.results_button)
        root.addLayout(actions)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.photo_list = QListWidget()
        self.photo_list.setMinimumWidth(205)
        self.photo_list.setMaximumWidth(300)
        self.photo_list.currentItemChanged.connect(lambda *a: self.show_selected())
        splitter.addWidget(self.photo_list)
        preview_panel = QWidget()
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        toolbar = QHBoxLayout()
        self.person_combo = QComboBox()
        self.person_combo.setMinimumWidth(150)
        self.person_combo.activated.connect(self.person_activated)
        self.manual_button = QPushButton("Dibujar recorte")
        self.manual_button.setCheckable(True)
        self.manual_button.toggled.connect(self.toggle_manual)
        self.reset_button = QPushButton("Volver a automático")
        self.reset_button.clicked.connect(self.reset_decision)
        toolbar.addWidget(QLabel("Protagonista"))
        toolbar.addWidget(self.person_combo)
        toolbar.addStretch()
        toolbar.addWidget(self.manual_button)
        toolbar.addWidget(self.reset_button)
        preview_layout.addLayout(toolbar)
        views = QHBoxLayout()
        self.original_view = PhotoView()
        self.result_view = PhotoView()
        self.original_view.person_clicked.connect(self.choose_person)
        self.original_view.crop_drawn.connect(self.apply_manual_crop)
        for label, view in [
            ("Original · personas y recorte propuesto", self.original_view),
            ("Vista previa del resultado", self.result_view),
        ]:
            column = QVBoxLayout()
            caption = QLabel(label)
            caption.setObjectName("muted")
            column.addWidget(caption)
            column.addWidget(view, 1)
            views.addLayout(column, 1)
        preview_layout.addLayout(views, 1)
        splitter.addWidget(preview_panel)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)
        from PySide6.QtWidgets import QProgressBar

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        root.addWidget(self.progress)
        footer = QHBoxLayout()
        self.status = QLabel("Elige una carpeta para empezar. Tus originales no se modifican.")
        self.status.setWordWrap(True)
        self.elapsed_label = QLabel("")
        footer.addWidget(self.status, 1)
        footer.addWidget(self.elapsed_label)
        root.addLayout(footer)
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.update_elapsed)
        self.config_controls = [
            self.mode,
            self.aspect,
            self.priority,
            self.margin,
            self.policy,
            self.device,
            self.quality,
            self.min_edge,
            self.focal,
            self.occupancy,
        ]
        for widget in self.config_controls:
            (
                widget.currentIndexChanged if isinstance(widget, QComboBox) else widget.valueChanged
            ).connect(self.invalidate)
        self.recursive.toggled.connect(self.recursion_changed)
        self.model_edit.textChanged.connect(self.invalidate)
        self.source_edit.editingFinished.connect(self.source_edited)
        self.output_edit.textChanged.connect(self.invalidate)
        self.update_controls()

    @staticmethod
    def combo(options):
        combo = QComboBox()
        for label, value in options:
            combo.addItem(label, value)
        return combo

    def current_config(self):
        return Config(
            mode=self.mode.currentData(),
            aspect=self.aspect.currentData(),
            composition_priority=self.priority.currentData(),
            margin=self.margin.value() / 100,
            quality=self.quality.value(),
            min_long_edge=self.min_edge.value(),
            focal_threshold=self.focal.value(),
            target_occupancy=self.occupancy.value() / 100,
            framing_policy=self.policy.currentData(),
            device=self.device.currentData(),
            recursive=self.recursive.isChecked(),
        )

    def pick_source(self):
        path = QFileDialog.getExistingDirectory(self, "Elegir fotografías", self.source_edit.text())
        if path:
            self.set_source(Path(path))

    def pick_output(self):
        path = QFileDialog.getExistingDirectory(self, "Elegir destino", self.output_edit.text())
        if path:
            self.output_edit.setText(path)

    def pick_model(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Modelo local", self.model_edit.text(), "Modelo YOLO (*.pt)"
        )
        if path:
            self.model_edit.setText(path)

    def set_source(self, path):
        path = Path(path)
        self._selected_source = str(path.resolve())
        self.invalidate()
        self.source_edit.setText(str(path))
        self.output_edit.setText(
            str(
                path.parent / "Raceframe_Output"
                if self.recursive.isChecked()
                else path / "exportaciones"
            )
        )
        self.update_count()

    def source_edited(self):
        if (
            self.source_edit.text()
            and str(Path(self.source_edit.text()).resolve()) != self._selected_source
        ):
            self.set_source(Path(self.source_edit.text()))

    def recursion_changed(self):
        self.invalidate()
        if self.source_edit.text():
            self.set_source(Path(self.source_edit.text()))

    def update_count(self):
        try:
            inventory = discover(
                Path(self.source_edit.text()),
                Path(self.output_edit.text()),
                recursive=self.recursive.isChecked(),
            )
            self.count_label.setText(f"{len(inventory.images)} fotografías")
        except (ValueError, OSError) as exc:
            self.count_label.setText(str(exc))
        self.update_controls()

    def invalidate(self, *unused):
        if self.worker is not None:
            return
        self.analysis_complete = False
        self.automatic_records = {}
        self.manual_button.setChecked(False)
        self.records = {}
        self.output_states = {}
        self.inventory = None
        self.photo_list.clear()
        self.preview_image = None
        self.preview_id = None
        self.original_view.clear_image()
        self.result_view.clear_image()
        self.status.setText("Analiza la carpeta para aplicar los parámetros actuales.")
        self.update_controls()

    def update_controls(self):
        busy = self.worker is not None
        self.paths_panel.setEnabled(not busy)
        self.settings_panel.setEnabled(not busy)
        self.analyze_button.setEnabled(not busy and bool(self.source_edit.text()))
        self.export_button.setEnabled(not busy and self.analysis_complete and bool(self.records))
        self.cancel_button.setEnabled(busy and not self.worker.cancel.is_set() if busy else False)
        self.results_button.setEnabled(self.last_result is not None)
        for widget in (self.person_combo, self.manual_button, self.reset_button):
            widget.setEnabled(not busy and bool(self.records))

    def launch(self, function, callback):
        worker = TaskWorker(function, self)
        self.worker = worker
        self.threads.append(worker)
        worker.progress.connect(self.on_progress)
        worker.record.connect(self.on_record)
        worker.result.connect(callback)
        worker.failed.connect(self.on_failed)
        worker.finished.connect(lambda: self.worker_finished(worker))
        self.started = monotonic()
        self.timer.start()
        self.progress.setRange(0, 0)
        self.update_controls()
        worker.start()

    def start_analysis(self):
        if self.worker is not None:
            return
        try:
            config = self.current_config()
            source = Path(self.source_edit.text())
            output = Path(self.output_edit.text())
            inventory = discover(source, output, recursive=config.recursive)
            weights = Path(self.model_edit.text())
            if not weights.is_file():
                raise ValueError("Falta el modelo local. Elige un archivo preparado.")
        except Exception as exc:
            self.on_failed(str(exc))
            return
        self.invalidate()
        self.inventory = inventory
        self.analysis_config = config
        self.count_label.setText(f"{len(inventory.images)} fotografías")
        self.status.setText("Preparando análisis local…")
        key = (str(weights.resolve()), config.device, config.detection_confidence)
        existing = self.detector if key == self.detector_key else None

        def task(progress, record, cancel):
            from raceframe.export.metadata import tool_path

            tool_path()
            detector = existing
            if detector is None:
                factory = self.detector_factory
                if factory is None:
                    from raceframe.core.detection import YoloDetector

                    factory = YoloDetector
                detector = factory(weights, config)
            return analyze_folder(source, output, config, detector, progress, record, cancel)

        self.pending_detector_key = key
        self.launch(task, self.analysis_done)

    def analysis_done(self, value):
        self.inventory = value["inventory"]
        self.detector = value["detector"]
        self.detector_key = self.pending_detector_key
        self.analysis_complete = not value["cancelled"]
        count = len(value["records"])
        review = sum(row["selection_status"] != "selected" for row in value["records"])
        self.status.setText(
            f"{'Análisis cancelado' if value['cancelled'] else 'Análisis listo'}"
            f" · {count} fotografías · {review} para revisar"
        )
        if self.photo_list.count():
            self.photo_list.setCurrentRow(0)
            self.show_selected()
        self.update_controls()

    def start_export(self):
        if self.worker is not None or not self.analysis_complete:
            return
        source = self.inventory.root
        output = self.inventory.destination
        config = self.analysis_config
        overrides = deepcopy(self.records)
        detector = self.detector
        self.status.setText("Exportando fotografías con metadatos verificados…")
        self.launch(
            lambda progress, record, cancel: process_folder(
                source,
                output,
                detector=detector,
                config=config,
                progress=progress,
                cancel=cancel,
                analysis_overrides=overrides,
            ),
            self.export_done,
        )

    def export_done(self, result):
        self.last_result = result
        self.output_states = {row["image_id"]: row for row in result["images"]}
        for index in range(self.photo_list.count()):
            item = self.photo_list.item(index)
            row = self.output_states[item.data(Qt.ItemDataRole.UserRole)]
            item.setText(self.caption(row))
        summary = result["summary"]
        label = {
            "completed": "Exportación terminada",
            "completed_with_errors": "Exportación con errores",
            "cancelled": "Exportación cancelada",
            "failed": "Exportación detenida",
        }[result["status"]]
        self.status.setText(
            f"{label} · {summary['exported']} exportadas · {summary['cropped']} recortadas"
            f" · {summary['review_required']} para revisar · {summary['errors']} errores"
        )
        self.update_controls()

    @staticmethod
    def caption(row):
        if row.get("error"):
            state = "Error"
        elif row.get("manual_crop"):
            state = "Recorte manual"
        elif row.get("manual_selection"):
            state = "Selección manual"
        elif not row.get("composition"):
            state = "Pendiente"
        else:
            state = {
                "cropped": "Recorte propuesto",
                "unchanged": "Sin cambios",
                "review_required": "Para revisar",
            }[row["composition"]["status"]]
        if row["operation_status"] == "exported":
            state += " · Exportada"
        return row["input_relative_path"] + "\n" + state

    def on_record(self, row):
        self.automatic_records[row["image_id"]] = deepcopy(row)
        self.records[row["image_id"]] = row
        item = QListWidgetItem(self.caption(row))
        item.setData(Qt.ItemDataRole.UserRole, row["image_id"])
        if row["selection_status"] != "selected":
            item.setForeground(QColor("#edb965"))
        self.photo_list.addItem(item)

    def on_progress(self, n, total):
        self.progress.setRange(0, max(1, total))
        self.progress.setValue(n)

    def on_failed(self, message):
        self.status.setText("No se completó la operación: " + message)

    def worker_finished(self, worker):
        worker.wait()
        self.worker = None
        self.timer.stop()
        self.update_elapsed()
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.update_controls()
        self.threads.remove(worker)
        worker.deleteLater()
        if self.close_when_finished:
            self.close()

    def cancel_work(self):
        if self.worker is not None:
            self.worker.cancel.set()
            self.status.setText("Cancelando al terminar la fotografía activa…")
            self.update_controls()

    def update_elapsed(self):
        if self.started is not None:
            self.elapsed_label.setText(f"{monotonic() - self.started:.1f} s")

    def selected_id(self):
        item = self.photo_list.currentItem()
        return None if item is None else item.data(Qt.ItemDataRole.UserRole)

    def show_selected(self):
        image_id = self.selected_id()
        if image_id is None or self.inventory is None:
            return
        row = self.records.get(image_id)
        if row is None:
            return
        try:
            if self.preview_id != image_id:
                item = next(i for i in self.inventory.images if i.image_id == image_id)
                with (
                    load_image(self.inventory.root, item) as loaded,
                    loaded.image.convert("RGB") as rgb,
                ):
                    rgb.thumbnail((1200, 1200))
                    width, height = rgb.size
                    self.preview_image = QImage(
                        rgb.tobytes(), width, height, width * 3, QImage.Format.Format_RGB888
                    ).copy()
                self.preview_id = image_id
            size = row["source"]["oriented_dimensions"]
            if size is None:
                raise ValueError("La imagen no tiene un análisis válido")
            self.original_view.ratio = {"original": size[0] / size[1], "3:2": 1.5, "4:5": 0.8}[
                self.analysis_config.aspect
            ]
            self.original_view.show_image(self.preview_image, size, row)
            crop = row.get("crop_xyxy")
            if crop:
                sx = self.preview_image.width() / size[0]
                sy = self.preview_image.height() / size[1]
                x1, y1, x2, y2 = crop
                preview = self.preview_image.copy(
                    round(x1 * sx),
                    round(y1 * sy),
                    max(1, round((x2 - x1) * sx)),
                    max(1, round((y2 - y1) * sy)),
                )
                self.result_view.show_image(preview, (x2 - x1, y2 - y1))
            self.person_combo.blockSignals(True)
            self.person_combo.clear()
            self.person_combo.addItem("Seleccionar…", None)
            for detection in row["detections"]:
                if "invalid_detection" not in detection.get("reasons", []):
                    self.person_combo.addItem(
                        f"Persona {detection['detection_id'] + 1} · {detection['confidence']:.0%}",
                        detection["detection_id"],
                    )
            index = self.person_combo.findData(row.get("selected_detection_id"))
            self.person_combo.setCurrentIndex(max(0, index))
            self.person_combo.blockSignals(False)
        except Exception as exc:
            self.status.setText("No se puede previsualizar: " + str(exc))
            self.result_view.clear_image()

    def person_activated(self, index):
        person = self.person_combo.itemData(index)
        if person is not None:
            self.choose_person(person)

    def choose_person(self, detection_id):
        if self.worker is not None:
            return
        image_id = self.selected_id()
        if image_id is None:
            return
        try:
            self.records[image_id] = select_detection(
                self.records[image_id], detection_id, self.analysis_config
            )
            self.photo_list.currentItem().setText(self.caption(self.records[image_id]))
            self.show_selected()
            self.status.setText(
                "Protagonista elegido manualmente; revisa el resultado antes de exportar."
            )
        except ValueError as exc:
            self.status.setText(str(exc))

    def apply_manual_crop(self, box):
        image_id = self.selected_id()
        if image_id is None or self.worker is not None:
            return
        try:
            self.records[image_id] = manual_crop(self.records[image_id], box, self.analysis_config)
            self.photo_list.currentItem().setText(self.caption(self.records[image_id]))
            self.status.setText("Recorte manual aplicado a esta fotografía.")
        except ValueError as exc:
            self.status.setText(str(exc))
        self.show_selected()

    def toggle_manual(self, checked):
        self.original_view.editing = checked
        if checked:
            self.status.setText(
                "Arrastra sobre el original para dibujar un recorte. "
                "Se conserva proporción y región del sujeto."
            )

    def reset_decision(self):
        image_id = self.selected_id()
        if image_id is None or self.worker is not None:
            return
        if image_id in self.automatic_records:
            self.records[image_id] = deepcopy(self.automatic_records[image_id])
            self.photo_list.currentItem().setText(self.caption(self.records[image_id]))
            self.show_selected()
            self.status.setText("Propuesta automática restaurada para esta fotografía.")

    def open_results(self):
        if self.last_result:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(Path(self.last_result["manifest_path"]).parent))
            )

    def closeEvent(self, event):
        if self.worker is not None:
            self.close_when_finished = True
            self.cancel_work()
            event.ignore()
        else:
            event.accept()
