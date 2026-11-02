# Feature Specification: Sujetos generales y recorte múltiple

**Feature Branch**: main
**Created**: 2026-11-01
**Status**: Especificación aprobada por solicitud de implementación del propietario
**Input**: Ampliar a animales/vehículos, elegir protagonista dominante o conservar grupo usando Spec Kit.

## User Scenarios & Testing

### User Story 1 - Elegir el tipo de protagonista (Priority: P1)
Como fotógrafo quiero elegir Personas, Animales o Vehículos para encuadrar el tema de mi sesión.
**Why this priority**: Fotos sin personas también pueden tener un protagonista recortable.
**Independent Test**: Cambiar categoría y analizar escenas de prueba con distintas clases.
**Acceptance Scenarios**:
1. Dada una foto de perro sin personas, al elegir Animales se puede seleccionar el perro.
2. Dado un auto y un corredor, Personas conserva al corredor como candidato y Vehículos al auto.
3. Dado un tipo no reconocido o baja confianza, conservar original y mostrar revisión.

### User Story 2 - Elegir dominante o grupo (Priority: P1)
Como fotógrafo quiero automatizar fotos con varios sujetos manteniendo control sobre la selección.
**Why this priority**: Reduce revisión sin elegir arbitrariamente entre protagonistas equivalentes.
**Independent Test**: Dos sujetos de áreas distintas, un empate y un grupo junto a los bordes.
**Acceptance Scenarios**:
1. En Dominante, un sujeto elegible con área al menos 1,5 veces la del segundo se selecciona.
2. En Dominante, áreas similares dejan la foto para revisión, independientemente del orden.
3. En Conservar grupo, el encuadre contiene todos los candidatos confiables de la categoría elegida.
4. Revisión manual conserva la puntuación conservadora previa y permite elegir el protagonista.
5. Si proporción o resolución impiden proteger el grupo, conservar original y pedir revisión.

### User Story 3 - Proteger conjuntos y corregir (Priority: P1)
Como fotógrafo quiero evitar cortar bicicletas o caballos asociados a una persona y revisar decisiones.
**Why this priority**: Una caja individual no representa siempre al sujeto fotográfico completo.
**Independent Test**: Persona+bicicleta, persona+caballo, parejas dudosas y selección manual exportada.
**Acceptance Scenarios**:
1. Una asociación geométrica única protege las cajas completas de ambos miembros, más margen.
2. Una asociación con más de una pareja plausible no fuerza recorte automático.
3. Selección manual conserva los compañeros plausibles para evitar cortes; se registra la advertencia.
4. Grupo, animal, vehículo o conjunto se compone sin interpretar el borde superior como cabeza.
5. Categoría/estrategia nuevas invalidan caché; el filtro de revisión refleja incertidumbre y errores.

### Edge Cases
Objetos no soportados; sujetos parcialmente fuera del lienzo; compañeros compartidos; sujeto auxiliar
sin objeto objetivo; grupos que ocupan casi toda la imagen; orientaciones EXIF; errores y cancelación.
No identificar corredores/espectadores por ropa o espalda. No afirmar que proximidad demuestra montaje.

## Requirements
- **FR-001**: Categorías Personas/Animales/Vehículos; mostrar etiquetas de clase legibles.
- **FR-002**: Estrategias Protagonista dominante/Conservar grupo/Revisión manual.
- **FR-003**: Dominante exige confianza y área mínimas y ventaja de tamaño configurable (inicial 1,5).
- **FR-004**: Grupo protege unión de candidatos confiables y compañeros asociados.
- **FR-005**: Asociar solo persona+bicicleta/moto/caballo cuando geometría compatible; dudas explícitas.
- **FR-006**: Mantener regla de cabeza únicamente para persona individual; resto usa ocupación
  sobre el eje limitante con focal larga y contexto con focal corta/ausente.
- **FR-007**: Mantener originales, proporción, resolución mínima, metadatos estrictos y procesamiento local.
- **FR-008**: Registrar categoría, política, miembros, caja conjunta, razones y métricas de selección.
- **FR-009**: Revisar/corregir desde interfaz y exportar las mismas decisiones sin repetir inferencia.
- **FR-010**: Entregar Picframe.app y repositorio picframe con historial conservado; CLI mantiene configuración conservadora por defecto.

### Key Entities
Detección clasificada; candidato con uno o varios miembros; selección con caja conjunta y métricas;
sesión con categoría/estrategia; composición con región protegida; exportación auditada.

## Success Criteria
- **SC-001**: Las tres categorías se seleccionan y exportan desde interfaz sin terminal.
- **SC-002**: En todos los casos de prueba, ningún recorte publicado excluye miembros protegidos.
- **SC-003**: Empates sin ganador según la política y parejas dudosas conservan original, salvo elección explícita de grupo o intervención manual.
- **SC-004**: Modificar categoría/política impide exportar decisiones obsoletas en todos los casos de prueba.
- **SC-005**: App abre y procesa sin conexión; regresión de originales/metadatos aprobada.

## Clarifications
### Session 2026-11-01
- La instrucción del propietario aprueba implementar la propuesta anterior con Spec Kit.
- Dominante en la interfaz por defecto; CLI conserva estrategia conservadora previa.
- Grupo es elección explícita; no es fallback silencioso de Dominante.
- El propietario confirmó Picframe y pidió renombrar el repositorio a picframe; conservar historial.

## Assumptions
Mismo modelo instalado; clases limitadas a su catálogo, sin nuevos pesos/dependencias.
Umbrales geométricos iniciales no equivalen a validación fotográfica. T042/T043 siguen pendientes.
No incluye RAW, poses, dorsales, perfiles persistentes ni guardar sesiones. Uso local personal.
