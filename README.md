# Raceframe

Aplicación de escritorio para macOS Apple Silicon que mejorará el encuadre de fotografías
deportivas mediante detección local de personas y recortes conservadores.

## Estado

Fase 1: bootstrap y constitución. Todavía no hay un motor de recorte ni una interfaz ejecutable.
La especificación funcional y la planificación requieren aprobación del propietario antes de comenzar.

## Principios

- Procesar las fotografías localmente y mantener intactos los originales.
- Preservar el tipo de plano, la integridad visible del sujeto y el máximo contexto posible.
- Registrar incertidumbre y facilitar revisión humana.
- Separar geometría, detección, selección, exportación e interfaz.
- Validar con pruebas automatizadas y 30–50 fotografías reales antes de aceptar el MVP.

Constitución completa: [.specify/memory/constitution.md](.specify/memory/constitution.md).
Idea original: [docs/idea-original.md](docs/idea-original.md).
Decisiones pendientes: [docs/decisiones-pendientes.md](docs/decisiones-pendientes.md).

## Entorno de desarrollo

Python 3.11.16, uv y dependencias de desarrollo fijadas en `uv.lock`.
Se ha elegido esta versión porque ya está instalada en el Mac; se revisará su compatibilidad
con las dependencias de visión e interfaz durante la planificación.

Comandos de referencia para el agente; el propietario no necesita ejecutarlos manualmente:

```sh
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

En esta fase no hay pruebas de aplicación: pytest sin pruebas devuelve código 5, no una validación.
No se han instalado dependencias de visión, descargado pesos ni procesado fotografías.

## Spec Kit

Inicializado con Specify CLI 1.0.1, integración `codex` y scripts Bash.
Las habilidades oficiales están en `.agents/skills/` y los artefactos compartidos en `.specify/`.

Secuencia: constitución → especificación → clarificación → plan → tareas → implementación.
Para la siguiente etapa, después de aprobación, usar `$speckit-specify` sobre el primer
incremento CLI. No ejecutar todavía `$speckit-plan` ni `$speckit-implement`.

## Estructura inicial

```text
.agents/skills/         Habilidades oficiales de Spec Kit
.specify/              Constitución, plantillas, scripts y flujo oficial
specs/                 Reservado para futuras especificaciones aprobadas
src/raceframe/         Reservado para el futuro paquete Python
tests/                 Reservado para pruebas unitarias, integración y fixtures sintéticos
docs/                  Idea original, decisiones y registro del bootstrap
pyproject.toml         Configuración inicial del entorno
uv.lock                Resolución reproducible de dependencias de desarrollo
```

No se establece todavía una licencia de distribución para la aplicación.
