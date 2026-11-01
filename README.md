# Raceframe

Prototipo CLI para mejorar localmente el encuadre de fotografías deportivas JPG/JPEG en macOS
Apple Silicon. Detecta personas, selecciona un protagonista, calcula recortes conservadores y
exporta a una carpeta independiente, sin modificar originales.

## Estado actual

La implementación técnica del CLI está terminada: **42/44 tareas completadas**.
Las dos tareas pendientes son evaluación con 30–50 fotografías reales y medición de un evento
completo; el propietario las realizará con ayuda del agente. Todavía no se declara el MVP
fotográficamente validado. La interfaz gráfica pertenece a la siguiente fase del proyecto.

Incluye:

- YOLO11n local, CPU predeterminada y MPS/auto opcional con preparación comprobada.
- Selección explicable y copias byte por byte ante ambigüedad o baja confianza.
- Modos conservador, equilibrado y cerrado; proporción original, 3:2 y 4:5.
- Recortes que priorizan región del sujeto, márgenes factibles y conservación de contexto.
- EXIF orientado, perfil ICC, calidad JPEG configurable y advertencias de metadatos no garantizados.
- Progreso, cancelación, errores por archivo, manifiesto JSON y recuperación de trabajos interrumpidos.
- Publicación de archivos completos sin reemplazo; entradas originales abiertas solo para lectura.

El detector no identifica infaliblemente al protagonista ni todas sus extremidades.
Las proporciones explícitas significan ancho:alto; si no existe un recorte seguro, se copia el
original y se marca para revisión. PNG, TIFF, CR3, poses, dorsales y GUI quedan fuera del CLI.

## Operación desde el chat

El propietario puede indicar una carpeta y pedir al agente que la procese. No necesita usar
terminal o editor. Antes de procesar sus fotos, revisaremos juntos origen, destino y parámetros.
Los comandos siguientes son referencias reproducibles para el agente.

## Preparación del entorno

Python 3.11.16 y uv. El Mac de desarrollo ya tiene dependencias y pesos preparados.

```sh
uv sync --locked --extra detector
uv run --no-sync python scripts/prepare_model.py
uv run --no-sync raceframe --version
```

La preparación descarga dependencias/pesos explícitamente. El procesamiento posterior no usa
servicios externos ni descarga pesos. Véase [modelos](docs/modelos.md) y [dependencias](docs/dependencias.md).
Para probar solo geometría y detector simulado, `uv sync --locked` sin el extra basta.

## Procesamiento

```sh
uv run --no-sync raceframe process /ruta/entrada --output /ruta/salida --model models/yolo11n.pt
uv run --no-sync raceframe process /ruta/entrada --output /ruta/salida --model models/yolo11n.pt --mode balanced --aspect 4:5 --device auto
uv run --no-sync raceframe report /ruta/salida/job-UUID
uv run --no-sync raceframe report /ruta/salida/job-UUID --recover
```

Cada trabajo crea un subdirectorio exclusivo `job-UUID`. Por defecto, el destino propuesto es
`Raceframe_Output`, hermano de la entrada. Se rechaza destino igual a entrada o dentro de una entrada recursiva.
Sin recursión se permite una subcarpeta de salida, excluida del inventario. Dentro del trabajo, nombres repetidos reciben sufijos; nunca se sobrescriben salidas.
Los volúmenes sin publicación exclusiva mediante enlaces duros se rechazan antes de exportar.

Opciones: `--recursive`, `--mode conservative|balanced|tight`, `--aspect original|3:2|4:5`,
`--margin` (0–0,5), `--quality` (1–95), `--device cpu|mps|auto`, `--config ARCHIVO_JSON`.
Argumentos explícitos prevalecen sobre archivo y valores por defecto. Pesos y umbrales avanzados
se configuran mediante JSON y quedan en el manifiesto; consultar [plan](specs/001-reencuadre-cli/plan.md).

Ctrl+C cancela cooperativamente: puede terminar la fotografía activa antes de detenerse.
Código 0: completado (incluye copias para revisión); 1: completado con errores; 2: preparación
inválida; 3: fallo global; 130: cancelado. Progreso y diagnósticos a stderr, resumen JSON a stdout.
`report --recover` requiere trabajo inactivo, verifica salidas preparadas y escribe un informe
nuevo sin reanudar ni borrar archivos. Un estado interrumpido no es éxito.

## Calidad y límites de validación

```sh
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest
RACEFRAME_TEST_MODEL="$PWD/models/yolo11n.pt" uv run --no-sync pytest
```

Sin RACEFRAME_TEST_MODEL las pruebas reales se omiten explícitamente; no se consideran aprobadas.
Una ejecución sin pruebas tampoco valida el producto. CI ejecuta calidad y pruebas sintéticas;
inferencia real y bloqueo de red se comprobaron por separado en el Mac.
[Resultados y cobertura](docs/validacion-cli.md), [evaluación pendiente](docs/evaluacion-fotografica.md)
y [medición pendiente](docs/rendimiento.md).

## Spec Kit

Flujo: constitución → especificación → clarificación → plan → tareas → implementación → convergencia.
Specify CLI 1.0.1, integración Codex. [Constitución](.specify/memory/constitution.md),
[especificación](specs/001-reencuadre-cli/spec.md), [plan](specs/001-reencuadre-cli/plan.md)
y [tareas](specs/001-reencuadre-cli/tasks.md). La aceptación/convergencia completa espera la
validación real; las casillas pendientes no se completan por pasar pruebas sintéticas.

Repositorio: [bastiancoquedano/raceframe](https://github.com/bastiancoquedano/raceframe).
No se incluye una licencia propia de distribución ni fotografías/modelos/entornos en Git.
