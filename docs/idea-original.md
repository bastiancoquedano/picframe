# RaceFrame — Especificación maestra del proyecto

## 1. Rol y metodología

Actúa como un equipo de ingeniería de software compuesto por:

- Senior Python Developer.
- Software Architect.
- Computer Vision Engineer.
- macOS Desktop Application Developer.
- QA Automation Engineer.

Quiero que desarrolles una aplicación llamada **RaceFrame**, utilizando **GitHub Spec Kit** y la metodología **Specification-Driven Development (SDD)**.

Quiero interactuar contigo desde ChatGPT Desktop. Debes encargarte de la creación del proyecto, configuración del entorno, arquitectura, implementación, pruebas y documentación, siempre dentro de las capacidades y permisos disponibles.

No quiero utilizar manualmente VSCode, Codex ni la terminal para desarrollar.

Trabaja en español, ejecuta las tareas que puedas realizar y solicita mi intervención únicamente cuando sea necesaria para autorizar acciones, resolver decisiones importantes o validar resultados.

No afirmes haber ejecutado acciones que no hayas podido realizar.

---

## 2. Contexto y problema

Soy fotógrafo deportivo y utilizo una Canon EOS R50 para fotografiar principalmente maratones y carreras.

Durante un evento puedo capturar entre 2.000 y 3.500 fotografías.

Muchas fotografías tienen buena exposición y enfoque, pero el corredor principal aparece desplazado horizontalmente, por lo que debo recortar manualmente cada imagen para mejorar su composición.

Quiero automatizar ese proceso.

### Ejemplo

Una fotografía horizontal muestra a un corredor completo desplazado hacia la izquierda.

La aplicación debe detectar al corredor y recortar la fotografía para que aparezca centrado, manteniendo el máximo contexto posible.

Si el corredor aparece de cintura hacia arriba, el programa debe respetar ese plano.

**El objetivo es mejorar el encuadre existente, no convertir todas las fotografías a un mismo tipo de plano.**

---

## 3. Objetivo principal

Desarrollar una aplicación de escritorio para macOS que permita:

1. Seleccionar una carpeta de fotografías.
2. Analizar automáticamente cada fotografía mediante inteligencia artificial.
3. Detectar a las personas presentes.
4. Identificar al corredor principal.
5. Calcular un recorte inteligente que lo centre.
6. Preservar el máximo contexto original posible.
7. Previsualizar el resultado.
8. Procesar cientos o miles de fotografías.
9. Exportar los resultados a una carpeta independiente.

La aplicación debe funcionar completamente en el computador del usuario, sin necesidad de subir fotografías a servicios externos.

---

## 4. Tecnologías

### Lenguaje principal

**Python 3**, utilizando una versión estable compatible con las dependencias.

### Visión computacional

**Ultralytics YOLO**, inicialmente con un modelo preentrenado para detección de personas.

Evaluar la versión y el tamaño del modelo más adecuados según rendimiento, precisión y licenciamiento.

Considerar detección de poses humanas en una fase posterior si permite proteger mejor las extremidades durante el recorte.

### Procesamiento de imágenes

**OpenCV** para:

- Manejo de coordenadas.
- Cálculos geométricos.
- Manipulación de regiones.
- Operaciones de recorte.

**Pillow** para:

- Apertura y exportación de imágenes.
- Gestión de formatos.
- Corrección de orientación EXIF.
- Conservación de metadatos compatibles.
- Control de calidad de exportación.

### Interfaz gráfica

**PySide6 / Qt**, para desarrollar una aplicación de escritorio nativa en experiencia de uso, aunque construida con Python.

### Herramientas adicionales

- `uv`: gestión de dependencias y entorno Python.
- `pytest`: pruebas automatizadas.
- `ruff`: linting y formato.
- `Git`: control de versiones.
- `GitHub Spec Kit`: especificaciones y planificación.

### Plataforma

macOS con procesadores Apple Silicon.

Evaluar aceleración mediante PyTorch MPS y alternativas como Core ML cuando corresponda.

La aplicación debe funcionar en CPU si la aceleración no está disponible.

---

## 5. Selección de carpetas

La aplicación debe disponer de una interfaz que permita:

### Carpeta de origen

- Seleccionar una carpeta mediante el explorador de archivos de macOS.
- Mostrar la ruta seleccionada.
- Contabilizar fotografías compatibles.
- Permitir configurar si se incluyen subcarpetas.
- Ignorar archivos no compatibles.
- Informar archivos dañados o ilegibles.

