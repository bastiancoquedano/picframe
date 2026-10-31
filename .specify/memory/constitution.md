<!--
Sync Impact Report
Version change: plantilla sin ratificar → 1.0.0 (adopción inicial).
Modified principles: cinco marcadores de plantilla sustituidos por ocho principios del proyecto.
Added sections: Restricciones del producto; Flujo y controles de calidad.
Removed sections: ninguna sección de gobierno; eliminados ejemplos y marcadores de plantilla.
Follow-up TODOs: ninguno en la constitución. Decisiones de producto diferidas a clarificación.
Dependent templates: sin cambios; leen esta constitución durante su ejecución.
-->
# Raceframe Constitution

## Core Principles

### I. Privacidad y procesamiento local

Las fotografías, detecciones y metadatos DEBEN procesarse y permanecer en el computador
del usuario. La aplicación NO DEBE subirlos a servicios externos ni introducir telemetría
que los incluya. Tras instalar dependencias y disponer de los pesos locales, analizar y
exportar DEBE funcionar sin conexión. Toda descarga necesaria DEBE distinguirse del
procesamiento de fotografías y documentarse.

### II. Originales inmutables y exportación segura

Ninguna operación DEBE modificar, borrar o sobrescribir archivos originales.
La exportación DEBE escribir en un destino independiente, prevenir colisiones y rechazar
configuraciones que reintroduzcan resultados en el árbol de entrada recursivo.
Las escrituras interrumpidas NO DEBEN presentarse como resultados exitosos.
Los errores individuales DEBEN registrarse sin invalidar el resto del lote.

### III. Integridad del sujeto y conservación del encuadre

El motor DEBE priorizar la integridad visible del sujeto sobre el centrado perfecto.
DEBE conservar el tipo de plano existente, mantener la relación de aspecto original por
defecto y preservar el máximo contexto compatible con el modo y las restricciones elegidos.
NO DEBE deformar, generar píxeles, ampliar el lienzo ni forzar recortes agresivos cuando
la geometría o la confianza no los justifiquen. Un sujeto ya centrado DEBE conservarse
preferentemente sin cambios. Las limitaciones de proteger extremidades con cajas de
detección DEBEN documentarse, sin prometer garantías que el detector no ofrece.

### IV. Incertidumbre explícita y revisión humana

La selección del protagonista DEBE considerar una puntuación configurable y documentada;
NO DEBE asumir que la persona más grande es siempre el sujeto principal.
Ambigüedad, baja confianza y ausencia de detecciones DEBEN tener estados explícitos y
una política conservadora. El usuario DEBE poder revisar resultados inciertos; la selección
alternativa y el ajuste manual pueden incorporarse progresivamente según la fase aprobada.
Cada imagen DEBE contar con un registro auditable de detecciones, selección, recorte,
estado, advertencias y errores, conforme al contrato que se defina durante la planificación.

### V. Modularidad, simplicidad y mantenibilidad

La geometría de recorte NO DEBE depender de Qt ni cargar YOLO para poder probarse.
El detector DEBE poder reemplazarse y el selector DEBE probarse de forma independiente.
La exportación DEBE separarse de la orquestación. CLI e interfaz DEBEN compartir el núcleo.
El proyecto DEBE usar módulos con responsabilidades claras, tipado razonable y dependencias
justificadas. NO DEBE introducir microservicios ni abstracciones sin una necesidad concreta.
La estructura definitiva DEBE justificarse durante la planificación, sin confundir carpetas
reservadas durante el bootstrap con una arquitectura aprobada.

### VI. Calidad verificable y validación fotográfica

Cada incremento funcional DEBE acompañarse de pruebas apropiadas a sus riesgos.
La geometría DEBE cubrir centrado, bordes, distintos planos, orientaciones y proporciones;
la integración DEBE cubrir EXIF, entradas dañadas, colisiones, cancelación y conservación
de originales. Linting, formato y pruebas aplicables DEBEN pasar antes de aceptar el incremento.
El MVP NO DEBE declararse validado únicamente porque el código ejecute: requiere evaluar
30–50 fotografías reales y documentar selección del sujeto, integridad visible, composición
y necesidad de intervención manual con el propietario.

