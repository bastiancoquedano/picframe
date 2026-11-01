# Implementation Plan: Interfaz de escritorio

**Branch**: main | **Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)

## Summary

Interfaz Qt Widgets en español, oscura, con análisis/revisión y exportación separados.
Reutilizar exactamente el núcleo y sus reglas, sin clasificación por espalda ni grupos automáticos.

## Technical Context

**Language/Version**: Python 3.11, paquete existente.
**Primary Dependencies**: PySide6 6.12.0; pytest-qt 4.5.0 (desarrollo); PyInstaller 6.22.3 (build).
**Storage**: análisis y decisiones en memoria, inventario/diario/manifiesto del núcleo para exportación.
**Testing**: pytest-qt offscreen, detector simulado, regresión CLI, apertura nativa y bundle offline.
**Target Platform**: macOS arm64 del propietario. CPU/MPS según motor probado.
**Project Type**: aplicación local Qt y .app; CLI conservada.
**Performance Goals**: ventana con eventos procesándose durante trabajo, una foto activa y previews reducidos.
**Constraints**: recursos locales, originales inmutables, metadatos estrictos, cancelación cooperativa.
**Scale/Scope**: un trabajo por ventana; sin persistencia de historial, cuentas, RAW ni nuevas clasificaciones.

## Constitution Check

Antes y después del diseño: privacidad local, seguridad de originales y geometría pura conformes.
La UI no calcula reglas alternativas: llama al mismo motor y exportador. Caché usa firma de entrada
y configuración; rechaza resultados obsoletos. La muestra pequeña no completa T042/T043.
No se requieren excepciones. Verificar ejecución y metadatos durante pruebas, no presumirlos.

## Project Structure

### Documentation (this feature)

spec.md, plan.md, research.md, data-model.md, contracts/ui.md, quickstart.md, tasks.md.

### Source Code

src/raceframe/ui/__main__.py: arranque.
src/raceframe/ui/window.py: controles y estado de ventana.
src/raceframe/ui/workers.py: trabajo asincrónico y análisis.
src/raceframe/ui/preview.py: imagen, overlays y selección/rectángulo.
src/raceframe/ui/decisions.py: selección manual, geometría de drag y validaciones.
src/raceframe/ui/resources.py: localizar pesos y herramientas en source/bundle.
src/raceframe/core/processing.py: separar análisis compartido y exportar decisiones vigentes.
packaging/raceframe.spec y scripts/build_macos.py: bundle local reproducible.
tests/unit y tests/integration: decisiones, caché, workers y widgets.

**Structure Decision**: Qt queda bajo ui/. Core no importa Qt. Analizar no escribe JPEG;
exportar usa decisiones revisadas con firmas vigentes, sin repetir inferencia. Modelo preparado
una vez y usado secuencialmente. Al cerrar durante tarea se cancela y se espera finished.

## Complexity Tracking

Sin excepciones. No introducir servidor, base de datos ni motor paralelo de recorte.