### Carpeta de destino

- Seleccionar una carpeta independiente.
- Proponer por defecto una carpeta llamada `RaceFrame_Output`.
- Evitar sobrescribir archivos existentes.
- No modificar nunca los archivos originales.
- Advertir si el destino coincide con el origen o está dentro de un árbol de entrada recursivo.

### Formatos

MVP:
- JPG.
- JPEG.

Futuras versiones:
- Canon CR3.
- PNG.
- TIFF.

La compatibilidad futura debe considerarse en la arquitectura, pero no es obligatorio implementarla en el MVP.

---

## 6. Detección de corredores

Cada fotografía debe analizarse utilizando YOLO.

### Proceso

1. Cargar la fotografía.
2. Normalizar su orientación.
3. Ejecutar detección de personas.
4. Obtener bounding boxes y niveles de confianza.
5. Analizar las personas detectadas.
6. Seleccionar al corredor principal.
7. Calcular el recorte apropiado.

### Selección del sujeto principal

La selección debe considerar:

- Cercanía al centro.
- Tamaño relativo.
- Confianza del detector.
- Visibilidad de la persona.
- Relación con otros corredores.

No debe asumir que la persona más grande es siempre el sujeto principal.

Implementar una estrategia de puntuación configurable y documentada.

Si hay varias personas con puntuaciones similares, la fotografía debe marcarse como ambigua.

### Casos especiales

- Una sola persona.
- Varias personas.
- Corredores parcialmente ocultos.
- Personas en segundo plano.
- Corredores agrupados.
- Ausencia de personas detectadas.
- Detecciones de baja confianza.

Cuando no exista suficiente confianza para identificar al protagonista, no aplicar un recorte agresivo.

---

## 7. Motor de recorte inteligente

Este es el componente más importante del proyecto.

### Principio fundamental

**Preservar el encuadre original tanto como sea posible mientras se mejora la posición del sujeto.**

### Requisitos

- Mantener la relación de aspecto original por defecto.
- Admitir proporciones 3:2 y 4:5.
- Permitir fotografías horizontales y verticales.
- Centrar al corredor cuando sea geométricamente posible.
- Evitar cortar cabeza, pies y extremidades visibles.
- Mantener márgenes de seguridad configurables.
- Preservar contexto ambiental.
- No deformar la fotografía.
- No inventar píxeles mediante IA generativa.
- No ampliar artificialmente el lienzo.

### Restricción geométrica

Cuando el corredor está muy cerca del borde, puede no existir un recorte capaz de centrarlo sin cortar parte de su cuerpo.

En esos casos, priorizar la integridad del sujeto y aceptar un centrado imperfecto.

Cuando el corredor ya está correctamente centrado, conservar preferentemente la fotografía sin cambios.

### Modos de recorte

**Modo conservador**

- Mínimo recorte.
- Máximo contexto.
- Correcciones suaves.
- Adecuado para fotografía deportiva con entorno.

**Modo equilibrado**

- Centrado más evidente.
- Márgenes moderados.
- Mantiene una composición natural.

**Modo cerrado**

- Recorte más ajustado.
- Mayor protagonismo del corredor.
- Respeta los márgenes de seguridad.

Los tres modos deben compartir el mismo motor geométrico, variando sus parámetros.

### Limitaciones que deben documentarse

El modelo de detección no garantiza identificar siempre al corredor correcto ni localizar perfectamente todas sus extremidades.

La aplicación debe registrar incertidumbre y permitir revisión manual.

---

## 8. Interfaz gráfica

Diseñar una interfaz moderna, minimalista y sencilla, preferentemente con tema oscuro.

### Pantalla principal

Debe incluir:

- Nombre y versión de RaceFrame.
- Selector de carpeta de origen.
- Selector de carpeta de destino.
- Contador de imágenes encontradas.
- Selector del modo de recorte.
- Selector de relación de aspecto.
- Configuración de márgenes.
- Botón para analizar.
- Botón para procesar.
- Barra de progreso.
- Botón de cancelación.

### Previsualización

Mostrar:

- Fotografía original.
- Fotografía recortada.
- Comparación antes/después.
- Rectángulo de recorte superpuesto.
- Sujeto principal detectado.
- Posibilidad de seleccionar otro corredor.
- Posibilidad de ajustar manualmente el recorte.

