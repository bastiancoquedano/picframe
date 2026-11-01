# Raceframe

Aplicación de escritorio para macOS Apple Silicon que mejorará el encuadre de fotografías
deportivas mediante detección local de personas y recortes conservadores.

## Estado

Etapa actual de Spec Kit: **implementación**. Primer incremento completado:

- Paquete instalable y comando `raceframe --version` / `--help`.
- Configuración validada, inventario seguro y lectura JPEG con orientación EXIF 1–8.
- Motor geométrico puro en modo conservador y proporción original, con protección de sujeto,
  márgenes, límite de pérdida de contexto y conservación de fotografías ya centradas.
- Pruebas sintéticas de geometría, configuración, orientación y archivos; CI configurada.

Avance: **12/44 tareas**. Todavía no se detectan corredores automáticamente ni se exportan
carpetas: esas capacidades se incorporarán en las siguientes tareas. No hay interfaz gráfica.
Las pruebas de este incremento no sustituyen la validación fotográfica del MVP.

Documentos: [especificación](specs/001-reencuadre-cli/spec.md),
[plan](specs/001-reencuadre-cli/plan.md), [tareas](specs/001-reencuadre-cli/tasks.md)
y [validación del incremento](docs/validacion-cli.md).

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

Python 3.11.16, uv, Pillow 13.0.0, pytest y ruff; dependencias fijadas en `uv.lock`.
Los módulos geométricos no importan Pillow ni bibliotecas de inferencia.

Comandos de referencia para el agente; el propietario no necesita ejecutarlos manualmente:

```sh
uv sync --locked
uv run raceframe --version
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Una ejecución sin pruebas devuelve código 5 y no valida el MVP. Omitir inferencia real tampoco
la da por aprobada. No se han instalado YOLO/torch/Qt ni descargado pesos; las fotografías
usadas por la suite son sintéticas y temporales.

## Spec Kit

Inicializado con Specify CLI 1.0.1, integración `codex` y scripts Bash.
Las habilidades oficiales están en `.agents/skills/` y los artefactos compartidos en `.specify/`.

Secuencia: constitución → especificación → clarificación → plan → tareas → implementación.
Se aplicó `$speckit-specify` al primer incremento CLI tras la aprobación.
Clarificaciones integradas; checklist 16/16; `$speckit-plan` completado documentalmente.
Tareas generadas con `$speckit-tasks`; `$speckit-implement` en curso, con avances verificados.

## Estructura

```text
.agents/skills/         Habilidades oficiales de Spec Kit
.specify/              Constitución, plantillas, scripts y flujo oficial
specs/                 Especificación, plan, contratos y tareas
src/raceframe/         Paquete Python, configuración, geometría y lectura
tests/                 Pruebas unitarias, integración y fixtures sintéticos
docs/                  Idea original, decisiones y registro del bootstrap
pyproject.toml         Paquete instalable y dependencias
uv.lock                Resolución reproducible de dependencias
```

No se establece todavía una licencia de distribución para la aplicación.

Repositorio del proyecto: [bastiancoquedano/raceframe](https://github.com/bastiancoquedano/raceframe).
