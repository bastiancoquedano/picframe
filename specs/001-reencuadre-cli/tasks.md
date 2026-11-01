# Tasks: Reencuadre seguro por lotes — prototipo CLI

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/` y `quickstart.md`.
**Created**: 2026-11-01.
**Prerequisites**: constitución y especificación clarificada; revisión documental 16/16.
**Tests**: exigidas por la especificación y la constitución. Escribir y comprobar el fallo de las
pruebas de cada capacidad antes de implementarla; no marcar pruebas reales no ejecutadas como aprobadas.
**Organization**: tareas por historia, con pruebas independientes y dependencias explícitas.

## Format: `[ID] [P?] [Story] Description`

Cada tarea incluye identificador secuencial y rutas relativas al repositorio. [P] identifica
archivos distintos sin dependencia mutua dentro del grupo indicado. No autoriza crear agentes.
Las marcas [X] corresponden a tareas verificadas; [ ] indica trabajo pendiente.
La aceptación del MVP y las pruebas fotográficas se registran por separado.

## Phase 1: Setup (Shared Infrastructure)

**Objetivo**: hacer instalable el paquete y preparar validación; Git, uv y Spec Kit ya existen.

- [X] T001 Configurar paquete src instalable y entry point raceframe en pyproject.toml, src/raceframe/__init__.py y src/raceframe/__main__.py; mantener separadas dependencias ligeras y detector opcional y actualizar uv.lock sin incorporar YOLO todavía.
- [X] T002 [P] Definir ejecución de ruff y pruebas unitarias sin pesos en .github/workflows/checks.yml y documentar en README.md que una ejecución sin pruebas o con inferencia omitida no valida el MVP.
- [X] T003 [P] Crear fábricas de fotografías y detector simulado en tests/conftest.py y tests/fixtures/README.md; generar fixtures sintéticos temporales, sin fotografías privadas ni binarios de modelos en Git.

**Checkpoint**: paquete importable; herramientas de calidad ejecutables. T002 y T003 después de T001.

## Phase 2: Foundational (Blocking Prerequisites)

**Objetivo**: tipos, configuración, entrada y orientación compartidos por todas las historias.

- [X] T004 Definir Box, Detection, Selection, Composition, InputImage, ImageResult, Job y enums en src/raceframe/core/models.py conforme a data-model.md; usar tipos puros sin importar Qt, torch, cv2 ni ultralytics.
- [X] T005 [P] Escribir validación de configuración en tests/unit/test_config.py: precedencia CLI/config/defaults, claves desconocidas, valores no finitos, pesos, calidad, márgenes y rangos; cubrir FR-001 y FR-023.
- [X] T006 Implementar configuración y serialización de valores efectivos en src/raceframe/config.py, respetando los parámetros numéricos de plan.md y rechazando datos inválidos antes de escribir salidas.
- [X] T007 [P] Escribir tests/integration/test_discovery.py para extensiones, Unicode, recursión, inventario estable, rutas equivalentes, enlaces externos y destinos inseguros; cubrir FR-002, FR-003 y FR-004.
- [X] T008 Implementar inventario determinista, identidad de rutas y validación de destino en src/raceframe/imaging/discovery.py; no seguir enlaces de directorio ni aceptar destinos dentro de entrada; revalidar archivos al abrir.
- [X] T009 Escribir tests/integration/test_orientation.py para EXIF 1–8, dimensiones almacenadas/orientadas, JPEG dañado y orientación inválida; generar imágenes asimétricas para comprobar rotaciones/reflejos.
- [X] T010 Incorporar Pillow evaluado, actualizar pyproject.toml y uv.lock e implementar src/raceframe/imaging/loader.py con carga orientada y captura EXIF/ICC; preservar las referencias originales sin guardar sobre ellas.

**Checkpoint**: T004 → T005/T007; T006 depende de T005 y T004; T008 de T007 y T006;
T009 después de T008; T010 después de T009. No comenzar historias sin esta base validada.

## Phase 3: User Story 1 - Encuadres útiles sin perder originales (Priority: P1)

**Objetivo**: recorrer un lote pequeño con protagonista fiable y modo conservador/original,
exportando copias o recortes seguros. La selección de esta historia solo acepta una persona
elegible; ante varios candidatos, conserva para revisión hasta completar US2.
**Independent Test**: lote de imágenes sintéticas con detector simulado y una persona conocida;
comparar geometría, orientación, salidas y SHA-256 originales sin GUI ni pesos reales.

### Tests for User Story 1

- [X] T011 [P] [US1] Escribir tests/unit/test_cropping.py para centrado, izquierda/derecha, bordes, cuerpo completo, plano medio, protección y redondeo exterior; verificar límites y ausencia de recorte agresivo con proporción original.
- [X] T012 [P] [US1] Escribir tests/integration/test_export.py para copia byte por byte, calidad JPEG, EXIF/ICC actualizado, miniaturas obsoletas, bloques no verificables, colisiones y original inmutable; cubrir FR-014 a FR-016.

### Implementation for User Story 1

- [X] T013 [US1] Implementar motor geométrico puro conservador/original en src/raceframe/core/cropping.py: región protegida, límite de área, centrado horizontal, mínima mejora y resultado sin cambios o revisión; satisfacer T011 sin cargar detector.
- [X] T014 [US1] Implementar preparación temporal y publicación JPEG sin reemplazo en src/raceframe/export/jpeg.py; probar capacidad de enlace exclusivo en destino, conservar copias exactas y auditar metadatos según T012.
- [X] T015 [US1] Definir Protocol del detector y selección provisional segura de una sola persona en src/raceframe/core/detection.py y src/raceframe/core/selection.py; varios candidatos siempre requieren revisión hasta US2, sin inferir identidad deportiva.
- [X] T016 [US1] Escribir tests/integration/test_process_basic.py y tests/integration/test_cli_basic.py con detector simulado para entrada vacía, fotos legibles/dañadas, rutas inseguras y códigos de salida del contrato.
- [X] T017 [US1] Implementar recorrido secuencial básico e inventario en src/raceframe/core/processing.py, con modelo inyectable, una fotografía activa, copias ante incertidumbre y resultado por entrada sin sobrescribir archivos.
- [X] T018 [US1] Implementar process conservador/original con argparse en src/raceframe/cli/main.py: validar antes de escribir, stdout JSON, progreso español a stderr, --help y --version; no anunciar opciones aún no implementadas como operativas.
- [X] T019 [US1] Resolver versiones conjuntas de Ultralytics/OpenCV/torch/torchvision en pyproject.toml y uv.lock e inventariar licencias efectivas en docs/dependencias.md; no instalar dos distribuciones cv2 ni afirmar compatibles candidatas no comprobadas.
- [X] T020 [US1] Escribir tests/unit/test_detector_adapter.py y tests/integration/test_detector_cpu.py para clase persona, BGR, dimensiones orientadas, ausencia de doble escalado, modelo ausente y carga única; separar inferencia real que requiere pesos.
- [X] T021 [US1] Implementar adaptador YOLO de import tardío y preparación CPU en src/raceframe/core/detection.py; exigir archivo local, desactivar sincronización/trackers/autoinstall antes del import y conectar CLI al detector sin permitir URLs.
- [X] T022 [US1] Preparar explícitamente YOLO11n fuera de Git y registrar URL, licencia, SHA-256 y versiones en docs/modelos.md; ejecutar smoke CPU y registrar el resultado real en docs/validacion-cli.md, sin fotografías privadas.

**Checkpoint**: T011 → T013; T012 → T014; T015 después de T004 y T006; T016 precede
T017/T018; T017 depende de T013–T016 y T018 de T017. T019 → T020 → T021 → T022.
La integración real exige T021 y T018. Aceptar US1 solo con su recorrido simulado y smoke real;
no confundirlo con validación fotográfica ni aceptación del MVP completo.

## Phase 4: User Story 2 - Fotografías que requieren revisión (Priority: P1)

**Objetivo**: selección explicable entre varias personas, conservando fotos inciertas sin cambios.
**Independent Test**: cajas y confianzas conocidas sin YOLO, incluyendo caso donde la mayor
persona no gana, empate, segundo candidato cercano, baja confianza y ausencia de detecciones.

### Tests for User Story 2

- [X] T023 [P] [US2] Escribir tests/unit/test_selection.py para todos los factores y umbrales del plan, cajas no finitas/degeneradas, desempate determinista y ambigüedad respecto del segundo candidato válido.
- [X] T024 [P] [US2] Escribir tests/integration/test_review_policy.py para copia íntegra y marca de revisión en grupo ambiguo, ausencia de personas, baja confianza y recorte inviable; comprobar que un fallo de copia es error, no éxito.

### Implementation for User Story 2

- [X] T025 [US2] Sustituir selección provisional por puntuación configurable completa en src/raceframe/core/selection.py; registrar factores, elegibilidad, descartes y motivo sin asumir visibilidad real ni identidad de corredor.
- [X] T026 [US2] Integrar estados de revisión y métricas de selección en src/raceframe/core/processing.py y src/raceframe/cli/main.py; incluir todas las detecciones/puntuaciones y conservar copia byte por byte cuando no hay selección fiable.

**Checkpoint**: T023/T024 después de la base y antes de T025/T026; T026 requiere T017/T018.
El selector se valida independientemente de US1; su integración sustituye la política provisional segura.

## Phase 5: User Story 3 - Lotes, cancelación y auditoría (Priority: P2)

**Objetivo**: diario durable, manifiesto, manejo de errores y recuperación sin falsos éxitos.
**Independent Test**: lote sintético mixto con cancelación y fallos entre preparar, publicar y
confirmar; reconciliar inventario, diario, salidas y contadores sin inferencia real.

### Tests for User Story 3

- [X] T027 [P] [US3] Escribir tests/integration/test_manifest.py para campos obligatorios, coordenadas, nulls, una fila por candidato y ecuación de contadores; distinguir revisión de estado operativo.
- [X] T028 [P] [US3] Escribir tests/integration/test_cancel.py para SIGINT, no iniciar otra imagen tras reconocer cancelación, salida activa segura, candidatos no intentados y código 130.
- [X] T029 [P] [US3] Escribir tests/integration/test_recovery.py para línea JSONL truncada, hash incorrecto, publicación sin confirmación, proceso aún activo, fallo de auditoría y recuperación sin sobrescribir ni reanudar.

### Implementation for User Story 3

- [X] T030 [US3] Implementar diario incremental y manifiesto derivado en src/raceframe/export/manifest.py y esquema v1 en specs/001-reencuadre-cli/contracts/manifest.schema.json, incluyendo inventario, intenciones, fsync y estados definidos.
- [X] T031 [US3] Integrar intenciones/confirmaciones de exportación en src/raceframe/export/jpeg.py y src/raceframe/core/processing.py; impedir éxito parcial, continuar errores recuperables y detener fallos globales de disco/auditoría.
- [X] T032 [US3] Implementar cancelación cooperativa y resumen reconciliado en src/raceframe/core/processing.py y src/raceframe/cli/main.py; informar totales, revisión, duración y destino sin acumular imágenes decodificadas.
- [X] T033 [US3] Implementar report y report --recover en src/raceframe/export/manifest.py y src/raceframe/cli/main.py; verificar trabajo inactivo con bloqueo exclusivo, confirmar hashes preparados y generar informe recuperado exclusivo sin cargar YOLO.
- [X] T034 [US3] Ejecutar fallos de publicación, destino no compatible, disco lleno y rutas duplicadas con fixtures en tests/integration/test_batch_failures.py; comprobar originales y registrar evidencia en docs/validacion-cli.md.

**Checkpoint**: T027/T028/T029 son independientes; T030 requiere T027/T029 y T004;
T031 requiere T030/T014/T017; T032 requiere T028/T031; T033 requiere T029/T030 y CLI;
T034 después de T031–T033. Ninguna foto cuenta exportada antes de publicación completa.

## Phase 6: User Story 4 - Modos y proporciones (Priority: P2)

**Objetivo**: añadir equilibrado/cerrado y 3:2/4:5 sin cambiar reglas de protección.
**Independent Test**: misma caja conocida en los tres modos y proporciones, horizontal y
vertical; comparar área retenida, redondeo y casos inviables sin ejecutar detector.

### Tests for User Story 4

- [X] T035 [P] [US4] Ampliar tests/unit/test_cropping_modes.py con conjuntos de cajas para retención anidada, proporción literal, error máximo de un píxel, área de referencia y margen factible idéntico entre modos.
- [X] T036 [P] [US4] Escribir tests/integration/test_cli_options.py para --mode, --aspect, --margin y --quality, rangos inválidos, archivo de configuración, precedencia y fallback de formato imposible a copia marcada.

### Implementation for User Story 4

- [X] T037 [US4] Extender src/raceframe/core/cropping.py y src/raceframe/config.py con los tres modos, proporciones y área de referencia del mayor rectángulo de formato solicitado; conservar la protección común y registrar retención original/adicional.
- [X] T038 [US4] Exponer opciones completas en src/raceframe/cli/main.py y propagar valores efectivos a src/raceframe/core/processing.py y src/raceframe/export/manifest.py; diferenciar proporción solicitada y efectiva cuando se copia sin cambios.

**Checkpoint**: T035/T036 después de base, T037 después de T013/T035;
T038 después de T036/T037 y la integración de US3; no duplicar motores por modo.

## Phase 7: Polish & Cross-Cutting Concerns

**Objetivo**: completar garantías transversales y evaluación antes de aceptar el prototipo.

- [X] T039 Añadir --device auto/mps con comprobación e inferencia de preparación en src/raceframe/core/detection.py y tests/integration/test_device.py; CPU sigue disponible, auto advierte fallback y mps explícito falla si no es utilizable.
- [X] T040 Verificar import y procesamiento real con red bloqueada en tests/integration/test_offline.py y documentar mecanismo y resultados en docs/validacion-cli.md; no equiparar una bandera de configuración con prueba offline.
- [X] T041 Completar trazabilidad FR-001 a FR-025 y SC-001 a SC-008 en docs/validacion-cli.md y ejecutar ruff check, ruff format --check y pytest; corregir fallos y distinguir pruebas reales omitidas de pruebas aprobadas.
- [ ] T042 Preparar plantilla de revisión local en docs/evaluacion-fotografica.md y evaluar con el propietario 30–50 fotos privadas: selección, integridad visible, composición, marca de revisión y utilidad de casos lateral/cintura/centrado/borde; no subir fotos ni rutas de muestra privadas a GitHub.
- [ ] T043 Medir lote representativo de 2.000–3.500 fotos con tiempo, rendimiento, dispositivo y RSS máximo, registrar en docs/rendimiento.md y comprobar memoria acotada; no extrapolar precisión o velocidad sin mediciones.
- [X] T044 Actualizar README.md y specs/001-reencuadre-cli/quickstart.md con comandos ya comprobados, limitaciones EXIF/detector, política de revisión, preparación explícita de modelo y estado real de validación; registrar avance revisable en specs/001-reencuadre-cli/tasks.md y publicar cambios en GitHub.

**Checkpoint**: T039 después de T021; T040 después de T022 y CLI completa; T041 tras
US1–US4/T039/T040; T042 necesita muestra privada y valoración del propietario; T043 lote real.
T044 se actualiza incrementalmente; no marcar T042/T043 completas sin acceso/evidencia real.

## Dependencies & Execution Order

```text
Setup → Foundation → US1 básica → US2 → US3 → US4 → Calidad/validación
                       │                          ↑
                       └→ Detector CPU real ──────┘