Los ajustes manuales pueden implementarse progresivamente después del primer prototipo funcional.

### Resultados

Mostrar:

- Total de fotografías.
- Fotografías procesadas.
- Fotografías sin cambios.
- Fotografías ambiguas.
- Fotografías con errores.
- Tiempo de procesamiento.
- Carpeta de salida.

La interfaz no debe congelarse durante el procesamiento.

---

## 9. Procesamiento por lotes

La aplicación debe soportar grandes volúmenes de fotografías.

### Requisitos

- Procesamiento secuencial inicial.
- Procesamiento en segundo plano respecto de la interfaz.
- Gestión eficiente de memoria.
- No mantener todas las fotografías originales cargadas simultáneamente.
- Continuar cuando una fotografía individual falle.
- Permitir cancelar el proceso.
- Informar progreso.
- Registrar resultados por fotografía.
- Evitar resultados incompletos que parezcan exitosos.

### Optimización

Evaluar:

- Inferencia a resolución reducida.
- Transformación correcta de coordenadas a resolución original.
- Caché de detecciones.
- Procesamiento por lotes del modelo cuando aporte mejoras.
- Aceleración Apple Silicon.
- Separación entre inferencia y exportación.

No establecer cifras de rendimiento sin mediciones reales.

---

## 10. Exportación

### Requisitos

- Guardar resultados en carpeta independiente.
- Conservar el nombre base original.
- Evitar colisiones.
- Mantener calidad JPEG configurable.
- Preservar metadatos EXIF relevantes.
- Corregir la orientación correctamente.
- No eliminar silenciosamente información importante.
- Registrar imágenes que no pudieron exportarse.

### Información adicional

Guardar un manifiesto JSON con:

- Nombre de archivo.
- Dimensiones originales.
- Bounding boxes detectadas.
- Sujeto seleccionado.
- Coordenadas del recorte.
- Dimensiones finales.
- Modo aplicado.
- Confianza de detección.
- Estado del procesamiento.
- Advertencias y errores.

Este manifiesto debe permitir auditar resultados y facilitar futuras integraciones.

---

## 11. Arquitectura de software

Separar responsabilidades en módulos.

Propuesta conceptual:

```text
raceframe/
├── .specify/
├── specs/
├── src/
│   └── raceframe/
│       ├── core/
│       │   ├── detection/
│       │   ├── selection/
│       │   ├── cropping/
│       │   └── processing/
│       ├── imaging/
│       ├── export/
│       ├── ui/
│       ├── config/
│       └── cli/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
├── pyproject.toml
├── README.md
└── .gitignore
```

La estructura definitiva debe justificarse durante la planificación con Spec Kit.

### Reglas arquitectónicas

- La lógica de recorte no debe depender de Qt.
- El detector debe poder reemplazarse.
- El selector de sujeto debe poder probarse independientemente.
- La geometría debe poder probarse sin cargar YOLO.
- La exportación debe estar separada del procesamiento.
- No utilizar microservicios.
- Evitar abstracciones innecesarias.
- Aplicar tipado estático cuando sea razonable.

---

## 12. Pruebas y calidad

Implementar pruebas automatizadas para:

- Corredor centrado.
- Corredor a la izquierda.
- Corredor a la derecha.
- Corredor cerca del borde.
- Cuerpo completo.
- Plano medio.
- Varias personas.
- Ausencia de personas.
- Imágenes horizontales.
- Imágenes verticales.
- Diferentes relaciones de aspecto.
- Orientación EXIF.
- Imágenes dañadas.
- Colisiones de nombres.
- Cancelación del procesamiento.
- Conservación de originales.

### Validación con fotografías reales

Utilizar inicialmente entre 30 y 50 fotografías reales de maratón.

Comparar:

- Imagen original.
- Imagen procesada.
- Sujeto seleccionado.
- Integridad del cuerpo.
- Calidad del encuadre.
- Cantidad de fotografías que requieren intervención manual.

No considerar el MVP validado únicamente porque el código se ejecute sin errores.

---

## 13. Metodología Spec Kit

Utilizar el flujo oficial de GitHub Spec Kit.

### Etapa 1 — Constitución

Crear los principios permanentes del proyecto:

- Calidad.
- Privacidad.
- Seguridad de originales.
- Modularidad.
- Pruebas.
- Simplicidad.
- Mantenibilidad.
- Desarrollo incremental.

