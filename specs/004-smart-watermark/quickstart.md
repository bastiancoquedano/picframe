# Validación Smart Watermark

Instalación dev en macOS:
`uv sync --locked --extra detector --extra gui --extra build --extra watermark-vision`.
La app empaquetada inicializa recursos sin red; no descarga Vision weights al analizar fotografías.

1. Tests unitarios con RGBA/opacity/position y masks fake; comprobar RGB de foreground core idéntico.
2. Tests orientation 1–8: original->EXIF upright->mask->overlay->JPEG, output dimensions/metadata estrictos.
3. Tradicional: PNG transparente único/multiple/repeat, texto/logo ID, posiciones/opacidades.
4. Smart: masks vacías, solapadas, bordes, mask resolution menor/fila stride padding, request failure.
5. Request Vision real: synthetic device scene puede dar empty; confirmar CVPixelBuffer valid/bytes/orientation;
   para calidad de segmentación, la propietaria evaluará foto local fuera de Git después.
6. Fallback a Traditional en una foto, con warning/review; otra foto del lote todavía exporta Smart;
   output de error ExifTool/JPEG nunca se publica.
7. Verificar JPEG byte hash originals, tamaños exactos, perfiles ICC, ExifTool y AMP/COM preservation.
8. Guardar/cargar presets, asset faltante y paths válidos; no guardar el contenido de fotos ni logos.
9. Lote fake de 1.000 fotos: progreso/cancel/UI, una sola imagen y mask activa, luego mac real benchmark.
10. Build PyInstaller arm64, run Picframe offline smoke con Vision, revisar firma ad hoc y reportar macOS min.
