# Feature Specification: Reencuadre seguro por lotes — prototipo CLI

**Feature Branch**: `main` (sin rama de funcionalidad; no hay hook Git instalado)

**Created**: 2026-10-31

**Status**: Draft — pendiente de dos clarificaciones del propietario

**Input**: Idea maestra conservada en `docs/idea-original.md`; aprobación del bootstrap
recibida el 2026-10-31. Primer incremento: procesar fotografías deportivas localmente,
seleccionar protagonista, proponer recortes conservadores, exportar y auditar resultados.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Obtener encuadres útiles sin perder originales (Priority: P1)

Como fotógrafo deportivo quiero indicar una carpeta de entrada y otra de salida para
obtener fotografías mejor encuadradas sin alterar mis originales ni cambiar el plano existente.
La interfaz de este incremento es de línea de comandos; el agente puede operarla por mí.

**Why this priority**: Resuelve el trabajo repetitivo que motiva Raceframe y permite evaluar
su utilidad antes de construir la interfaz gráfica.

**Independent Test**: Procesar una carpeta pequeña con protagonistas conocidos y comparar
originales, salidas y registro del trabajo; no requiere interfaz gráfica ni ajustes manuales.

**Acceptance Scenarios**:

1. **Given** una imagen horizontal con corredor completo desplazado a la izquierda o derecha,
   **When** se procesa con una selección fiable, **Then** el recorte reduce el desplazamiento
   horizontal si existe una solución permitida y conserva el sujeto detectado y su margen factible.
2. **Given** una imagen de plano medio, **When** se reencuadra, **Then** se conserva la parte
   visible y no se exige reconstruir el cuerpo completo ni convertir el plano en un retrato cerrado.
3. **Given** un corredor ya centrado y proporción original, **When** se usa el modo conservador,
   **Then** se mantiene el encuadre completo sin volver a comprimir innecesariamente el archivo.
4. **Given** un corredor junto al borde, **When** centrarlo exigiría cortarlo,
   **Then** se prioriza conservar su región visible, aceptando centrado imperfecto o sin recorte.
5. **Given** imágenes verticales u orientadas por sus metadatos, **When** se procesan,
   **Then** las salidas se ven derechas y las regiones registradas corresponden a esa orientación.
6. **Given** un archivo con nombre de salida ya existente, **When** se exporta,
   **Then** se produce un nombre distinto y ninguno de los archivos previos se modifica.

---

### User Story 2 - Conocer qué fotografías requieren revisión (Priority: P1)

Como fotógrafo quiero saber cuándo Raceframe duda del protagonista para evitar aceptar
recortes incorrectos y localizar rápidamente las fotografías que debo revisar.

**Why this priority**: Un recorte geométricamente correcto puede ser inútil si elige otra persona.

**Independent Test**: Evaluar casos de una persona, grupo, empate, baja confianza y ausencia
de personas, inspeccionando la decisión y sus motivos sin depender de la exportación gráfica.

**Acceptance Scenarios**:

1. **Given** varias personas, **When** se selecciona el protagonista, **Then** se consideran
   cercanía al centro, tamaño relativo, confianza y relaciones espaciales observables;
   la persona más grande no gana automáticamente.
2. **Given** candidatos con puntuaciones dentro de la tolerancia de ambigüedad configurada,
   **When** se decide, **Then** se marca para revisión y no se aplica un recorte automático.
3. **Given** ninguna persona válida o confianza insuficiente, **When** se analiza,
   **Then** se registra el motivo y se aplica la política de exportación que el propietario confirme.
4. **Given** un resultado marcado, **When** el fotógrafo revisa el manifiesto,
   **Then** puede identificar la foto original, las detecciones, las puntuaciones y el motivo.

---

### User Story 3 - Completar lotes y cancelar con resultados auditables (Priority: P2)

