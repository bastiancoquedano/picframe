# Implementation Plan: Picframe — sujetos generales

**Branch**: main | **Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)

## Summary
Ampliar selección y composición existentes; categorías explícitas, estrategias dominante/grupo/manual,
protección de conjuntos geométricos y marca Picframe. No cambiar pesos ni añadir dependencias.

## Technical Context
**Language/Version**: Python 3.11 y entorno bloqueado existente.
**Primary Dependencies**: Ultralytics/YOLO11n local, Pillow, ExifTool, PySide6 Essentials y PyInstaller existentes.
**Storage**: configuración inmutable, caché por firma y manifiesto v1 con campos aditivos.
**Testing**: pytest/pytest-qt, ruff, detector real opcional, bundle offline con datos sintéticos.
**Target Platform**: macOS arm64 local. **Project Type**: escritorio y CLI.
**Performance Goals**: inferencia única por imagen; exportación revisada sin repetirla; trabajo en QThread.
**Constraints**: privacidad, originales, metadatos estrictos, aspecto/resolución, incertidumbre explícita.
**Scale/Scope**: personas, clases COCO animales 14–23 y vehículos 1–8; sin clases personalizadas arbitrarias.

## Constitution Check
Antes/después: conforme. Dominante es política explícita con umbral de ventaja; no asume identidad
por tamaño. Grupo es selección explícita autorizada ahora. Marca actualizada sin cambiar principios.
T042/T043 y evaluación fotográfica siguen pendientes. No hay nuevas licencias/dependencias.

## Project Structure
core/categories.py: catálogo y clases auxiliares; core/subjects.py: candidatos y asociaciones geométricas.
core/selection.py: puntuación previa más políticas dominante/grupo; core/cropping.py: composición
no humana por eje limitante, sin referencia anatómica. core/processing.py: caja y miembros auditados.
config.py/cli/main.py: opciones; ui/{window,decisions,preview}.py: controles y revisión.
packaging/raceframe.spec y scripts/build_macos.py: Picframe.app. Mantener módulo raceframe y alias CLI
para compatibilidad; distribución y comandos preferentes picframe. Repositorio renombrado en GitHub,
carpeta local histórica conservada para no romper referencias del entorno.

## Phase 0 — Investigación
Investigación delegada completada; ver research.md. No preguntas técnicas pendientes.

## Phase 1 — Diseño
Ver data-model.md, contracts/subjects.md y quickstart.md. Detecciones conservan clase; selecciones
usan miembros y caja conjunta. Asociaciones con múltiples opciones fuerzan revisión automática;
selección manual protege unión de todas las parejas plausibles y registra incertidumbre.

## Complexity Tracking
Sin excepciones. Marca solo producto/distribución; no reescribir imports ni mover checkout activo.

## Corrección: modo Automático y selección múltiple

Config añade subject_categories opcional (tupla canónica) y active_categories; subject_category
sigue como fallback para configuraciones anteriores. Detectar unión de clases y compañeros.
Deduplicar candidatos por member_ids para que un conjunto no compita consigo mismo en mixto.
Ventana reemplaza combo por Automático inicial, resumen de tres categorías y casillas al
personalizar. CLI añade --auto-subjects y --subject-categories; mutuamente excluyentes con singular.
Pruebas antes de modificar: lote mixto, exclusión personalizada, caché, deduplicación, lista vacía,
normalización/compatibilidad. Sin nuevas dependencias ni investigación técnica pendiente.