### VII. Procesamiento robusto y mediciones honestas

Los lotes DEBEN usar memoria acotada al trabajo en curso y NO DEBEN mantener todas las
fotografías originales en memoria. La interfaz DEBE continuar respondiendo durante análisis
y exportación. El proceso DEBE ofrecer progreso, cancelación y resultados por fotografía.
La aceleración DEBE disponer de alternativa CPU. Toda afirmación de rendimiento DEBE
incluir mediciones reales y condiciones del equipo; las estimaciones NO DEBEN presentarse
como resultados comprobados.

### VIII. Desarrollo incremental dirigido por especificaciones

El proyecto DEBE seguir el flujo oficial de GitHub Spec Kit: constitución, especificación,
clarificación, planificación, tareas e implementación. Las ambigüedades importantes DEBEN
resolverse con el propietario antes de implementar. Los cambios DEBEN ser pequeños,
verificables y documentados en español. El agente DEBE ejecutar el trabajo técnico autorizado,
comunicar limitaciones reales y NO DEBE afirmar acciones que no haya verificado.
La aprobación del bootstrap NO implica aprobación de especificación o planificación.

## Restricciones del producto

- Plataforma inicial: macOS Apple Silicon; aplicación local de escritorio con Python.
- MVP: JPG/JPEG; RAW CR3, PNG, TIFF, poses, dorsales y Lightroom quedan para futuras fases.
- Herramientas previstas por el propietario: uv, pytest, ruff, Git y GitHub Spec Kit.
- Tecnologías solicitadas para evaluar en el plan: Ultralytics YOLO, OpenCV, Pillow,
  PySide6/Qt y aceleración MPS con alternativa CPU.
- Versiones, pesos, compatibilidad y licencias DEBEN evaluarse antes de adoptar dependencias
  de ejecución o comprometer una distribución comercial.
- La instalación de desarrollo NO define por sí sola la arquitectura ni valida la aplicación.
- Las fotografías privadas y los pesos de modelos NO DEBEN incorporarse al historial Git.

## Flujo y controles de calidad

1. Completar bootstrap y esta constitución; presentar evidencias del entorno y decisiones pendientes.
2. Esperar aprobación explícita del propietario antes de especificación funcional y planificación.
3. Especificar el primer incremento CLI con historias, escenarios y criterios de aceptación;
   clarificar las decisiones importantes antes de implementar.
4. Planificar contratos, arquitectura, dependencias y pruebas; descomponer en tareas verificables.
5. Implementar primero el motor CLI, validar fotografías reales, desarrollar la interfaz,
   optimizar y preparar distribución, siguiendo las fases de la idea original.
6. Revisar cada incremento contra esta constitución y sus criterios de aceptación. Registrar
   comprobaciones ejecutadas, resultados y limitaciones; justificar cualquier excepción.

## Governance

Esta constitución gobierna las decisiones del proyecto. Cada especificación, plan y revisión
DEBE comprobar su cumplimiento. Una excepción DEBE documentar alcance, motivo, riesgos
y mitigaciones, y recibir aprobación del propietario antes de implementarse.

Los cambios de principios DEBEN proponer su justificación y obtener aprobación del propietario.
Cada enmienda DEBE actualizar el informe de impacto, la fecha y la versión semántica:
MAJOR para retirar o redefinir incompatiblemente principios; MINOR para añadir o ampliar
obligaciones; PATCH para aclaraciones sin cambio de obligaciones. Los artefactos afectados
DEBEN revisarse durante su flujo correspondiente; NO DEBEN modificarse plantillas oficiales
como efecto secundario de redactar la constitución.

La versión 1.0.0 es la constitución inicial redactada a partir de los principios solicitados.
No autoriza el paso a especificación ni implica aceptación del MVP por el propietario.

**Version**: 1.0.0 | **Ratified**: 2026-10-31 | **Last Amended**: 2026-10-31
