# Validación prevista de escritorio

Instalar extras gui/detector/build y pytest-qt. Ejecutar pruebas offscreen más regresión CLI.
Abrir ventana con detector simulado y fotos sintéticas, verificar navegación/overlays/selección,
ROI válido e inválido, cambios de Config que invalidan análisis, cancelación y cierre durante tarea.

Después abrir app en macOS, elegir carpeta de prueba local, analizar, revisar y exportar;
comprobar metadatos, firmas y que no se repite inferencia en la exportación revisada.
Construir dist/Raceframe.app con scripts/build_macos.py, abrir con Finder y ejecutar smoke offline.
No publicar fotos, resultados privados, bundle, modelos ni herramientas en Git.
Una apertura local no equivale a firma Developer ID ni notarización para otros equipos.
