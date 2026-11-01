"""Imagen reducida con coordenadas de escena en píxeles originales."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPen, QPixmap, QTransform
from PySide6.QtWidgets import QGraphicsItem, QGraphicsScene, QGraphicsView

from raceframe.core.models import Box
from raceframe.ui.decisions import aspect_box


class PhotoView(QGraphicsView):
    person_clicked = Signal(int)
    crop_drawn = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.original_size = None
        self.detections = []
        self.editing = False
        self.ratio = 1
        self.drag_start = None
        self.drag_item = None
        self.setMinimumSize(180, 180)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def show_image(self, image, size, row=None):
        self.scene().clear()
        self.drag_item = None
        self.drag_start = None
        self.original_size = tuple(size)
        width, height = size
        pixmap = self.scene().addPixmap(QPixmap.fromImage(image))
        pixmap.setTransform(QTransform.fromScale(width / image.width(), height / image.height()))
        self.scene().setSceneRect(0, 0, width, height)
        self.detections = [] if row is None else row.get("detections", [])
        for detection in self.detections:
            box = Box(**detection["box"])
            if not box.valid:
                continue
            color = (
                "#80d4b7"
                if detection["detection_id"] == row.get("selected_detection_id")
                else "#edb965"
            )
            pen = QPen(QColor(color), 2)
            pen.setCosmetic(True)
            self.scene().addRect(box.x1, box.y1, box.width, box.height, pen)
            label = self.scene().addSimpleText(f"Persona {detection['detection_id'] + 1}")
            label.setBrush(QColor(color))
            label.setPos(box.x1, box.y1)
            label.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations)
        if row and row.get("crop_xyxy"):
            x1, y1, x2, y2 = row["crop_xyxy"]
            pen = QPen(QColor("#80d4b7"), 3)
            pen.setCosmetic(True)
            self.scene().addRect(x1, y1, x2 - x1, y2 - y1, pen)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def clear_image(self):
        self.scene().clear()
        self.original_size = None
        self.detections = []

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_size:
            self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton or not self.original_size:
            return super().mousePressEvent(event)
        point = self.mapToScene(event.position().toPoint())
        if self.editing:
            self.drag_start = (point.x(), point.y())
            event.accept()
            return
        candidates = [
            d
            for d in self.detections
            if d["box"]["x1"] <= point.x() <= d["box"]["x2"]
            and d["box"]["y1"] <= point.y() <= d["box"]["y2"]
        ]
        if candidates:
            candidate = min(candidates, key=lambda d: Box(**d["box"]).area)
            self.person_clicked.emit(candidate["detection_id"])
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag_start is None:
            return super().mouseMoveEvent(event)
        point = self.mapToScene(event.position().toPoint())
        box = aspect_box(self.drag_start, (point.x(), point.y()), self.original_size, self.ratio)
        if self.drag_item is not None:
            self.scene().removeItem(self.drag_item)
        pen = QPen(QColor("#b3e7ff"), 3)
        pen.setCosmetic(True)
        self.drag_item = self.scene().addRect(box.x1, box.y1, box.width, box.height, pen)
        event.accept()

    def mouseReleaseEvent(self, event):
        if self.drag_start is None:
            return super().mouseReleaseEvent(event)
        point = self.mapToScene(event.position().toPoint())
        box = aspect_box(self.drag_start, (point.x(), point.y()), self.original_size, self.ratio)
        self.drag_start = None
        if self.drag_item is not None:
            self.scene().removeItem(self.drag_item)
            self.drag_item = None
        self.crop_drawn.emit(box)
        event.accept()
