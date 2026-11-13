# Feature Specification: Marcas de agua inteligentes en Picframe

**Feature Branch**: main
**Created**: 2026-11-12
**Status**: Aprobada e implementada; evaluación visual con fotos reales pendiente
**Input**: módulo Smart Watermark pegado por el propietario; antes RaceFrame, ahora Picframe.

## User Scenarios & Testing

### User Story 1 — Aplicar marcas PNG tradicionales (Priority: P1)
Como fotógrafo quiero añadir una o más marcas PNG con transparencia para identificar mis fotos
sin recortarlas ni editar los originales.

**Why this priority**: Da valor sin depender del segmentador y ofrece una alternativa para cualquier foto.
**Independent Test**: Cargar una foto JPEG y uno o varios PNG; revisar posiciones, tamaños, opacidad
antes/después y exportar al destino independiente.

**Acceptance Scenarios**:
1. **Given** un JPEG y PNG transparente, **When** selecciono el modo Tradicional, **Then** la marca
   aparece con la escala, opacidad y posición elegidas en el tamaño original de la foto.
2. **Given** varias marcas, **When** las ordeno o cambio su posición, **Then** la vista previa y la
   exportación conservan el mismo orden, tamaño y transparencia.
3. **Given** una carpeta con fotos, **When** inicio el lote, **Then** Picframe exporta una por una,
   muestra progreso, permite cancelar y registra errores sin alterar originales.

### User Story 2 — Poner la marca principal detrás de las personas (Priority: P1)
Como fotógrafo quiero que un PNG grande atraviese la escena pero quede detrás de las personas
para que se distingan naturalmente y la marca siga visible donde no hay personas.

**Why this priority**: Es el efecto principal que hace inteligente este módulo.
**Independent Test**: Máscara artificial con persona única, varias personas, superposición y bordes;
comparar composición en memoria antes de codificar JPEG.

**Acceptance Scenarios**:
1. **Given** personas segmentadas, **When** aplico Smart Watermark, **Then** el PNG principal
   aparece en su posición y escala debajo de la máscara de todas las personas.
2. **Given** la composición antes de renderizar la identificación y de codificar JPEG, **When**
   comparo el plano de personas con la foto orientada, **Then** cada píxel de persona protegido es
   idéntico al original; no se desplaza, inventa, suaviza ni reconstruye la persona.
3. **Given** máscara de menor resolución, **When** la adapto a la foto, **Then** se alinea con las
   dimensiones, orientación y coordenadas del JPEG original y evita halos visibles.
4. **Given** ninguna persona en la foto, **When** aplico el modo inteligente, **Then** el PNG se
   muestra sobre el fondo sin dejar franjas fuera del lienzo.

### User Story 3 — Mantener visible una identificación frontal (Priority: P1)
Como fotógrafo quiero añadir mi nombre, texto o un segundo PNG encima de la composición para que
la autoría permanezca visible.

**Why this priority**: La marca principal puede quedar ocluida por las personas.
**Independent Test**: Aplicar texto/logotipo en posiciones configurables y comprobar que se renderiza
por encima del PNG principal y de la máscara.

**Acceptance Scenarios**:
1. **Given** una identificación activada, **When** exporto una imagen, **Then** texto o PNG se dibuja
   después de la composición inteligente y permanece visible en la posición configurada.
2. **Given** tamaños, opacidad y margen distintos, **When** cambio las opciones, **Then** la vista
   previa y la exportación coinciden.
3. **Given** identificación desactivada, **When** exporto, **Then** solo aparecen las marcas principales.

### User Story 4 — Repetir una configuración en una sesión grande (Priority: P1)
Como fotógrafo quiero guardar una configuración, ver el resultado antes de aplicarla y procesar
hasta 5.000 JPEG sin cargar toda la sesión en memoria.

**Why this priority**: El mismo diseño se utiliza para vender o identificar lotes deportivos.
**Independent Test**: Guardar/cargar preset y procesar lote sintético cancelando a mitad de sesión.

**Acceptance Scenarios**:
1. **Given** un preset guardado, **When** lo cargo, **Then** se restauran modos, marcas y parámetros;
   si una ruta local de PNG desapareció, Picframe explica cuál falta y no procesa con un sustituto.
2. **Given** procesamiento, **When** observo el trabajo, **Then** la ventana continúa respondiendo,
   muestra cantidad/progreso, libera cada imagen y continúa luego de un error individual.
3. **Given** que cancelo, **When** termina el archivo activo, **Then** quedan manifiesto y salidas
   completas; originales y archivos de salida anteriores permanecen intactos.

## Edge Cases

Personas superpuestas o en bordes; orientación EXIF 1–8; PNG sin área visible, completamente opaco,
malformado o de tamaño extremo; foto sin personas; máscara vacía, desalineada, parcial o corrupta;
fallo del framework/modelo; herramienta de metadatos ausente; cancelación o cierre durante lote;
identificación que intersecta personas; preset con archivos no disponibles; fondo complejo.
La máscara solo controla la oclusión del PNG principal. La identificación frontal es una marca
separada y se dibuja encima; no se afirma que píxeles bajo una marca intencional permanezcan iguales.
Los originales nunca son destino de escritura. No se promete protección absoluta frente a borrado.