Como fotógrafo quiero procesar carpetas grandes, conocer el progreso y poder detener un
trabajo sin perder el rastro de qué terminó correctamente y qué quedó pendiente.

**Why this priority**: Los eventos contienen 2.000–3.500 fotos y los fallos individuales son posibles.

**Independent Test**: Usar un lote con entradas válidas, dañadas y nombres repetidos;
cancelar durante el procesamiento y contrastar el informe con los archivos completos.

**Acceptance Scenarios**:

1. **Given** una carpeta con fotos y otros archivos, **When** se inicia el trabajo,
   **Then** se informa el número de JPG/JPEG encontrados y se ignoran los formatos fuera del alcance.
2. **Given** subcarpetas, **When** se activa la búsqueda recursiva,
   **Then** se incluyen sus fotos sin colisiones de nombres; sin esa opción no se recorren.
3. **Given** una fotografía dañada o un error de exportación individual,
   **When** se procesa el lote, **Then** se registra el error y se intenta la siguiente fotografía.
4. **Given** un trabajo en curso, **When** se solicita cancelación,
   **Then** no se inicia la siguiente imagen tras reconocerla, se resuelve de forma segura la
   operación activa y se informa de lo completado y de lo no intentado, sin prometer interrupción instantánea.
5. **Given** un destino igual al origen o dentro de su árbol recursivo,
   **When** se valida el trabajo, **Then** se rechaza antes de exportar y se explica el motivo.
6. **Given** falta de espacio, pérdida del destino o imposibilidad de registrar resultados,
   **When** no es seguro continuar, **Then** se detiene el trabajo con estado incompleto/error,
   conservando lo ya confirmado; no se anuncia un éxito global.

---

### User Story 4 - Comparar modos y proporciones (Priority: P2)

Como fotógrafo quiero elegir un modo y proporción para adaptar el recorte a la entrega
manteniendo la protección del sujeto como prioridad.

**Why this priority**: Permite comparar composición y pérdida de contexto durante la validación.

**Independent Test**: Evaluar la misma selección conocida en tres modos y proporciones;
comparar regiones, contexto preservado y advertencias sin ejecutar un detector real.

**Acceptance Scenarios**:

1. **Given** una misma foto y protagonista, **When** se comparan conservador, equilibrado y cerrado,
   **Then** el conservador no elimina más área que el equilibrado, ni este más que el cerrado;
   se permite igualdad cuando las restricciones lo exijan.
2. **Given** la proporción original, **When** se recorta, **Then** se mantiene salvo el redondeo
   inevitable a píxeles enteros, sin estirar la imagen.
3. **Given** una proporción 3:2 o 4:5 solicitada, **When** existe un recorte seguro,
   **Then** se respeta la proporción con un error máximo de un píxel en el lado calculado.
4. **Given** una proporción solicitada incompatible con conservar la región protegida,
   **When** se evalúa, **Then** no se fuerza un recorte inseguro y se registra la incompatibilidad.

### Edge Cases

- Carpeta vacía, inexistente o sin permiso: resultado explícito; ningún original modificado.
- Extensiones en mayúsculas, nombres Unicode y espacios: admitidos igual que los equivalentes simples.
- Archivo con extensión JPEG pero contenido ilegible: error por archivo, no éxito sin salida.
- Corredor parcialmente oculto o cortado en el original: proteger lo visible detectable,
  registrar límites de confianza; no inventar extremidades ni prometer detectarlas todas.
- Multitud, espectadores y corredores agrupados: posible ambigüedad; no asumir identidad deportiva.
- Detecciones inválidas o fuera de imagen: no producir un recorte fuera de límites.
- Margen solicitado que rebasa la imagen: conservar el sujeto y usar el margen factible,
  registrando que no se pudo aplicar íntegramente; no extender el lienzo.
- Orientación EXIF ausente, inválida o con rotación/reflejo: mantener coherencia visual;
  advertir si no puede interpretarse con seguridad.
