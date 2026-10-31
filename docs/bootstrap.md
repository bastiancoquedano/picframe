# Registro de bootstrap — 2026-10-31

## Ubicación y alcance

Proyecto: `/Users/bastiancoquedano/Proyectos/raceframe`.
Creado en el Mac del propietario (Darwin arm64), con acceso de escritura autorizado.
La carpeta de la conversación `/Users/bastiancoquedano/Documents/ChatGPT/Raceframe`
no contiene este proyecto; no se ha duplicado ni movido su repositorio inicial vacío.

Alcance completado: Fase 1 y constitución. No se ha iniciado la especificación funcional,
la planificación detallada, el motor ni la interfaz. El nombre acordado es Raceframe;
la idea original se conserva literalmente, incluyendo su grafía histórica RaceFrame.

## Entorno comprobado

- Python del sistema: 3.9.6, sin modificar.
- Python del proyecto: 3.11.16, instalado previamente mediante uv.
- Entorno aislado: `.venv/` (excluido de Git).
- uv: 0.12.7.
- Specify CLI: 1.0.1, instalado previamente.
- Integración oficial: codex; scripts Bash; habilidades en `.agents/skills/`.
- pytest: 9.2.0; ruff: 0.17.3.
- Dependencias de desarrollo fijadas en `uv.lock`; `uv sync --locked` completado.
- Caché uv usada durante el bootstrap: `/private/tmp/raceframe-uv-cache`.
  Se usó una caché temporal porque la caché global no era escribible desde el sandbox.
- Git inicializado en rama `main`, sin remoto ni publicación externa.

## Constitución

Versión 1.0.0, adopción inicial basada en los principios solicitados.
Se ejecutó el resolvedor oficial `resolve-template.sh constitution-template --json`.
Se aplicó `.agents/skills/speckit-constitution/SKILL.md` solo a la constitución.
No hay hooks de extensión configurados. Las plantillas oficiales no se modificaron.

## Verificaciones ejecutadas

- `specify check`: CLI listo; Codex disponible. No se requieren los otros agentes listados.
- `ruff check --no-cache .`: sin incidencias.
- `ruff format --check --no-cache .`: 20 archivos ya formateados (scripts de Spec Kit).
- Constitución: ocho principios, versión y fechas presentes, sin marcadores pendientes.
- Integración: `codex` registrada en `.specify/integration.json`.
- Idea original: copia comprobada mediante SHA-256.
- `src/` y `tests/`: sin implementación ni pruebas de aplicación.

No se ejecutó una suite de aplicación: todavía no existe. Las comprobaciones anteriores
validan el bootstrap, no la detección, los recortes ni el MVP fotográfico.
No se descargaron pesos, instalaron YOLO/Qt ni procesaron fotografías.

## Próximo paso sujeto a aprobación

Usar `$speckit-specify` para el primer incremento CLI después de la aprobación explícita
del propietario. Resolver las decisiones de `docs/decisiones-pendientes.md` en clarificación
y planificación antes de implementar. No es necesario que el propietario use la terminal.

Referencias oficiales consultadas:
- https://github.com/github/spec-kit
- https://github.github.io/spec-kit/integrations/codex.html
