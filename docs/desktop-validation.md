# Evidencias de interfaz y app local

- Especificación GUI: checklist 9/9, sin ambigüedades críticas nuevas.
- Casos: análisis sin exportación, caché vigente, firmas/configuración/inventario obsoletos,
  selección manual, ROI proporcional, clic sobre persona, drag de recorte, exportación de
  decisión revisada y metadatos, cierre cooperativo y restauración automática.
- Regresión completa ejecutada con pesos locales; las pruebas reales se distinguen de omisiones en CI.
- Vista renderizada con foto sintética y revisión de distribución visual, sin fotos privadas en Git.
- Bundle construido en macOS arm64, abierto normalmente y observado como ventana Raceframe 0.2.0.
- Bundle probado con sandbox-exec deny network*: Qt creado, inferencia real CPU, 1 recorte
  exportado y metadata_verified. Informe privado de prueba en /private/tmp; no se incorpora al repo.
- No se probó distribución en otro Mac, firma Developer ID ni notarización.

Las pruebas de 30–50 fotos y el evento de 2.000–3.500 siguen pendientes. Las pruebas ya
revisadas sirven para avanzar a interfaz, pero no se presentan como esas mediciones completas.