- Dos entradas con mismo nombre y subcarpetas distintas; ejecuciones repetidas: salidas y
  manifiestos identificables sin sobrescritura.
- Entrada y destino equivalentes por enlaces simbólicos: tratar como la misma ubicación.
  Por defecto no seguir enlaces a directorios durante el recorrido recursivo para evitar ciclos.
- Imagen demasiado pequeña para el recorte o proporción inviable: conservar sin recortar
  o marcar pendiente según la política confirmada y registrar el motivo.
- Cancelación o cierre abrupto: distinguir cancelación gestionada de trabajo interrumpido;
  una exportación parcial nunca cuenta como fotografía completada.
- Modelo no disponible localmente: explicar el problema antes de analizar;
  no descargarlo silenciosamente durante un trabajo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El usuario DEBE poder indicar entrada, destino, inclusión de subcarpetas,
  modo, proporción, margen y calidad JPEG. Se DEBEN validar antes de iniciar escrituras.
- **FR-002**: El sistema DEBE aceptar JPG/JPEG sin distinguir mayúsculas, contabilizar candidatos
  y conservar un inventario estable del trabajo para identificar también los no intentados.
- **FR-003**: El sistema NO DEBE modificar ni sobrescribir originales; DEBE validar ubicaciones
  reales de origen/destino y rechazar destinos inseguros descritos en los escenarios.
- **FR-004**: Si no se indica destino, DEBE proponer un directorio hermano `Raceframe_Output`;
  si no puede hacerlo de forma segura, DEBE solicitar un destino válido en lugar de escribir en el origen.
- **FR-005**: El análisis y la exportación DEBEN funcionar sin conexión una vez preparados los
  recursos locales; ninguna fotografía ni metadato DEBE salir del computador.
- **FR-006**: El análisis DEBE normalizar la orientación visual, detectar personas y registrar
  sus regiones y confianza en las dimensiones de la fotografía visualmente orientada.
- **FR-007**: La selección DEBE producir puntuaciones explicables y configurables, usando posición,
  tamaño, confianza y relaciones espaciales; DEBE documentar qué se observa y qué no se puede inferir
  sobre visibilidad o identidad. Las tolerancias configuradas DEBEN permitir reproducir la decisión.
- **FR-008**: Se DEBEN distinguir selección fiable, ambigüedad, baja confianza y ausencia de personas.
  Las tres últimas NO DEBEN recibir un recorte automático; requieren revisión.
- **FR-009**: Para fotografías inciertas o sin recorte seguro, la exportación DEBE seguir
  [NEEDS CLARIFICATION: ¿copiar sin cambios y marcar para revisión, o no exportar y registrar como pendiente?].
- **FR-010**: El recorte DEBE quedar dentro de la imagen, preservar la región detectada del sujeto,
  respetar márgenes factibles y mejorar el centrado horizontal cuando sea posible sin incumplir
  esos límites ni el grado de conservación de contexto del modo. No se exige centrar verticalmente.
- **FR-011**: Con proporción original y modo conservador, un sujeto dentro de la tolerancia de
  centrado DEBE conservar el encuadre. La tolerancia y el límite de pérdida de contexto DEBEN
  quedar definidos en configuración y en el registro del trabajo antes de implementar el motor.
- **FR-012**: Los tres modos DEBEN usar las mismas reglas de protección y variar únicamente
  sus parámetros de composición; DEBEN satisfacer la relación de conservación del escenario 4.1.
- **FR-013**: Se DEBE ofrecer proporción original (predeterminada), 3:2 y 4:5. Las proporciones
  explícitas se interpretan ancho:alto, sin inversión automática según la orientación de entrada.
  Si no hay solución segura, se DEBE advertir y aplicar FR-009, sin deformar ni generar píxeles.
- **FR-014**: La exportación DEBE conservar el nombre base, resolver colisiones sin sobrescribir,
  aplicar calidad configurable a imágenes recortadas y omitir recomprimir las copias sin cambios.
