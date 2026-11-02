# Tasks: Picframe — sujetos generales

**Input**: spec.md, plan.md, research.md, data-model.md y contracts/subjects.md.
**Tests**: requeridas por constitución; sintéticas, Qt, detector real y bundle sin red.

## Phase 1: Setup
- [X] T001 Registrar diseño aprobado y renombrado en specs/003-general-subjects/ y AGENTS.md.

## Phase 2: Foundational
- [X] T002 Probar configuración y candidatos/selección en tests/unit/test_subject_selection.py.
- [X] T003 Implementar catálogo/configuración/modelos y candidatos en src/raceframe/{config.py,core/categories.py,core/models.py,core/subjects.py}.

## Phase 3: US1 — Categorías (P1)
**Independent Test**: detectar clases correctas y rechazar modelos con nombres incompatibles.
- [X] T004 [US1] Probar adaptador multicategoría en tests/unit/test_detector_adapter.py.
- [X] T005 [US1] Ampliar detector y selección categorizada en src/raceframe/core/{detection.py,selection.py}.

## Phase 4: US2 — Dominante y grupo (P1)
**Independent Test**: dominante por área, empate conservador, grupo íntegro y composición de objetos.
- [X] T006 [US2] Implementar estrategias y composición en src/raceframe/core/{selection.py,cropping.py,processing.py} y CLI en src/raceframe/cli/main.py.
- [X] T007 [US2] Probar exportación con metadatos, auditoría y caché en tests/integration/test_general_subjects.py.

## Phase 5: US3 — Conjuntos y revisión (P1)
**Independent Test**: parejas únicas/dudosas y selección manual no cortan miembros protegidos.
- [X] T008 [US3] Integrar corrección y etiquetas en src/raceframe/ui/{decisions.py,window.py,preview.py}.
- [X] T009 [US3] Probar categorías/grupos/corrección e invalidación en tests/integration/test_ui_subjects.py.

## Phase 6: Producto y calidad
- [X] T010 Actualizar marca/aliases en pyproject.toml, packaging/raceframe.spec, scripts/build_macos.py y docs/desktop.md.
- [X] T011 Ejecutar regresión y construir/verificar dist/Picframe.app; registrar evidencia en docs/general-subjects-validation.md.
- [X] T012 Publicar código/documentación en repo picframe y verificar estado Git.

## Dependencies & Execution Order
T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → T011 → T012.
Pruebas antes de implementación cuando definen contrato; no agentes de implementación.

## Parallel Opportunities
Investigación oficial y lectura del código pueden ser paralelas; implementación secuencial por compartir archivos.
Ejemplo US1: revisar catálogo y contrato CLI por separado; ambos deben concluir antes de modificar detector.

## Implementation Strategy
MVP: categorías primero; luego políticas, protección de conjuntos, interfaz y empaquetado.
FR001 T003/T005/T008; FR002/003/004 T006; FR005 T003/T008; FR006 T006;
FR007/008/009 T007/T009; FR010 T010/T011/T012. SC001 T009; SC002/003 T002/T007;
SC004 T009; SC005 T011. Sin hooks registrados; T042/T043 anteriores siguen pendientes.

## Corrección: Automático y selección múltiple
- [X] T013 Probar configuraciones múltiples, deduplicación y lote mixto en tests/unit/test_subject_selection.py y tests/integration/test_ui_subjects.py.
- [X] T014 Implementar unión de categorías y compatibilidad en src/raceframe/{config.py,core/categories.py,core/subjects.py,core/selection.py,core/detection.py,cli/main.py}.
- [X] T015 Reemplazar selector por Automático/casillas en src/raceframe/ui/window.py, con caché y validación coherentes.
- [X] T016 Actualizar contratos/docs, ejecutar regresión y construir/verificar Picframe.app; publicar código.
Dependencias: T013 → T014 → T015 → T016. Sin hooks de extensión.
