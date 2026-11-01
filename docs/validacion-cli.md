# Validación técnica — 2026-11-01

Implementación CLI completa, sin declarar validación fotográfica del MVP. 45/47 tareas;
T042/T043 se reservan al propietario por su indicación del 2026-11-01.

## Evidencia

- Las pruebas nuevas de exportación, procesamiento, selección, diario y modos se ejecutaron
  antes de sus implementaciones y reprodujeron los fallos esperados; luego pasaron.
- Suite completa con pesos locales: 127 pruebas aprobadas, incluidas CPU real y offline.
- La prueba offline lanza un proceso nuevo bajo sandbox-exec con deny network*, y además
  intercepta sockets/DNS: import, inferencia y exportación de un JPEG válido, junto a uno
  dañado, sin intentos de red. El código 1 por el archivo dañado es el resultado esperado.
- La inferencia sobre bus.jpg (asset público incluido en Ultralytics) detectó personas y
  devolvió cajas dentro de las dimensiones originales. No demuestra precisión en carreras.
- MPS auto preparado en este Mac: dispositivo efectivo mps, sin fallback. CPU también probado.
  Los fallos de MPS y fallback de auto se comprueban con simulación de fallo del backend.
- SIGINT real: salida 130, imagen activa completa y siguiente imagen no intentada.
- Recuperación: bloqueo activo, cola truncada, secuencia inválida y hash erróneo comprobados;
  ningún archivo existente se sobrescribe para reparar un trabajo.
- EXIF anidado, fecha, GPS, dimensiones, ICC y MakerNotes conservados y comprobados.
  Los recortes nuevos requieren metadata_verified; no se publican si la comprobación falla.
- Ultralytics parchea Image.open globalmente; Raceframe usa JpegImageFile explícito para
  mantener lectura exclusiva de JPEG y evitar la carga inesperada de pi-heif ante una entrada dañada.
- Dependencias reales resueltas e instaladas; pesos oficiales comprobados por SHA-256 y excluidos de Git.

Los tiempos de pytest no se usan como benchmark fotográfico. CI y pruebas locales se distinguen;
una ejecución remota solo se afirmará después de comprobarla en GitHub.

## Trazabilidad

Los archivos de prueba se encuentran bajo tests/unit o tests/integration.

| Requisito / criterio | Evidencia o limitación |
| --- | --- |
| FR-001 | test_config.py, test_cli_options.py |
| FR-002 | test_discovery.py |
| FR-003 | test_discovery.py, test_export.py |
| FR-004 | test_discovery.py |
| FR-005 | test_offline.py (real + sandbox-exec) |
| FR-006 | test_orientation.py, test_detector_adapter.py, test_detector_cpu.py |
| FR-007 | test_selection.py |
| FR-008 | test_selection.py, test_review_policy.py |
| FR-009 | test_review_policy.py, test_export.py |
| FR-010 | test_cropping.py, test_cropping_modes.py |
| FR-011 | test_cropping.py |
| FR-012 | test_cropping_modes.py |
| FR-013 | test_cropping_modes.py, test_cli_options.py |
| FR-014 | test_export.py |
| FR-015 | test_export.py, test_orientation.py |
| FR-016 | test_export.py, test_review_policy.py |
| FR-017 | test_manifest.py |
| FR-018 | test_manifest.py, test_cancel.py |
| FR-019 | test_cancel.py, test_cli_basic.py, test_recovery.py |
| FR-020 | test_batch_failures.py, test_process_basic.py |
| FR-021 | test_cancel.py (incluye SIGINT real) |
| FR-022 | una imagen activa en processing.py; volumen real pendiente T043 |
| FR-023 | test_config.py, test_cli_options.py |
| FR-024 | pendiente de evaluación del propietario T042 |
| FR-025 | docs/dependencias.md, docs/modelos.md; uso personal confirmado |
| SC-001 | test_export.py, test_discovery.py |
| SC-002 | test_cropping.py, test_cropping_modes.py |
| SC-003 | test_selection.py, test_review_policy.py |
| SC-004 | test_manifest.py, test_cancel.py, test_recovery.py, test_batch_failures.py |
| SC-005 | pendiente de evento real T043 |
| SC-006 | offline real verificado; muestra de carreras pendiente T042 |
| SC-007 | pendiente valoración estética del propietario T042 |
| SC-008 | manifiesto/report implementados; revisión con propietario pendiente T042 |

## Pendientes de aceptación

No hay fotografías privadas disponibles en este chat. La evaluación con 30–50 fotos y la
medición con 2.000–3.500 fotos reales no se ejecutaron. Se harán con el propietario; no se
simulan como completadas ni se confunden los tests con aceptación estética o rendimiento.

## Refinamiento de la muestra — metadatos y focal

Se sustituyó la pérdida advertida de MakerNotes por conservación estricta. Los bloques JPEG
APP/COM originales se copian completos. ExifTool actualiza solo orientación, dimensiones,
miniatura y referencias estructurales permitidas; se comparan los demás campos y los bloques.
La previsualización MPF de Canon se verifica además binariamente. Una muestra sintética MPF
cubre tanto la conservación correcta como el rechazo seguro cuando no es verificable.

Pruebas de focal: 69,9 mm conserva contexto; 70 mm activa protagonismo; ausencia de focal
conserva contexto; resolución mínima impide acercamiento excesivo. Objetivo aceptado: 75 %
de altura (aproximadamente 70–80 %), sin ampliar ni cortar la región protegida.

La muestra privada de 10 fotos se reprocesó a un trabajo nuevo: 10 exportadas, 0 errores,
4 recortes verificados, 1 sin cambios y 5 copias para revisión por ambigüedad. Los originales
conservaron sus hashes. Los datos y tiempos por archivo quedan solo en la carpeta privada.
Este resultado no sustituye la valoración estética ni la muestra mayor de T042/T043.
