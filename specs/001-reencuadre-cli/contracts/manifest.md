# Contrato de manifiesto JSON — v1

Documento único UTF-8 y schema_version=1. Campos raíz obligatorios:
job_id, created_at, finished_at (nullable), status, input_root, output_root, config,
runtime, summary, images. Nombres de campos y enums se fijan en data-model.md.
Futuras versiones incompatibles incrementan schema_version; campos adicionales compatibles
pueden ignorarse por lectores v1. La implementación añadirá esquema JSON validable y fixture.

Cada elemento images referencia exactamente un image_id del inventario, con input_relative_path,
source (dimensiones stored/oriented y exif_orientation nullable), detections, selection_status,
selected_detection_id nullable, composition nullable, crop_xyxy nullable, final_dimensions nullable,
operation_status, output_relative_path nullable, output_sha256 nullable, warnings y error nullable.
Datos no calculados por error o cancelación son null/listas vacías, nunca inventados.
Las cajas usan coordenadas orientadas y las rutas de salida son relativas al directorio de trabajo.

Config conserva pesos de selección, umbrales, retenciones, modo, margen, proporción y calidad;
runtime conserva modelo/hash, versiones y dispositivo efectivo. Estos datos permiten auditar
una decisión, pero no prometen resultados bit a bit idénticos entre CPU y MPS.

Invariantes verificables:

- Una sola fila por imagen candidata, incluso dañadas o no intentadas.
- Exported exige salida completa confirmada, ruta, hash y dimensiones finales.
- Recorte automático exige selected y caja contenida en imagen; review_required exige
  copia íntegra si exportada, y motivo explícito.
- No recorte equivale a crop_xyxy completo cuando las dimensiones orientadas se conocen.
- Errores incluyen código y etapa; dimensiones pueden ser null si no se pudo abrir la imagen.
- Totales cumplen la ecuación del modelo; revisión se cuenta aparte.
- No hay confianza de selección presentada como precisión real o probabilidad de acierto humano.

El diario es fuente de reconstrucción si falta manifest.json. Un manifiesto presente no implica
éxito: el consumidor debe leer status y contadores. No usar el diario como API pública estable
fuera de la versión del trabajo sin comprobar schema_version.
