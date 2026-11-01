# Guía de validación del CLI implementado

El agente puede operar estos pasos desde el chat, sin que el propietario use una terminal.

1. `uv sync --locked --extra detector` para el entorno completo.
2. `uv run --no-sync python scripts/prepare_model.py` prepara pesos oficiales explícitamente.
   En el Mac de desarrollo ya están preparados; el script verifica el archivo existente.
3. `uv run --no-sync raceframe --version` comprueba el entry point.
4. Ejecutar lint/formato y `RACEFRAME_TEST_MODEL="$PWD/models/yolo11n.pt" uv run --no-sync pytest`.
5. Con permiso sobre la carpeta privada elegida, ejecutar process con destino independiente.
6. Revisar manifest.json y originales/salidas junto al propietario; no publicar fotografías ni rutas.
7. Medir un evento real cuando se disponga de él; ver docs/rendimiento.md.

```sh
uv run --no-sync raceframe process /ruta/entrada --output /ruta/salida --model models/yolo11n.pt
uv run --no-sync raceframe report /ruta/salida/job-UUID
uv run --no-sync raceframe report /ruta/salida/job-UUID --recover
```

Resultado esperado: subdirectorio exclusivo, fotografías completas, inventario, diario y
manifiesto. Inciertas: copia íntegra y revisión. Dañadas: error individual y siguiente foto.
Cancelación: 130 y estado cancelled, sin comenzar otra imagen tras reconocerla.
Recuperación: trabajo inactivo, hashes comprobados, informe nuevo sin sobrescritura ni reanudación.

Contratos: [CLI](contracts/cli.md), [manifiesto](contracts/manifest.md),
[esquema JSON](contracts/manifest.schema.json), [datos](data-model.md).
Evidencias: [validación](../../docs/validacion-cli.md).
Evaluación fotográfica y evento grande pendientes por indicación del propietario.
