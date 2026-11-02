"""Arranque de la ventana de escritorio."""

import sys

from PySide6.QtWidgets import QApplication

from raceframe import __version__
from raceframe.ui.window import MainWindow


def main():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Picframe")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
