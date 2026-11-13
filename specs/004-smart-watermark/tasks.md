---
description: "Tareas para Smart Watermark"
---

# Tasks: Smart Watermark para Picframe

**Input**: Diseño en `specs/004-smart-watermark/` (spec, plan, research, model, contract y quickstart).
**Tests**: Obligatorias por spec/aprobación; tests empezados antes de implementación (TDD).
**Organización**: Tareas trazadas por historia e independientes tras las dependencias base.

## Phase 1: Setup
**Propósito**: Habilitar la máscara nativa y verificar el gate de plataforma antes del resto de UI.

- [x] T001 Probar `scripts/vision_spike.py` y `tests/unit/test_watermark_vision.py`; fijar extras Darwin `watermark-vision` (Vision/NumPy) y `uv.lock`; ejecutar `VNGeneratePersonSegmentationRequest`, L008, tamaño/máscara, autorelease y escalado con imagen sintética. Registrar gate/procedencia en `research.md`.
- [x] T002 Congelar Vision dentro de `Picframe.app` y comprobar detección/request offline vía `src/raceframe/ui/smoke.py`, `packaging/raceframe.spec`, `scripts/build_macos.py` en el Mac; garantizar que operación CLI/UI sin máscara Vision queda sin cambios.

## Phase 2: Foundation
**Propósito**: Modelos/capa compositor puros y comprobables sin Qt o Vision.

- [x] T003 Escribir `tests/unit/test_watermark_models.py` para Config, fuentes PNG, alpha, opciones fuera de rango y presets inválidos/válidos.
- [x] T004 Implementar modelos inmutables y validación en `src/raceframe/core/watermark_models.py`.
- [x] T005 Escribir `tests/unit/test_watermark_render.py`: stacking, coordenadas/anchors, opacidad, canvas original y comparación exacta de persona protegida antes de ID.
- [x] T006 Implementar compositor puro Pillow en `src/raceframe/core/watermark_render.py` con marcas Traditional/Smart, alfa PNG y firma final.

## Phase 3: User Story 1 — Marca tradicional (Priority: P1)
**Historia**: aplicar PNG transparente sin segmentación y conservar la resolución.
**Independent Test**: importar logo sintético, previsualizar/posicionar y exportar con origen inmutable.

- [x] T007 [US1] Probar transparencia, varias PNG, repetición, logo inválido, dimensiones y RGB de entrada en tests de compositor y lote.
- [x] T008 [US1] Implementar distribución/posición del asset y patrón en `src/raceframe/core/watermark_render.py`.
- [x] T009 [US1] Añadir pruebas en `tests/integration/test_watermark_export.py` para JPEG full-frame, ICC/EXIF, colisión, integridad y `metadata_verified`.
- [x] T010 [US1] Implementar `export_rendered_jpeg` y copia byte-a-byte reutilizando metadatos/Journal/publicación atómica; verificar antes de publicar.

## Phase 4: User Story 2 — Profundidad Smart (Priority: P1)
**Historia**: ocultar el PNG principal detrás de una oclusión persona, sin retocar píxeles.
**Independent Test**: máscara inyectada con varias personas, superposición, huecos y bordes; igualdad RGB core.

- [x] T011 [US2] Probar PixelBuffer fake/empty/error/fallback, escalado anisotrópico y orientación en `tests/unit/test_watermark_vision.py` y `tests/integration/test_watermark_batch.py`; Vision real con `real_vision`.
- [x] T012 [US2] Implementar `VisionPersonSegmenter`, autorelease/lock/stride/copy/unlock en `src/raceframe/watermark/vision.py`; Traditional no crea Vision request.
- [x] T013 [US2] Integrar máscara unión y fallback por foto en `src/raceframe/core/watermark_processing.py`; probar compositor foreground exacto y revisión.

## Phase 5: User Story 3 — Firma y presets locales (Priority: P1)
**Historia**: identificación por encima de capas y repetir una configuración.
**Independent Test**: ID activo/desactivado, Text/PNG, preview igual al render, preset round-trip.

