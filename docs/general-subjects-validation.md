# Picframe 0.3.0 — evidencia de implementación

Fecha: 2026-11-01. Feature Spec Kit: specs/003-general-subjects/.

- 191 pruebas locales aprobadas, con RACEFRAME_TEST_MODEL apuntando al YOLO preparado.
- Ruff check y format --check correctos; comandos picframe/raceframe muestran Picframe 0.3.0.
- Categorías excluyentes, ventaja de área, empates reproducibles, grupos y asociaciones probados
  con cajas sintéticas. Casos de bicicleta/moto/caballo, parejas competidas y cercanía sin solape.
- Exportación JPEG con ExifTool y metadata_verified, originales intactos, membresía/caja conjunta
  auditadas y recuperación/manifiesto v1 compatibles. Categoría/política forman parte de la caché.
- UI Qt probada: animal, etiquetas, grupo, selección manual, exportación sin repetir inferencia e
  invalidación. Captura docs/desktop-preview.png corresponde a muestra sintética sin fotos privadas.
- GitHub confirmó renombrado bastiancoquedano/raceframe → bastiancoquedano/picframe; origin actualizado.

No se validó precisión con fotografías reales nuevas de animales/vehículos ni asociaciones deportivas.
Los casos sintéticos validan lógica e integridad, no sensibilidad del modelo. No completar T042/T043
(30–50 fotografías y lote 2.000–3.500). Firma ad hoc, sin Developer ID ni notarización.

Bundle Picframe.app 0.3.0 construido y verificado con codesign --verify --deep --strict.
Diagnóstico bajo deny network* correcto: inferencia CPU con categorías people/animals/vehicles,
ventana Qt/filtro y exportación de cuatro escenarios sintéticos. Animal, conjunto y grupo
produjeron recortes metadata_verified; vehículo conservó el original completo por geometría
(sin recodificación). No se atribuyen resultados visuales reales a detecciones simuladas.

## Corrección 0.3.1 — Automático y categorías combinables

198 pruebas locales aprobadas con detector real disponible; ruff check y formato correctos.
Lote sintético mixto persona/perro/auto analizado y exportado sin cambiar categorías, con tres
inferencias para tres fotos. Casillas combinables, selección vacía, invalidación y reconstrucción
del detector por categorías efectivas verificados. Asociaciones persona+bici/caballo no compiten
consigo mismas al activar varias categorías. CLI nuevo y configuración singular compatibles.
Captura actualizada con Automático visible y muestra sintética persona+perro.
Bundle 0.3.1 reconstruido y diagnóstico bajo deny network* aprobado: automatic_categories_verified,
filtro, inferencia CPU con todas las categorías y exportación de objetos/conjuntos/grupos.
codesign --verify --deep --strict correcto. No nueva validación fotográfica ni notarización.

CI detectó SIGSEGV en recolección automática de ciclos desde el worker (run 41375912697).
Se añadió recolección periódica en hilo GUI, restaurando la política anterior al salir y sin
cambiar CLI. Nueva prueba verifica 3.000 ciclos creados en worker y liberados en GUI.
Regresión local: 199 pruebas aprobadas. La inferencia sobre causa y fuentes están en research.md.