- **FR-015**: Las salidas modificadas DEBEN verse derechas, conservar metadatos compatibles y
  perfil de color cuando exista, actualizar dimensiones/orientación y eliminar o actualizar
  miniaturas obsoletas. Toda pérdida de metadatos identificada DEBE advertirse por fotografía.
- **FR-016**: Las copias sin cambios DEBEN conservar el archivo byte por byte, incluidos EXIF,
  perfil de color y orientación; el registro DEBE aclarar que sus regiones se expresan en
  coordenadas visualmente orientadas aunque el archivo copiado mantenga su orientación EXIF.
- **FR-017**: El sistema DEBE producir un manifiesto JSON del trabajo con identificación de entrada
  y salida, dimensiones orientadas, detecciones, puntuaciones, protagonista, recorte, dimensiones
  finales, configuración aplicada, confianza, decisiones, advertencias y errores por fotografía.
  El nombre relativo de entrada DEBE desambiguar archivos homónimos.
- **FR-018**: El informe DEBE distinguir decisión de composición (recortada, sin cambios o revisión)
  de resultado operativo (exportada, omitida, error o no intentada). El resumen DEBE permitir
  reconciliar cada candidato exactamente una vez en los resultados operativos, y contar revisión
  de manera independiente. Solo una salida completa DEBE contar como exportada.
- **FR-019**: Un trabajo DEBE informar total, avance, exportadas, omitidas, errores, no intentadas,
  recortadas, sin cambios, para revisión, duración y destino. El estado global DEBE diferenciar
  completado, completado con errores, cancelado e interrumpido; no ocultar fallos tras un éxito global.
- **FR-020**: El sistema DEBE tratar errores individuales recuperables sin abortar el lote y
  detenerse con información explícita ante fallos globales que impidan exportar o auditar con seguridad.
- **FR-021**: La cancelación DEBE conservar las salidas completas, no iniciar nuevas imágenes tras
  reconocer la petición y dejar auditable lo pendiente; no exige terminar instantáneamente una operación activa.
- **FR-022**: El proceso DEBE evitar acumular fotografías originales decodificadas a medida que
  crece el lote; solo mantendrá las necesarias para el trabajo activo. DEBE funcionar en CPU.
- **FR-023**: Los parámetros de selección, confianza, ambigüedad, márgenes, conservación de área,
  centrado y calidad DEBEN tener valores válidos documentados y quedar registrados con el trabajo;
  sus valores definitivos se fijarán en el plan y se ajustarán con evaluación fotográfica.
- **FR-024**: El prototipo DEBE acompañarse de una comparación local de originales y resultados
  para 30–50 fotografías reales, anotando protagonista correcto, integridad visible, composición
  y necesidad de intervención. Esta revisión NO requiere desarrollar una interfaz gráfica.
- **FR-025**: El alcance de distribución para evaluar dependencias y modelos queda pendiente:
  [NEEDS CLARIFICATION: ¿uso personal inicial, publicación abierta o distribución comercial cerrada?].
  La decisión no autoriza publicación ni determina por sí sola una licencia compatible.

### Key Entities *(include if feature involves data)*

- **Trabajo**: origen, destino, inventario, configuración, estado global, progreso, duración y resumen.
- **Fotografía de entrada**: ruta relativa única, dimensiones, orientación y legibilidad.
- **Persona detectada**: región visible estimada, confianza, puntuación y factores de selección.
- **Decisión de composición**: protagonista opcional, recorte opcional, modo, proporción, incertidumbre
  y motivos de conservar el encuadre o solicitar revisión.
- **Resultado de fotografía**: decisión, resultado operativo, salida opcional, advertencias y error.
- **Evaluación fotográfica**: referencia a original/salida, valoración del propietario y necesidad de
  intervención; separada de la confianza automática, que no mide satisfacción estética.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En todos los escenarios de aceptación, el 100 % de los originales y archivos
  preexistentes conserva su contenido; ninguna ejecución sobrescribe una salida anterior.
