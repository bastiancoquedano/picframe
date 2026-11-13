# Contrato de UI, segmentador y exportación

## UI

Tab Marcas de agua separado del estado/tab Encuadre. Origen, destino, nombre, PNG principal, modo
Tradicional/Smart, capas tradicionales múltiples/repetidas, texto o PNG de identidad, preview before/after,
presets, progreso, cancel y errores. Campos default: center, primary opacity 0.30, scale 0.65 frame width,
identification off; auto ID uses bottom-center and safe margins. Configuración no se procesa hasta
validar logos, masks/Vision readiness, output, color/quality.

## Segmenter

`segment(oriented_rgb) -> MaskResult(mask uint8 H×W, status/reason, backend,version,compute_device,quality)`.
Interface puro; real Vision lazy. `VNGeneratePersonSegmentationRequestQualityLevelAccurate`, output L008.
Usar el dispositivo CPU solo si Vision lo reporta como soportado. Usar handler
`.up` porque loader ya aplicó EXIF. `request.results[0].pixelBuffer()` es método; comprobar CVPixelBuffer
width,height,format,bytesPerRow; lock/read-only, copiar líneas excluyendo padding por fila a numpy y unlock
con mismas flags, todo dentro de autorelease pool. Vision mask puede diferir de canvas; Pillow/OpenCV resize
con factores X/Y explícitos; no inferir aspect. Mask union una persona mask. Excepciones/máscaras inválidas
no llegan al renderer: el lote las normaliza a status error con contexto sin píxeles.

## Render

`render(original_rgb, config, mask?) -> PIL.Image RGB/RGBA` con igual dimensión. Traditional compone PNGs
sobre todo el marco. Smart oculta únicamente alfa de la principal en mask foreground; sustituye el
foreground por RGB original en mask core. Padding/dilation 1–2 px solamente sobre máscara y validado por
orilla; firma se dibuja última. Salida en memoria es punto de comparación antes JPEG.

## Failure fallback

UI ofrece `traditional_foreground | copy_original | skip_image`, configurable, con default aprobado
`traditional_foreground`. Vision request falla, PixelBuffer no válido, máscara desalineada/corrupta o
compositor no acepta: aplicar política elegida, registrar `segmentation_fallback`, causa y revisar.
Traditional dibuja las marcas por delante; copy_original publica bytes idénticos con warning/review;
skip_image registra omitted/error, sin JPEG. En todos los casos continúa el lote. Máscara vacía válida
significa sin persona; Smart muestra PNG principal sin oclusión y no la considera error. Falla PNG/JPEG/
ExifTool: error por imagen y no publica archivo; solo error fatal de disco detiene lote.

## Export/manifest

`export_rendered_jpeg` recibe RGB full-frame igual a oriented source, escribe JPEG al temp de destino,
llama a `preserve_metadata` con el origen RO y render, crea miniatura y actualiza dimensiones/orientación,
verifica todos los demás metadata y bloques APP/COM/ICC/MPF, fsync/hash/Journal y hardlink exclusivo.
No llamar a `export_image` con `CompositionStatus.CROPPED`, no fingir box de recorte. Añadir `watermark`
como campo opcional preservando lectores/validadores manifest v1 anteriores. El trabajo incluye
`job_type=watermark` y huellas SHA-256 de PNG; fallback `copy_original` publica bytes idénticos. El original
nunca es target.
