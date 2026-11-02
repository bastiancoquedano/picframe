# Tasks: Interfaz de escritorio

**Input**: spec.md, plan.md, research.md, data-model.md y contracts/ui.md.
**Tests**: requeridas; datos sintéticos y detector simulado, más smoke nativo y bundle real.

## Phase 1: Setup

- [X] T001 Preparar extras gui/build y pytest-qt en pyproject.toml/uv.lock; conservar CLI y dependencias opcionales.

## Phase 2: Foundational

- [X] T002 Escribir tests/integration/test_analysis_cache.py para análisis sin exportación, caché vigente, firma/configuración obsoleta e inferencia no repetida.
- [X] T003 Separar analyze_loaded/analyze_image y exportación de decisiones validadas en src/raceframe/core/processing.py sin importar Qt.
- [X] T004 Probar e implementar selección manual y ROI proporcional seguro en tests/unit/test_ui_decisions.py y src/raceframe/ui/decisions.py.
- [X] T005 Escribir tests/integration/test_ui_workers.py para progreso, cancelación y respuesta asíncrona.
- [X] T006 Implementar trabajadores y resolución de recursos en src/raceframe/ui/workers.py y src/raceframe/ui/resources.py.

## Phase 3: User Story 1 - Preparar y abrir (P1)

**Independent Test**: elegir carpetas sintéticas y analizar sin consola ni bloqueo.
- [X] T007 [US1] Implementar ventana en español con rutas, parámetros, conteo y controles en src/raceframe/ui/window.py y entradas de arranque.
- [X] T008 [US1] Verificar rutas, estados y edición de parámetros con tests/integration/test_ui_window.py.

## Phase 4: User Story 2 - Revisar y corregir (P1)

**Independent Test**: elegir candidato alternativo y ROI válido/inválido con detector simulado.
- [X] T009 [US2] Probar coordenadas de preview, selección y recorte manual con tests/integration/test_ui_review.py.
- [X] T010 [US2] Implementar comparación y overlays interactivos en src/raceframe/ui/preview.py y conectar decisiones en window.py.

## Phase 5: User Story 3 - Exportar y cancelar (P1)

**Independent Test**: exportación de decisiones vigentes, cancelación y cierre seguro.
- [X] T011 [US3] Probar exportación/revisión, invalidación y cierre durante tarea en tests/integration/test_ui_export.py.
- [X] T012 [US3] Conectar exportación y resumen sin inferencia repetida, cancelación y Finder en src/raceframe/ui/window.py.

## Phase 6: Aplicación local y calidad

- [X] T013 Crear packaging/raceframe.spec y scripts/build_macos.py con recursos locales preparados y arquitectura arm64.
- [X] T014 Construir y abrir dist/Raceframe.app; comprobar recursos, inferencia y metadatos offline sin Developer ID/notarización.
- [X] T015 Documentar uso de escritorio y limitaciones, ejecutar regresión y CI, y publicar cambios en GitHub.

## Dependencies & Execution Order

T001 → T002 → T003 → T004 → T005 → T006 → T007/T008 → T009/T010 → T011/T012 → T013/T014 → T015.
Las pruebas de cada capacidad preceden a implementación. Un solo escritor por archivo.
Cada historia se valida con simulación antes de usar pesos/fotos reales. No se crean agentes de implementación.

## Implementation Strategy

Reutilizar núcleo; revisar primero las decisiones con datos sintéticos; luego exportación y bundle.
No excluir personas por espalda ni activar agrupamiento automático. No marcar T042/T043 del CLI como completadas.

## Requirement Coverage

FR-001/FR-002: T007/T008; FR-003: T005/T006/T012; FR-004/FR-005: T004/T009/T010;
FR-006/FR-007: T002/T003/T011/T012; FR-008: T013/T014; FR-009: T003/T006/T015.
SC-001: T008/T014; SC-002: T005/T011; SC-003/SC-004: T009/T011; SC-005: T014.
Sin hooks de extensión configurados. Formato y cobertura revisados antes de implementar.

## Evidencia de cierre

15 tareas completadas. Pruebas de interfaz, regresión CLI y diagnóstico de bundle offline
realizados; ventana nativa observada. Ver docs/desktop-validation.md. Los pendientes T042/T043
del incremento CLI continúan sin marcar; no se declaran resultados fotográficos no evaluados.

## Incremento: carpeta legible

- [X] T016 Probar nombre personalizado, colisiones, rechazo de rutas y caché UI conservado.
- [X] T017 Implementar nombre opcional seguro en núcleo y campo de carpeta en ventana.
- [X] T018 Documentar, ejecutar regresión, reconstruir app y publicar código.

## Incremento: filtro de revisión

- [X] T019 Probar clasificación, filtro/contador, selección vacía, corrección/restauración y exportación íntegra.
- [X] T020 Implementar filtro en lista sin invalidar caché ni excluir fotos al exportar.
- [X] T021 Documentar, validar regresión/bundle y publicar código.
