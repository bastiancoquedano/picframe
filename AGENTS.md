# Instrucciones de Raceframe

- Trabajar y documentar en español. Nombre del producto y paquete: Raceframe / raceframe.
- Leer `.specify/memory/constitution.md` antes de modificar el proyecto.
- Usar el flujo oficial de GitHub Spec Kit y las habilidades de `.agents/skills/`.
- Bootstrap y constitución completados; el propietario aprobó avanzar el 2026-10-31.
- Especificación y clarificación cerradas el 2026-11-01; plan técnico y contratos redactados.
- Uso personal confirmado; fotografías inciertas: copiar bytes sin cambios y marcar revisión.
- Tareas generadas en specs/001-reencuadre-cli/tasks.md; seguir sus dependencias y no saltar validación.
- El propietario autorizó usar https://github.com/bastiancoquedano/raceframe para subir cambios.
- Publicar solo código/documentación revisados, sin fotos privadas, pesos, credenciales ni entornos.
- La aprobación de avance ya fue recibida; no volver a pedirla para redactar la especificación.
- Funcionalidad activa: `specs/001-reencuadre-cli/`; leer spec.md y plan.md antes de generar tareas.
- No implementar motor, interfaz ni funcionalidades antes de completar las etapas aprobadas.
- La idea fuente está en `docs/idea-original.md`; conservarla como referencia histórica.
- CLI implementado: detección local, selección, modos, exportación, diario, cancelación y reportes.
- Progreso: 45/47 tareas; T042/T043 pendientes de fotos y evaluación del propietario, reservadas por él.
- No afirmar validación fotográfica ni rendimiento real hasta completar esos pasos.
- Entorno completo: uv sync --locked --extra detector. Usar --no-sync al ejecutar para conservar el extra.
- Pesos en models/ excluidos de Git; configuración de desarrollo en .runtime/ también excluida.
- No modificar fotografías originales ni incorporar fotografías privadas al repositorio.
- No descargar pesos ni instalar dependencias de visión hasta evaluar su versión y licencias.
- Registrar resultados verificables. No presentar un entorno configurado como un MVP validado.

- Metadatos obligatorios: usar ExifTool y verificar antes de publicar recortes; no degradar a advertencia.
- Política por focal real >=70 mm: ocupación objetivo 0,75 y lado largo mínimo 3000 px, configurables.
- Con focal menor o ausente, conservar contexto. Las fotos ambiguas siguen copiándose completas.
