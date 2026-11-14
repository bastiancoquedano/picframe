# Research — Smart Watermark para Picframe

Investigación de lectura para planificación, sin instalaciones, descargas de pesos ni fotografías.

- Apple Vision: `VNGeneratePersonSegmentationRequest` existe en macOS 12+, entrega una máscara de
  persona vía `VNPixelBufferObservation`; Apple documenta `fast`, `balanced`, `accurate` y el uso de
  máscara para blend. Elegida `accurate` para fotografía fija; como el logo usa unión de personas, la
  segmentación semántica basta para la primera versión. Un solo mapa final y `autorelease_pool` por foto.
  Fuentes: [Apple request](https://developer.apple.com/documentation/vision/vngeneratepersonsegmentationrequest),
  [guía matte](https://developer.apple.com/documentation/vision/applying-matte-effects-to-people-and-images-and-video),
  [qualityLevel](https://developer.apple.com/documentation/vision/vngeneratepersonsegmentationrequest/qualitylevel-swift.enum).
- PyObjC: `pyobjc-framework-Vision==13.0` (30-10-2026), Python>=3.11, wheel universal2 arm64/x86_64,
  MIT. Necesita pyobjc-core, Cocoa, Quartz/CoreML. Se agregó como extra opcional Darwin y quedó instalado
  para el build local. La integración PyInstaller aún requiere smoke congelado; T002 es el gate restante.
  Autorelease pool por archivo.
  Fuentes: [PyPI official](https://pypi.org/project/pyobjc-framework-Vision/13.0/),
  [setup/dependencies](https://github.com/ronaldoussoren/pyobjc/blob/main/pyobjc-framework-Vision/setup.py),
  [hilos](https://pyobjc.readthedocs.io/en/latest/core/intro.html#working-with-threads),
  [instalación](https://pyobjc.readthedocs.io/en/latest/install.html).
- Alternativa condicionada: Ultralytics 8.4.197 local incluye YOLO11-seg architecture y `SegmentationPredictor`;
  modelo es `yolo11n-seg.pt` independiente. Puede devolver máscaras por instancia y unirlas en uint8 para
  no apilar N×W×H. `retina_masks=True` devuelve dimensiones originales pero consume más RAM. URL de assets
  prevista v8.4.0 no confirmada; nunca auto-download. AGPL/Enterprise de Ultralytics requiere una revisión
  explícita antes de distribuir. Fuentes: [YOLO11](https://docs.ultralytics.com/models/yolo11/),
  [predict y masks](https://docs.ultralytics.com/modes/predict/),
  [predictor segment](https://docs.ultralytics.com/reference/models/yolo/segment/predict/),
  [licencia](https://www.ultralytics.com/license).
- Detalle de implementación: foto orientada `ImageOps.exif_transpose` ya existe; pasar orientación `.up`.
  PixelBuffer puede diferir en ancho y alto del origen: escalar cada eje. Render = overlay RGBA cuyo alfa
  se multiplica por `1-mask`; en núcleo de máscara opaca, original RGB permanece idéntico. Dilatar 1–2 px
  si pruebas de borde muestran filtración. Firma se dibuja luego y queda excluida de aserción de igualdad.
- Exportador: JPEG Pillow + `preserve_metadata` ExifTool existente; verificación strict APP/MakerNotes/MPF/
  IPTC/XMP/ICC, dimensiones full-frame, ориentation=1, miniatura actualizada, atomic temp/hardlink/Journal.
  Reusar ruta pero añadir `export_rendered_jpeg` para no forzar `CompositionStatus.CROPPED`.
- Escala: una foto RGB, una máscara union y un JPEG temporal a la vez. Arrancar secuencial y medir; no usar
  paralelismo especulativo de 1k–5k.

**Evidencia de gates**: Mac local macOS 26.6.2 arm64, Python 3.11, PySide6 Essentials 6.12.0/PyInstaller 6.22.3.
La llamada Vision sintética se ejecutó en T001; T002 confirmó el bundle congelado offline.

## Smoke local PyObjC 13.0 — macOS 26.6.2 arm64 (2026-11-12)

- Instalé el extra Vision opcional ya evaluado en el uv env, no en runtime de fotos.
- Importé Vision/Quartz/objc; construí una imagen sintética, ejecuté `VNGeneratePersonSegmentationRequest`
  `.accurate`, obtuve `VNPixelBufferObservation` y PixelBuffer L008. Request API funciona en Python 3.11.
- PyObjC accede a CVPixelBuffer con `observation.pixelBuffer()` (selector, se invoca), no la propiedad sin
  llamada. `CVPixelBufferLockBaseAddress` retorna 0; `GetBaseAddress` es `objc.varlist`, se copia con
  `base.as_buffer(bytesPerRow * height)` antes de unlock. Validar status/format/strides y liberar usando
  las mismas flags. Una primera prueba usando el selector como propiedad produjo puntero NULL; no leerlo.
- La máscara solicitada mide 2016×1512 aun con un CGImage input 128×128; escalar explícitamente X/Y al
  raster orientado está confirmado como requisito, nunca suponer dimensiones idénticas.
- La silueta geométrica artificial produjo máscara de baja confianza (máx 34/255). El clasificador no
  detectó una persona sintética confiable: esto es correcto tratar como máscara vacía/fallback, no como
  precisión de persona. Sensibilidad de personas reales requiere prueba visual posterior.
- Apple documenta que la segmentación semántica entrega máscara union para grupos numerosos; su sample
  usa máscaras por instancia hasta cuatro y máscara union con más de cuatro. El logo único solo requiere
  la union. Fuente oficial adicional: [Apple: múltiples personas](https://developer.apple.com/documentation/vision/segmenting-and-colorizing-individuals-from-a-surrounding-scene).

## Resultado del gate T001 — 2026-11-12

- El extra fijado instaló PyObjC Vision 13.0 en el entorno macOS arm64 y `Vision`, `Quartz` y `objc`
  importan. La prueba ejecutó `VNGeneratePersonSegmentationRequest` `.accurate`, seleccionó el dispositivo
  CPU ofrecido por `supportedComputeStageDevicesAndReturnError`, recibió L008, copió el CVPixelBuffer y
  escaló X/Y al lienzo. La prueba también valida stride, ownership, lock/unlock y formato con PixelBuffer fake.
- La comprobación de la API con el sandbox restringido falló porque macOS no pudo leer/crear su plan de
  inferencia. La misma prueba sintética, ejecutada con acceso normal al runtime de macOS, pasó. Esto fue
  una limitación del sandbox de prueba, no un envío de datos o un fallo del binding.
- El diagnóstico `vision_spike.py` sobre una figura geométrica sintética dio `status=error`, razón
  `low_confidence_mask`, cero píxeles por encima de 128, backend Apple Vision 26.6.2 y solicitud/revisión
  1. Es el fallback correcto: la silueta no imita un corredor y no demuestra precisión en fotos reales.
- El adaptador fija CPU solo si Vision reporta ese dispositivo como soportado. La prueba de máscara real
  es sintética; no existe aún evaluación visual de personas reales.

## Resultado del gate T002 — 2026-11-12

- `Picframe.app` 0.4.0 se construyó en arm64 con PyInstaller 6.22.3 e incluye los módulos Vision, Quartz,
  objc y sus metadatos. El script de build comprueba que Vision esté instalado y verifica los recursos.
- El smoke del bundle bajo `sandbox-exec` con toda red denegada confirmó QTabWidget/WatermarkPage,
  import de Vision, inference CPU del detector y exportación de JPEG. Una solicitud Vision sobre la figura
  sintética no obtuvo confianza; `copy_original` dejó bytes idénticos y registró `review_required`.
- `codesign --verify --deep --strict` pasó. Firma ad hoc local; no Developer ID/notarización.

## Incidencia del primer lote real — 2026-11-14

- El propietario ejecutó Smart en diez JPEG. Todos los registros indicaron
  `ValueError: NSInvalidArgumentException - key does not exist`, con fallback Traditional y revisión.
- Reproduje el error con una imagen sintética. La excepción ocurría al crear
  `VNImageRequestHandler.initWithCGImage_options_` pasando `{}`; el mismo initializer funciona pasando
  `None`. Cambié el adaptador para dejar las opciones sin configurar. El test local real de Vision
  vuelve a pasar; el bundle 0.4.1 bajo `deny network*` informa `low_confidence_mask` para la figura, no la
  excepción de inicialización. CI para este parche queda pendiente.