- [x] T014 [US3] Probar firma/z-order y recursos faltantes en `tests/unit/test_watermark_models.py`, render y `tests/integration/test_watermark_ui.py`.
- [x] T015 [US3] Implementar firma de texto/PNG en Pillow y su selección en Qt; margen/anchor en `src/raceframe/core/watermark_render.py`.
- [x] T016 [US3] Persistir presets JSON locales atómicos en `src/raceframe/watermark/presets.py`; validar rutas y hashes al cargar.

## Phase 6: User Story 4 — Lote con fallos recuperables (Priority: P1)
**Historia**: ejecutar miles de fotos en segundo plano, con progreso y cancelación por foto.
**Independent Test**: carpeta con imágenes buenas/rotas, Smart error y tres fallbacks configurables; manifiesto por cada una.

- [x] T017 [US4] Probar Journal, inventario de 1k, cancel, progreso, error por foto y fallo de metadata sin publicación en `tests/integration/test_watermark_batch.py`.
- [x] T018 [US4] Implementar pipeline separado/incremental; reuse discovery/Journal, una foto/máscara, fallback configurable, hash final y verificación metadata.
- [x] T019 [US4] Probar Qt para PNG, modos, preset, before/after, progreso, cancelación y cierre de worker en `tests/integration/test_watermark_ui.py`.
- [x] T020 [US4] Añadir `QTabWidget` y `WatermarkPage`; conectar en `window.py` y conservar estado/worker de Encuadre.

## Phase 7: Polish y aceptación

- [x] T021 [P] Extender schema de forma aditiva con `job_type=watermark` y campo opcional por fila; validar manifest v1.
- [x] T022 Actualizar README, guía desktop, dependencias y guía de Watermarks con operación local, límites, fallback y privacidad.
- [x] T023 Ejecutar ruff, suite completa, 1k sintético, Vision local sintético y `Picframe.app` bajo `deny network*`; guardar evidencia en `docs/smart-watermark-validation.md`.
- [ ] T024 Confirmar el build y la firma en macOS 26.6.2, documentar que la versión mínima macOS 12 no se probó en otro equipo, subir sólo código/documentación a `picframe`, revisar CI y dejar el árbol limpio; no subir logos, fotos, weights ni presets.

## Dependencies & Execution Order

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 →
T011 → T012 → T013 → T014 → T015/T016 → T017 → T018 → T019 → T020 → T021/T022 → T023 → T024.
T001–T002 gates Smart/tab. Si Vision frozen falla, detener antes de T012/T020 y adaptar diseño/backend.

## Parallel Opportunities

T021 manifest/schema y T022 docs pueden escribirse en paralelo después de estabilizar contract. El resto
secuencial por los contratos compartidos `WatermarkConfig` y `export_rendered_jpeg`. No usar agentes de
implementación; un escritor por cada fichero fuente.

## MVP e Implementación incremental

Completar Foundation y US1 Traditional, revisar artefacto en app. Habilitar US2 tras aprobar el spike Vision.
Después signature/preset y batch. Tradicional no espera ni crea un objeto Detector. Máscaras/PIL/Qt jobs
se inyectan en tests; ninguna fotografía privada se agrega a Git.

## Cobertura

FR001 T019/T020; FR002/FR003 T003–T008; FR004/FR005 T011–T013; FR006 T014–T016;
FR007 T019/T020; FR008/FR009 T017–T020; FR010 T009/T010; FR011 T014/T016;
FR012 T017/T018/T021; FR013 T001/T002/T023.
SC001 T007–T010; SC002 T005/T011/T013; SC003 T009/T011/T019;
SC004 T017–T020; SC005 T009/T010; SC006 T001/T002/T023; SC007 T014/T016.
No hay extension hooks registradas. T042/T043 previas siguen pendientes y no se cierran aquí.
