# Implementation Plan: Smart Watermark para Picframe

**Branch**: main | **Date**: 2026-11-12 | **Spec**: [spec.md](spec.md)
**Approval**: propietario aprueba la especificación y fallback el 2026-11-12.

## Summary
Añadir una pestaña Tradicional/Smart para componer marcas RGBA y una identificación frontal en JPEG
sin recorte. Smart usa una máscara de personas local de Apple Vision. Ante error por imagen degrada a
aplica una política de fallback configurable por foto y conserva el lote.

## Technical Context

**Language/Version**: Python 3.11.
**Primary Dependencies**: PySide6 Essentials 6.12.0, Pillow 13.0.0, NumPy 2.4.6,
OpenCV 4.13.0.92, ExifTool 13.58, PyInstaller 6.22.3; `pyobjc-framework-Vision==13.0`
como extra opcional de macOS.
**Storage**: Config/presets JSON locales en Application Support/Picframe; archivo original read-only;
una imagen/máscara en RAM y salida/manifiesto/eventos existentes.
**Testing**: pytest/pytest-qt, máscaras Vision simuladas en todas las plataformas, pruebas JPEG/ExifTool,
smoke real Vision y PyInstaller offline en macOS arm64.
**Target Platform**: macOS 12+ arm64. Vision nativo como backend primario.
**Project Type**: App desktop PySide6, core Python, CLI actual no se cambia.
**Performance Goals**: tiempo por foto medido con imagen/resolución y equipo; lote secuencial inicial
para 1.000–5.000, sin cargar el lote. No prometer un tiempo fijo.
**Constraints**: privacidad local, sujeto intacto en máscara principal, EXIF/ICC estricto, coordenadas
orientadas, JPEG original sin cambios, cancelación, App sin descarga durante procesamiento.
**Scale/Scope**: entrada y salida JPEG; capas PNG/RGBA; texto; segmentación de personas solamente;
sin RAW, firma/servicio cloud, animal/vehículo segmentation, ni estampado destructivo de originales.

## Constitution Check

1. Privacidad: Vision local; PyObjC sin tráfico/fotos fuera. Conforme.
2. Originales: sólo apertura read-only, destino separado, publicación temporal/atomic. Conforme.
3. Integridad: renderer de watermark no invoca cropper; dimensiones/aspecto pixel-preserving. Conforme.
4. Incertidumbre: fallback tradicional/copia exacta/omitir configurable; valor predeterminado Tradicional aprobado; el lote continúa. Conforme.
5. Modularidad: watermark renderer/segmenter no depende de MainWindow; mismo manifest/exporter. Conforme.
6. Calidad: píxeles mask-core, `metadata_verified`, transparencia, orientación, fallos/batches testeados. Conforme.
7. Robustez: QThread/event, cancel entre fotos, una imagen/máscara. Benchmark documentado. Conforme.
8. Spec Kit: spec 16/16 y aprobada; investigación, plan, contratos, tareas antes de código. Conforme.

## Project Structure

### Documentation
`specs/004-smart-watermark/{spec,plan,research,data-model,quickstart}.md`, `contracts/watermark.md`.

### Source Code
`src/raceframe/core/watermark_models.py`: capas, configuración, mask/resulto.
`src/raceframe/core/watermark_render.py`: mezcla RGBA pura y offsets centrados.
`src/raceframe/core/watermark_processing.py`: analyze/render/fallback/batch.
`src/raceframe/watermark/vision.py`: Vision adapter, autorelease pool.
`src/raceframe/watermark/presets.py`: JSON local versionado/validado.
`src/raceframe/export/jpeg.py`: `export_rendered_jpeg` temp + metadata/ICC + atomic publish.
`src/raceframe/ui/watermark_page.py`: controls, before/after, preset y worker; `ui/window.py`: tab.
`packaging/raceframe.spec`, `pyproject.toml`, `uv.lock`, `scripts/build_macos.py`: Vision binding frozen.
`tests/unit`, `tests/integration`: render, API adapter, metadata, UI/batch, Vision real mac.

**Structure Decision**: `QTabWidget` mantiene la pantalla Encuadre en su propia página y agrega
Marcas de agua. `WatermarkPage` tiene estado/worker propio; MainWindow cancela las páginas activas y
espera sus workers antes de cerrar. Rendering core recibe sólo imagen orientada, capas y máscara. El
nuevo workflow reutiliza discovery, worker signals, Journal y metadata publisher pero no llama a
detector de recorte ni introduce una persona de mentira en `process_folder`.

## Phase 0 Research — decisiones cerradas

- Vision `VNGeneratePersonSegmentationRequest`, `accurate`; máscara semántica union basta para un
  símbolo central detrás de todas las personas. `Vision` devuelve PixelBuffer que puede bajar resolución;
  normalizar X/Y de la imagen y liberar autorelease pool/cv buffers por archivo.
- PyObjC Vision 13.0 MIT declarado; el extra opcional se fijó y pasó gates T001/T002: request sintética,
  PixelBuffer L008, build arm64 y smoke offline del bundle. Sin cambio de hardware ni pesos.
- YOLO11n-seg queda alternativa documentada condicionada; no agregar el peso automáticamente. Si
  Vision no se puede congelar, detener y reevaluar antes de instalar otro peso.
- Fallback producto elegido: Tradicional por foto + `review_required` warning; archivo debe continuar.
- Ver [research.md](research.md) y fuentes oficiales citadas.

## Phase 1 Design

Ver [data-model.md](data-model.md), [contracts/watermark.md](contracts/watermark.md) y
[quickstart.md](quickstart.md). Metadatos mantienen esquema existente con campos aditivos `watermark`;
rendered JPEG usa publisher atómico actual y ExifTool antes de publicar.

## Complexity Tracking

Sin infracción constitucional. PyObjC es binding opcional Darwin, no nuevo runtime de visión paralelo.
No se cambia la arquitectura ni se agrega un proceso/subproceso para cada persona/foto.

## Risks / Failure Decisions

- Los bordes/motion blur/traslúcidos pueden fallar; los tests automáticos demuestran álgebra, no precision
  real. Evaluación visual personal permanece pendiente.
- La ID superior cambia intencionalmente los píxeles que cubre; test de identidad se mide antes de ID y JPEG.
- Fallback Traditional puede cubrir la persona; la foto se marca para revisión.
- No garantizar protección absoluta contra herramientas de borrado; la marca central es removible.
- Presets validan referencias de recursos; no incluir logos personales dentro de Git o la app.

## Implementation Phases

1. PyObjC/Vision spike y renderer/tests en memoria.
2. Export full-frame/JPEG metadata y pipeline/journal.
3. Tradicional/firma y UI/presets.
4. Segmentación Smart/fallback, orientación/máscaras.
5. Lote/cancel, bundle/offline smoke, CI/docs.
