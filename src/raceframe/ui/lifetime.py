"""Recolección de ciclos en el hilo GUI; CLI conserva la política normal de Python."""

import gc

from PySide6.QtCore import QObject, QThread, QTimer, Slot
from PySide6.QtWidgets import QApplication


class GuiCollection(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.collect)
        app.aboutToQuit.connect(self.restore)
        self.was_enabled = False
        self.start()

    def start(self):
        if not self.timer.isActive():
            self.was_enabled = gc.isenabled()
            gc.disable()
            self.timer.start()

    @Slot()
    def collect(self):
        # La recolección automática puede correr en el worker que asigna memoria.
        # Las envolturas Qt con ciclos deben destruirse desde el hilo de la interfaz.
        if QThread.currentThread() != self.thread():
            raise RuntimeError("La limpieza de interfaz debe ejecutarse en el hilo GUI")
        gc.collect()

    @Slot()
    def restore(self):
        self.timer.stop()
        if self.was_enabled:
            gc.enable()


def ensure_gui_collection():
    app = QApplication.instance()
    if app is None or QThread.currentThread() != app.thread():
        raise RuntimeError("Se requiere QApplication en el hilo GUI")
    manager = getattr(app, "_picframe_collection", None)
    if manager is None:
        manager = GuiCollection(app)
        app._picframe_collection = manager
    else:
        manager.start()
    return manager