Foundation → pruebas US2, pruebas US4 (independientes del detector)
Exportación base → diario/recuperación US3
Todas las historias → offline + revisión fotográfica + mediciones
```

US1 entrega el primer recorrido útil conservador con una persona y preservación segura;
US2 añade elección entre personas; US3 robustece trabajos largos y su auditoría; US4 expone
los demás modos y proporciones. Ninguna entrega intermedia debe anunciar soporte de toda
la especificación. Los tests unitarios de selección y geometría son independientes, aunque
su integración real reutiliza la tubería del primer incremento.

### Parallel Opportunities and Examples

Los ejemplos indican trabajo técnicamente independiente; no requieren múltiples agentes.

- Setup: T002 y T003 después de T001, sin modificar el mismo archivo.
- Base: T005 y T007 después de T004; implementar cada capacidad después de su prueba.
- US1: T011 en tests/unit/test_cropping.py y T012 en tests/integration/test_export.py.
- US2: T023 en tests/unit/test_selection.py y T024 en tests/integration/test_review_policy.py.
- US3: T027, T028 y T029 en sus archivos separados.
- US4: T035 y T036 en archivos separados; implementaciones T037/T038 secuenciales.

No paralelizar T025 y T015 ni tareas que escriban processing.py, cli/main.py, config.py,
pyproject.toml o uv.lock simultáneamente.

## Implementation Strategy

1. Ejecutar setup/base y demostrar geometría sin YOLO; commit pequeño tras validación.
2. Completar US1 conservador/original con detector simulado y luego smoke CPU real.
3. Añadir US2, US3 y US4, ejecutando pruebas de cada historia y regresión aplicable.
4. Ejecutar offline, revisión fotográfica y volumen; entregar evidencia sin llamar validado
   al MVP hasta terminar todas sus condiciones.
5. Registrar y subir commits a https://github.com/bastiancoquedano/raceframe sin incluir
   fotografías, pesos, credenciales, entornos o informes con datos privados.

**MVP sugerido**: US1 es una demostración inicial de valor, no el MVP aceptado completo.
La aceptación del prototipo exige US1–US4, incertidumbre segura y validación real definida.
No introducir GUI, RAW, pose, dorsales ni reanudación durante estas tareas.

## Requirement Coverage

| Requisito | Tareas |
| --- | --- |
| FR-001 | T005, T006, T018, T036, T038 |
| FR-002 | T007, T008, T017 |
| FR-003 | T007, T008, T012, T014, T034 |
| FR-004 | T007, T008, T018 |
| FR-005 | T021, T040 |
| FR-006 | T009, T010, T020, T021 |
| FR-007 | T023, T025 |
| FR-008 | T023, T024, T025, T026 |
| FR-009 | T012, T014, T024, T026 |
| FR-010 | T011, T013, T035, T037 |
| FR-011 | T011, T013, T037 |
| FR-012 | T035, T037 |
| FR-013 | T035, T036, T037, T038 |
| FR-014 | T012, T014, T036 |
| FR-015 | T009, T010, T012, T014 |
| FR-016 | T012, T014, T024 |
| FR-017 | T027, T030, T031, T038 |
| FR-018 | T027, T030, T032 |
| FR-019 | T028, T030, T032, T033 |
| FR-020 | T016, T017, T029, T031, T034 |
| FR-021 | T028, T032 |
| FR-022 | T017, T021, T043 |
| FR-023 | T005, T006, T025, T030, T038 |
| FR-024 | T042 |
| FR-025 | T019, T022, T044 |
| SC-001 | T012, T034 |
| SC-002 | T011, T035 |
| SC-003 | T011, T023, T024 |
| SC-004 | T027, T028, T029, T034 |
| SC-005 | T043 |
| SC-006 | T040, T042 |
| SC-007 | T042 |
| SC-008 | T030, T033, T042 |

## Notes

44 tareas: setup 3, base 7, US1 12, US2 4, US3 8, US4 4, transversal 6.
No hay hooks before_tasks/after_tasks configurados. Implementación técnica completada: 45/47 tareas, incluido el refinamiento focal/metadatos.
T042/T043 permanecen pendientes por indicación del propietario: evaluación y evento real
se harán con su ayuda. No se considera el MVP validado fotográficamente.
Las limitaciones de acceso a fotos reales se comunicarán al alcanzar T042/T043, sin fabricar resultados.

## Estado de aceptación — 2026-11-01

Implementación técnica CLI y comprobaciones automatizadas completas. T042 y T043 siguen
sin marcar: el propietario respondió que realizará la prueba con sus fotos con ayuda del agente.
No son bloqueos técnicos de código ni motivos para inventar fotografías/mediciones.
La convergencia y aceptación completas requieren esa evidencia; mantenerla pendiente.

## Phase 8: Refinamiento por evaluación de muestra

- [X] T045 Preservar y verificar EXIF/MakerNotes y bloques APP/COM en src/raceframe/export/metadata.py y tests/integration/test_export.py, sin publicación ante pérdida, conforme a FR-028.
- [X] T046 Implementar focal real, ocupación y límite de resolución en src/raceframe/core/cropping.py, src/raceframe/config.py y tests/unit/test_focal_framing.py, conforme a FR-026/FR-027.
- [X] T047 Documentar preparación ExifTool, actualizar contrato/CLI y reprocesar la muestra a un trabajo nuevo con tiempos y comparación de metadatos, sin tocar originales; README.md y scripts/prepare_metadata_tool.py.