### Etapa 2 — Especificación

Crear requisitos funcionales, historias de usuario, escenarios y criterios de aceptación.

### Etapa 3 — Clarificación

Identificar decisiones ambiguas y resolverlas conmigo antes de implementar.

### Etapa 4 — Planificación

Definir arquitectura, dependencias, modelo de datos y contratos entre módulos.

### Etapa 5 — Tareas

Dividir el trabajo en tareas pequeñas, verificables y ordenadas.

### Etapa 6 — Implementación

Desarrollar incrementalmente, ejecutar pruebas y validar resultados.

No saltarse las etapas de especificación y planificación.

---

## 14. Fases de desarrollo

### Fase 1 — Bootstrap

- Crear el directorio del proyecto.
- Preparar Git.
- Configurar Python y uv.
- Inicializar Spec Kit.
- Crear documentación inicial.

### Fase 2 — Motor CLI

- Importar fotografías.
- Detectar personas.
- Seleccionar sujeto.
- Calcular recortes.
- Exportar resultados.
- Generar manifiesto JSON.

### Fase 3 — Validación fotográfica

- Probar fotografías reales.
- Analizar errores.
- Ajustar selección de sujetos.
- Refinar geometría.
- Evaluar calidad.

### Fase 4 — Interfaz gráfica

- Crear aplicación PySide6.
- Seleccionar carpetas.
- Previsualizar.
- Configurar parámetros.
- Procesar lotes.
- Revisar imágenes ambiguas.

### Fase 5 — Optimización

- Mejorar rendimiento.
- Optimizar memoria.
- Evaluar aceleración.
- Mejorar gestión de errores.

### Fase 6 — Distribución

- Empaquetar para macOS.
- Gestionar modelos y dependencias.
- Evaluar firma y notarización.
- Revisar licencias comerciales.
- Preparar documentación de instalación.

---

## 15. Funcionalidades futuras

No implementar en el MVP, pero considerar extensibilidad para:

- Fotografías RAW Canon CR3.
- Detección de poses.
- Detección de dorsales.
- Identificación de corredores por dorsal.
- Procesamiento de ciclismo y otros deportes.
- Presets de recorte.
- Procesamiento multicarpeta.
- Integración con Lightroom.
- Exportación de instrucciones de recorte no destructivas.
- Historial de trabajos.
- Reprocesamiento a partir del manifiesto JSON.

---

## 16. Criterios de éxito

El primer prototipo debe poder:

1. Recibir una carpeta con fotografías JPG.
2. Detectar personas automáticamente.
3. Seleccionar un corredor principal razonablemente.
4. Calcular recortes seguros.
5. Conservar el tipo de encuadre original.
6. Exportar fotografías procesadas.
7. No modificar los originales.
8. Registrar imágenes ambiguas y errores.
9. Ejecutar pruebas automatizadas.
10. Procesar una muestra real de 30 a 50 fotografías para evaluación.

El objetivo no es recortar todas las fotografías a cualquier costo, sino producir resultados útiles y seguros.

---

## 17. Instrucciones de ejecución autónoma

Quiero que te encargues de la mayor cantidad posible de trabajo técnico.

Directorio deseado:

`/Users/bastiancoquedano/Proyectos/raceframe`

Antes de trabajar:

1. Verifica si tienes acceso real a ese directorio.
2. Comprueba las herramientas disponibles.
3. Identifica las limitaciones de tu entorno.
4. No asumas acceso al Mac si estás trabajando en un computador remoto.
5. Solicita autorización cuando sea necesaria.
6. No sobrescribas archivos existentes sin confirmación.

Si puedes acceder al entorno, realiza el bootstrap y configura Spec Kit.

Si no puedes acceder directamente, explica la limitación y propone el camino más sencillo para continuar desde ChatGPT Desktop.

No quiero instrucciones genéricas de programación si puedes ejecutar directamente las acciones.

---

## 18. Primera acción solicitada

Comienza con la **Fase 1: Bootstrap y constitución del proyecto**.

Realiza las acciones posibles, verifica los resultados y muéstrame:

- Directorio y estructura creada.
- Estado del entorno Python.
- Estado de Spec Kit.
- Estado de Git.
- Constitución del proyecto.
- Decisiones técnicas pendientes.

**No comiences todavía la implementación completa del motor ni de la interfaz.**

Espera mi aprobación antes de pasar a la especificación funcional y planificación detallada.