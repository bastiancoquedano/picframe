# Propuesta arquitectónica — Marcas de agua

**Estado**: propuesta aprobada como base; los hitos de PyObjC/Bundle se validan en el plan.

## Punto de partida verificado

Picframe es Python 3.11 con PySide6/Qt Widgets y ya procesa JPEG localmente por carpetas.
`MainWindow` es una sola ventana con controles de Encuadre y panel antes/después; `TaskWorker` en
QThread ofrece progreso/cancelación y limita el trabajo a una foto activa. El núcleo de selección
actual usa cajas de YOLO, no máscaras. `export_image` crea una salida temporal atómica, conserva APP/
COM y verifica EXIF/MakerNotes/IPTC/XMP/ICC con ExifTool. Sus decisiones de composición actuales
están ligadas al recorte/personas. El bundle local es PyInstaller arm64 e incluye ExifTool/Perl;
las fotos, pesos y salida están fuera de Git.

## Propuesta

- Añadir pestaña independiente **Marcas de agua**, conservando Encuadre. Reusar diálogos/listado,
  worker, cancelación, vista orientada, descubrimiento de carpetas y auditoría; no llamar al recortador
  para operaciones de marca.
- Mantener un módulo de configuración/renderizador puro Pillow/OpenCV: produce RGBA a dimensiones
  originales; interfaz solo edita capas y muestra esa misma composición.
- Evaluar primero **Apple Vision** `VNGeneratePersonSegmentationRequest` mediante un adaptador local
  Python/Objective-C (`pyobjc-framework-Vision`). Está integrado en macOS desde 12 y solicita máscara
  de persona en resoluciones/calidades seleccionables; evita otro peso y descarga. La investigación
  oficial confirma la API y la máscara pixel-buffer. Probar paquete PyObjC, visión sin UI, orientación,
  desempeño y distribución PyInstaller antes de fijarla en el plan. Fuentes: [Apple: person matte]
  (https://developer.apple.com/documentation/vision/applying-matte-effects-to-people-in-images-and-video),
  [Apple: request](https://developer.apple.com/documentation/vision/vngeneratepersonsegmentationrequest).
- Alternativa si PyObjC/Apple Vision no se integra limpiamente: YOLO11n-seg, reutilizando Ultralytics
  ya instalado. Entrega máscaras por instancia (favorable a solapes), pero añade pesos y dependencia
  de licencia AGPL para la distribución; confirmar hash, licencia y preparación explícita antes de
  adoptarla. Fuentes oficiales: [Ultralytics segmentation](https://docs.ultralytics.com/tasks/segment/),
  [licencias](https://www.ultralytics.com/license). Ninguna alternativa sube fotos fuera del Mac.
- Flujo propuesto por foto orientada: RGB original → PNG principal → oclusión únicamente de alfa del
  PNG usando máscara (dilatar 1–2 px a resolución original reduce filtración en bordes) → identificación
  superior → JPEG una vez. El área de máscara opaca recompuesta conserva RGB original idéntico antes
  de identificación/codificación. Umbral/dilatación se probarán con máscaras sintéticas; no retocar,
  recortar, mover o regenerar la persona.
- Reusar preservación/validación de metadatos existente. Agregar un camino de exportación renderizada
  a tamaño completo (no `CompositionStatus.CROPPED` ni un detector ficticio); escribir JPEG en temp,
  validar metadatos/ICC, fsync, publicar sin colisión, registrar el hash/máscara/estado en el manifiesto.
- Una imagen y máscara activas. Usar trabajo secuencial primero; medir antes de paralelizar los
  objetivos 1k–5k. Cancelar entre fotos y continuar ante error individual.
- Guardar presets JSON locales bajo Application Support/Picframe; validar rutas/recursos ausentes.
  Crear un asset de PNG no incluido hasta que el fotógrafo seleccione su propia marca.

## Riesgos por resolver durante el plan

PyObjC tiene que funcionar en el Python uv (3.11), build aislado y bundle Apple Silicon, sin afectar
PySide6/Qt. La máscara semántica quizá una varias personas en una silueta; como la marca principal usa
la unión, normalmente basta, pero se debe confirmar comportamiento y calidad con solapes. La máscara
ha de remuestrearse a orientación/resolución exactas sin haloes. Cambiar los píxeles de la zona del
logotipo es inevitable: la invariancia se comprueba antes de la firma frontal; firma superpuesta es
una alteración de marca explícita y elegida. Un modelo Ultralytics añadido puede cambiar obligaciones
de distribución; el uso personal actual no las resuelve para una publicación futura.

## Fallback confirmado por el propietario

Si la máscara falla en una foto, esa foto se compone en modo Tradicional por delante de las personas,
se registra y queda marcada para revisión. El resto del lote continúa.
