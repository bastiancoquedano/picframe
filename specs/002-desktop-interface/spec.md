# Feature Specification: Interfaz de escritorio de Raceframe

**Feature Branch**: main
**Created**: 2026-11-01
**Status**: Especificación lista para planificación
**Input**: Idea maestra y petición de continuar tras revisar la muestra; sin clasificación por espalda.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Abrir Raceframe y preparar fotografías (Priority: P1)

Como fotógrafo quiero abrir una ventana con doble clic, seleccionar origen/destino y parámetros
para analizar mis fotografías sin terminal.

**Why this priority**: La aplicación de escritorio es el producto solicitado.
**Independent Test**: Abrir ventana, elegir carpetas sintéticas y comprobar conteo y validaciones.
**Acceptance Scenarios**:
1. **Given** una instalación local preparada, **When** abro Raceframe, **Then** aparece una ventana en español.
2. **Given** una carpeta JPEG, **When** la selecciono, **Then** veo ruta, número y opción de subcarpetas.
3. **Given** destino dentro de entrada recursiva, **When** intento analizar, **Then** se explica el problema sin escribir fotos.

### User Story 2 - Revisar y corregir el encuadre (Priority: P1)

Como fotógrafo quiero ver antes/después, cajas de personas y recorte; elegir otra persona y
ajustar el rectángulo cuando la propuesta no sirve.

**Why this priority**: Las pruebas revelaron que la revisión humana es necesaria.
**Independent Test**: Detector simulado con dos candidatos, cambiar selección y ajustar un recorte.
**Acceptance Scenarios**:
1. **Given** análisis terminado, **When** elijo una foto, **Then** veo original orientado, recorte superpuesto y resultado.
2. **Given** una foto ambigua, **When** elijo una persona válida, **Then** se recalcula y registra la selección manual.
3. **Given** edición manual, **When** dibujo un recorte válido, **Then** se conserva proporción, región protegida y resolución.
4. **Given** cambios de parámetros u origen, **When** los aplico, **Then** el análisis anterior no se exporta como vigente.

### User Story 3 - Exportar sin bloquear la ventana (Priority: P1)

Como fotógrafo quiero exportar, ver progreso y cancelar sin dañar originales o perder auditoría.

**Why this priority**: Hace utilizable el motor para lotes desde una ventana.
**Independent Test**: Exportar/cancelar un lote sintético usando resultados revisados.
**Acceptance Scenarios**:
1. **Given** un análisis completo, **When** exporto, **Then** se usan sus decisiones y correcciones sin repetir inferencia.
2. **Given** procesamiento activo, **When** navego o cancelo, **Then** la ventana responde y finaliza con estado correcto.
3. **Given** exportación terminada, **When** abro resultados, **Then** Finder muestra el trabajo y su informe.
4. **Given** originales modificados después de analizar, **When** exporto, **Then** se rechaza la decisión obsoleta de esa foto.

### Edge Cases

- Carpetas vacías, JPEG dañados, modelo o herramienta de metadatos ausente.
- Cerrar durante inferencia/exportación: cancelar y esperar fotografía activa; no destruir hilos en marcha.
- Rostro no visible o persona de espaldas: no añadir exclusión automática.
- Fotos ambiguas: copia original hasta selección manual; la comparación de grupos no es política automática.
- Selección inválida o recorte que excluye el sujeto: rechazar y explicar, sin aplicar ni exportar ese ajuste.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Mostrar nombre, versión, origen/destino, conteo y controles de análisis/exportación/cancelación.
- **FR-002**: Permitir modos, proporción, márgenes, calidad, focal, prioridad de composición y resolución mínima.
- **FR-003**: Analizar/exportar en segundo plano y publicar progreso, estado y duración en la ventana.
- **FR-004**: Mostrar lista de fotos con estados y comparación orientada antes/después y rectángulos.
- **FR-005**: Permitir seleccionar otra persona y dibujar un recorte manual seguro en coordenadas originales.
- **FR-006**: Exportar decisiones revisadas con la misma conservación estricta de metadatos y auditoría del CLI.
- **FR-007**: Invalidar resultados al cambiar configuración; verificar firma del archivo y configuración antes de exportar caché.
- **FR-008**: Distribuir una aplicación local abrible con doble clic en este Mac, con modelo y recursos de metadatos preparados.
- **FR-009**: Mantener procesamiento local y CPU disponible; no introducir clasificación de espectadores ni poses.

### Key Entities

- Sesión: carpetas/configuración, inventario, análisis, foto seleccionada y estado del trabajo.
- Decisión revisada: registro del motor, selección manual opcional, recorte y firma de entrada/configuración.
- Trabajo activo: progreso, cancelación, duración, resultados y ruta de salida.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un usuario puede preparar, analizar y exportar una carpeta desde la ventana sin terminal.
- **SC-002**: Durante trabajo simulado prolongado se procesan eventos de interfaz y la cancelación deja totales coherentes.
- **SC-003**: Vista previa y exportación usan las mismas coordenadas y orientación en todos los casos de prueba.
- **SC-004**: Originales y metadatos quedan protegidos en las pruebas de exportación con decisiones manuales.
- **SC-005**: La aplicación local abre en macOS arm64 mediante doble clic y carga recursos sin descarga durante el trabajo.

## Assumptions

- Tema oscuro sencillo, textos en español y ventanas/diálogos de macOS.
- Un trabajo activo a la vez y una fotografía decodificada para previsualización; no almacenar todas las imágenes en memoria.
- La muestra revisada orienta la GUI; 30–50 fotos y el lote de 2.000–3.500 siguen pendientes y no se declaran validados.
- Uso personal en este Mac; firma comercial y notarización pertenecen a distribución posterior.

## Incremento: nombre de exportación (2026-11-01)

FR-010: Permitir nombrar la subcarpeta del trabajo desde la ventana, con propuesta legible por fecha.
Se rechazan nombres vacíos, rutas, caracteres de control y nombres reservados; las colisiones
crean sufijos numerados sin sobrescribir. El UUID se conserva internamente para auditoría.
Cambiar solo este nombre no invalida el análisis ni las correcciones. CLI conserva su destino actual.

## Incremento: filtro de revisión (2026-11-01)

FR-011: Permitir alternar Todas / Necesitan revisión y mostrar conteos. Incluir selección
incierta/ausente, composición review_required y errores de análisis/exportación.
Filtrar solo la lista: conservar decisiones, caché y exportación del lote completo.
Al resolver la foto visible, avanzar a la siguiente pendiente. Sin coincidencias, limpiar
previews y deshabilitar edición; mostrar que no hay fotos pendientes. Todas permite volver
a cualquier foto corregida. Actualizar filtro/conteos durante análisis, correcciones y exportación.
No añade persistencia de sesiones ni perfiles en este incremento.