## Requirements

### Functional Requirements

- **FR-001**: Mostrar una sección «Marcas de agua» coherente con la app Picframe existente.
- **FR-002**: Aceptar JPEG de entrada y PNG con transparencia como recursos de marca, sin transformar
  el aspecto, relación ni tamaño de la foto al componer.
- **FR-003**: Ofrecer modo Tradicional y modo Smart; Tradicional admite múltiples PNG posicionables,
  con escala, opacidad y centrado automático.
- **FR-004**: Smart compone foto, PNG principal y máscara de personas en ese orden perceptual;
  oclusiones coinciden con la silueta y el lienzo original.
- **FR-005**: La máscara no elimina, reemplaza, mueve ni suaviza píxeles de los sujetos. La verificación
  de identidad se realiza antes de JPEG y antes de aplicar marcas que cubran voluntariamente esos píxeles.
- **FR-006**: Agregar identificación de texto o PNG con tamaño, opacidad, posición y margen propios;
  el usuario puede activarla o apagarla. En modo Smart se dibuja encima de las demás capas.
- **FR-007**: Mostrar previsualización coincidente con antes/después y permitir configurar la carpeta
  de salida y el nombre del trabajo.
- **FR-008**: Admitir máscaras alineadas con la foto orientada para varias personas, solapamientos,
  orientación EXIF y personas cerca del borde. Configurar conducta ante fallo por foto: Tradicional
  delante, copiar original bytes o no publicarla. Default aprobado: Traditional + revisión; continuar lote.
- **FR-009**: Procesar localmente sesiones de 1.000 a 5.000 fotos, liberar cada imagen/máscara, ofrecer
  progreso y cancelación cooperativa; no cargar el lote completo a memoria ni sobrescribir originales.
- **FR-010**: Exportar JPEG en resolución original y calidad configurable; preservar orientación
  visual, ICC y metadatos EXIF/IPTC/XMP soportados por la política estricta del exportador existente.
- **FR-011**: Guardar y reutilizar presets locales, incluyendo ruta/identidad del PNG y configuración.
- **FR-012**: Mantener exportación atómica, registro/auditoría por imagen y lectura clara de fallos.
- **FR-013**: Todo análisis/segmentación/composición funciona offline después de preparar el software;
  no se envían fotografías ni máscaras a redes externas.

### Key Entities

- **Capa principal**: archivo PNG, escala, opacidad, ubicación, repetición opcional.
- **Identificación**: texto o PNG, tamaño, posición, opacidad y margen; z-order superior.
- **Máscara de persona**: mapa local en coordenadas de la foto orientada, dimensiones, calidad y estado.
- **Configuración/preset**: modo, capas, identificación, calidad JPEG y rutas locales de recursos.
- **Trabajo**: origen/destino, inventario, progreso, cancelación, manifiesto y fallos por imagen.

## Success Criteria

- **SC-001**: La persona usuaria puede aplicar modo Tradicional a una foto sin modificar el origen.
- **SC-002**: En composición Smart, todo píxel de alta confianza marcado como persona queda idéntico
  al original después de aplicar la oclusión del PNG principal y antes de la identificación/JPEG.
- **SC-003**: Foto, máscara, vista previa y exportación conservan el tamaño y la orientación visual
  para las 8 orientaciones EXIF probadas.
- **SC-004**: Un lote mixto sintético continúa tras errores de segmentación, muestra progreso y
  cancelación coherente sin escribir en originales.
- **SC-005**: Los campos EXIF/IPTC/XMP e ICC que el exportador actual promete conservar quedan
  verificados antes de publicar cada JPEG.
- **SC-006**: El flujo de inicio no descarga ni transmite fotos/máscaras; ejecutar offline funciona.
- **SC-007**: Preset guardado y vuelto a cargar reproduce los mismos parámetros sobre el conjunto de
  pruebas sintéticas.

## Clarifications
### Session 2026-11-12
- Smart Watermark detecta y protege personas; animales/vehículos quedan fuera de la máscara de esta versión.
- La foto se orienta con el cargador existente antes de segmentar; el exportador normaliza orientación
  visual y conserva metadatos soportados.
- La identificación superior es una marca voluntaria; la prueba de preservación se aplica antes de
  dibujarla y excluye sus píxeles si se superpone a una persona.
- Si falla la segmentación de una foto, Picframe aplica a esa foto el modo Tradicional por encima de
  las personas, la marca para revisión y continúa el lote.

## Assumptions

- Automático es local y determinista para la configuración/modelo fijos; no ofrece protección absoluta.
- JPEG es el único formato fotográfico de entrada/exportación en esta fase; RAW, TIFF y PNG de entrada
  siguen el alcance actual del motor.
- Por defecto, la identificación frontal está desactivada hasta que se configure; Smart Watermark
  exige que el usuario elija un PNG de marca principal.
- El preset guarda rutas locales; no copia PNG ni fotos a servicios externos.
- La calidad final de JPEG puede producir la pérdida generacional inevitable; la identidad pixel a pixel
  se verifica en la composición de memoria, antes de la codificación.
- UX debe mostrar el efecto de identificación superpuesto al usuario y permitir recolocarlo.
