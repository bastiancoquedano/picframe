# Guía de validación prevista

Estado: paquete, pruebas de base y --version ya ejecutables. Los comandos process/report
siguen siendo diseño futuro y **todavía no están disponibles**.
Pillow está instalado; YOLO/torch/Qt y los pesos todavía no. El agente ejecutará estos
pasos cuando corresponda; el propietario no necesita usar terminal ni editor.

## Prerrequisitos de implementación

1. Tareas generadas; implementar los contratos pendientes antes de ejecutar process/report.
2. Resolver versiones compatibles con uv, revisar licencias, fijar uv.lock y ejecutar uv sync --locked.
3. Paquete instalable y entry point ya preparados; comprobar uv run raceframe --version.
4. Preparar YOLO11n explícitamente desde origen oficial, registrar URL, licencia y SHA-256.
   No usar un peso recibido de terceros sin procedencia; no incorporarlo a Git.
5. Configurar offline/telemetría antes del import; verificar que no se requiere red.
6. Disponer de fixtures sintéticos y carpeta privada de 30–50 fotos, fuera del repositorio.

## Comprobaciones automatizadas previstas

```sh
uv run ruff check .
uv run ruff format --check .
uv run pytest tests/unit tests/integration
```

Primero geometría y selección con detector simulado: centrado, izquierda/derecha, borde,
plano medio, múltiples personas, ausencia y cajas inválidas; modos anidados y tres proporciones.
Después EXIF 1–8, ICC, etiquetas EXIF conocidas, bloque no verificable con advertencia,
JPEG dañado, colisiones, subcarpetas, symlinks, rutas inseguras, SIGINT, disco lleno y
fallos entre intención/publicación/confirmación. Comparar hashes de originales antes/después.

La inferencia real es una prueba explícita separada que exige pesos locales; no ocultar una
prueba no ejecutada como si hubiera pasado. Ensayar process y report con la red bloqueada,
incluido import del detector. Medir CPU antes de comparar MPS.

## Ejecución prevista sobre fotografías privadas

```sh
uv run raceframe process /ruta/privada/muestra --output /ruta/privada/salidas --model /ruta/local/yolo11n.pt --device cpu
uv run raceframe report /ruta/privada/salidas/job-UUID
```

Resultado esperado: directorio exclusivo, copias/reencuadres completos, inventario, diario y
manifiesto; originales idénticos. Una foto ambigua legible se copia con hash idéntico y marca
de revisión. Un error individual no detiene el siguiente archivo. Revisar estado y contadores,
no únicamente el código de salida. Para SIGINT: 130, estado cancelled, sin falsos éxitos.

Para interrupción abrupta, usar report --recover solo con proceso inactivo y verificar que
un temporal parcial no se confunda con una fotografía exportada.

## Aceptación fotográfica y escala

Comparar 30–50 pares original/salida. Registrar por foto: protagonista correcto, integridad
visible, mejora de composición, advertencias y necesidad de intervención. Revisar al menos
cuerpo completo lateral, plano medio, centrado y borde. Corregir recortes que corten al
protagonista o derivarlos a revisión; el propietario confirma utilidad estética.

Después probar 2.000–3.500 fotos con registro de dispositivo, tiempo, fotos/segundo y RSS máximo.
No declarar velocidad, precisión ni MVP aceptado antes de ejecutar y revisar esos resultados.
