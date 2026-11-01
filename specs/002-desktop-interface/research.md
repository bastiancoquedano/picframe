# Investigación — escritorio local

Investigación delegada por speckit-plan, con fuentes oficiales; candidatas sujetas a instalación/smoke.

- Decisión: PySide6 Essentials 6.12.0 (solo Widgets/Core/Gui necesarios), Python 3.11 existente y Qt Widgets. Reutilizar motor, Pillow, YOLO y ExifTool.
  Razón: interfaz de escritorio solicitada, sin servidor web ni nuevas APIs de procesamiento.
  Alternativas: interfaz web y reescribir el motor en Swift añaden alcance innecesario.
  Fuentes: https://pypi.org/project/PySide6/ y https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html .
- Decisión: tarea en QThread con señales, cancelación threading.Event, widgets solo hilo principal.
  Razón: quit() no detiene inferencia; cerrar solo tras finalizar/cancelar cooperativamente.
  Fuente: https://doc.qt.io/qt-6/threads-qobject.html .
- Decisión: QImage con copia de buffer RGB orientado y QGraphicsView en coordenadas originales.
  Razón: evitar errores de EXIF y memoria de buffer; una vista previa reducida, no originales en caché.
  Fuente: https://doc.qt.io/qt-6/qimage.html .
- Decisión: pytest-qt 4.5.0 y offscreen para lógica/widgets, más apertura visual real en macOS.
  Fuente: https://pytest-qt.readthedocs.io/en/latest/intro.html .
- Decisión: PyInstaller 6.22.3, onedir/windowed arm64, hooks de Qt/torch/ultralytics y pesos incluidos.
  Razón: generar .app local con recursos preparados. No declarar distribución notarizada.
  Fuentes: https://pyinstaller.org/en/stable/feature-notes.html y
  https://github.com/pyinstaller/pyinstaller-hooks-contrib/blob/master/_pyinstaller_hooks_contrib/stdhooks/hook-ultralytics.py .
- Decisión: incluir ExifTool y lib juntos y resolver ruta absoluta; /usr/bin/perl en este Mac.
  Fuente: https://exiftool.org/install.html . No depende del PATH del terminal en Finder.
- Licencias: uso personal; Qt LGPL/GPL/comercial según componentes y PyInstaller con excepción
  de distribución. Inventariar sin imponer licencia propia; no publicar dependencias ni pesos en Git.
  Fuentes: https://doc.qt.io/qtforpython-6/licenses.html y https://pyinstaller.org/en/stable/license.html .