- **SC-002**: En el conjunto de casos geométricos conocidos, el 100 % de los recortes permanece
  dentro de la imagen, conserva la región protegida factible y respeta la proporción dentro
  de la tolerancia de un píxel; los casos inviables se señalan y no se recortan automáticamente.
- **SC-003**: En casos sintéticos definidos de protagonista centrado, lateral, en borde, plano medio,
  varias personas y ausencia de personas, todas las decisiones cumplen sus escenarios;
  todos los casos inciertos conocidos se identifican para revisión.
- **SC-004**: En un lote de comprobación con fotos dañadas, duplicados y cancelación, el 100 %
  de los candidatos figura una sola vez en los resultados operativos y ninguna salida incompleta
  aparece como exportada. Los totales del informe coinciden con los archivos confirmados.
- **SC-005**: Un lote representativo de 2.000–3.500 fotografías puede ejecutarse sin conservar
  todas las imágenes decodificadas en memoria. Se registra duración, volumen y consumo máximo
  en el Mac de prueba; no se promete una velocidad ni un límite numérico antes de medir.
- **SC-006**: Una ejecución sobre la muestra de 30–50 fotografías se completa sin acceso de red
  con recursos previamente preparados y cada fotografía recibe valoración humana de selección,
  integridad visible y composición. Se informa número y proporción que requieren intervención.
- **SC-007**: El propietario evalúa como útil al menos un resultado lateral de cuerpo completo y
  uno de plano medio, y verifica la conservación de un caso centrado y otro junto al borde.
  Ningún recorte que el propietario detecte que corta al protagonista se acepta como seguro
  en la evaluación: se registra, corrige o deriva a revisión antes de aceptar el prototipo.
- **SC-008**: Para cada fotografía de la muestra, el propietario puede localizar original,
  salida si existe, motivo de revisión y parámetros aplicados usando el registro local,
  sin tener que inspeccionar el código ni utilizar un editor de programación.

## Assumptions

- Producto: Raceframe. Operación inicial por el agente; el propietario no tiene que usar la terminal.
- El prototipo CLI es el primer incremento; la interfaz gráfica, selección alternativa de corredor,
  ajuste manual interactivo y previsualización dentro de la aplicación pertenecen a una fase posterior.
- Alcance inicial: JPG/JPEG, macOS Apple Silicon, un trabajo local a la vez y ejecución secuencial.
  RAW, otros formatos, poses, dorsales, Lightroom y reanudación automática quedan fuera.
- Valores iniciales propuestos: modo conservador, proporción original, sin subcarpetas y margen
  relativo configurable. No se fijan aquí algoritmos, pesos ni umbrales numéricos de composición.
- La preservación de metadatos incluye GPS si existe en el original; la aplicación no los publica.
  Una opción de eliminación deliberada de datos personales queda fuera de este incremento.
- Las proporciones explícitas ancho:alto se aplican literalmente; un requisito de inversión
  automática o presets adicionales deberá clarificarse antes de añadirlo.
- El manifiesto y resultados son locales y permanecen hasta que el propietario los gestione;
  no se incluye borrado automático ni historial centralizado de trabajos.
- Las detecciones son estimaciones: preservar su región no garantiza conservar toda extremidad real.
  Los errores de selección y detección deben medirse con fotografías reales y revisión humana.
- Se requiere disponer de pesos locales y acceso autorizado a una muestra privada representativa;
  no se incluirán las fotografías en Git ni se presupone que ya estén disponibles.
- La evaluación de licencias, dependencias, parámetros, coordenadas y escrituras interrumpidas
  pertenece al plan técnico posterior. No se instalarán dependencias de visión ni descargarán pesos
  durante esta etapa de especificación.
