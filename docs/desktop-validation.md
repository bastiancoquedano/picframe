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

## Incremento 0.2.1 — nombre de carpeta

159 pruebas locales aprobadas (incluyendo detector real), ruff check y formato correctos.
Exportación Qt con nombre personalizado, rechazo de rutas sin perder análisis, colisión
con sufijo numerado y conservación de carpeta existente verificados con fotos sintéticas.
El UUID de auditoría sigue separado del nombre visible; CLI conserva job-UUID por defecto.
App 0.2.1 reconstruida; diagnóstico offline con inferencia CPU y exportación metadata_verified
correctos. codesign --verify --deep --strict pasó. Se conserva firma ad hoc sin notarización.

## Incremento 0.2.2 — filtro de revisión

170 pruebas locales aprobadas, con RACEFRAME_TEST_MODEL para detector real. Ruff check y
formato correctos. Casos Qt: pendientes y errores, filtro sin perder decisiones, avance tras
selección manual, restauración automática, lista vacía con previews limpios, reanálisis y
exportación del lote completo aunque haya filas ocultas. Errores de exportación simulados
reaparecen en revisión y se actualizan al corregir la foto. El filtro no implica aprobación
fotográfica ni completa T042/T043.
Bundle 0.2.2 reconstruido: diagnóstico bajo deny network* confirmó review_filter_verified,
inferencia CPU y exportación metadata_verified. Firma local verificada con codesign --verify
--deep --strict. Sin cambios en alcance de distribución (ad hoc, sin notarización).
