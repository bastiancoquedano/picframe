# Modelo de datos: Smart Watermark

## WatermarkConfig

`mode=traditional|smart`; calidad JPEG 1..95 (default95); lista ordenada de capas; firma opcional;
fallback `traditional_foreground|copy_original|skip_image`; default `traditional_foreground` aprobado;
origen/destino/job_name/recursive y huellas de assets en la configuración del manifiesto. Normalizar
anchors/desplazamientos y medidas como fracciones del lienzo orientado; validar antes de procesar.

## WatermarkLayer

PNG+SHA256; ancho objetivo como fracción del ancho de foto; ubicación (centro y 8 anchors), offset x/y,
opacidad 0..1, patrón opcional repeat/spacing. Tradicional admite una o más; Smart usa una principal
para crear profundidad. Máscaras solo ocluyen alfa principal. Assets no viajan en outputs/Git.

## SignatureLayer

enabled; `kind=text|png`; texto o recurso PNG+SHA256; tamaño relativo al lado largo; posición/anchor,
opacidad, margen (default bottom-center), fuente. Es siempre la última capa y puede cubrir píxeles de
persona si usuario ubica ahí la firma, de forma intencional.

## PersonMask y renderer

`PersonMask(status=ok|empty|error, width,height, backend/version, compute_device, quality, reason)`.
Máscara vacía sin valores = respuesta válida sin personas; matte sin core de confianza >=128 es error
`low_confidence_mask`. `error` aplica el fallback configurado con warning/review_required. Nunca
persistir mapa o píxeles en manifest. En memoria: source RGB orientado → capas principales → máscara
union → signature → codificador JPEG. High-confidence core de persona es pixel-identical tras ocluir PNG
principal, anterior a firma y JPEG.

## Job y WatermarkImageResult

Manifest v1 aditivo: `job_type=watermark`; fila con configuración `watermark` (modo, estado/reason de
segmentación, backend/dispositivo/calidad/revisión, fallback elegido/aplicado y review_required), warnings
y salida/hash/dimensiones. La foto tradicional registra `segmentation_status=not_attempted`. El fallback
registra `segmentation_fallback`; marca revisión si antepone la marca o copia el original. `skip_image`
registra omitted y error, sin JPEG. `empty` no requiere fallback/revisión. Errores de ExifTool/JPEG no se
publican.

## WatermarkPreset

JSON versionado local con nombre y WatermarkConfig, sin fotos ni copia de assets. Si faltan PNG referidos,
se informa path/nombre y el botón Analyze queda desactivado hasta corregirlo. Guardado atomic replace.
