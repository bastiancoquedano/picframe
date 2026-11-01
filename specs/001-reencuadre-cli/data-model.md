# Modelo de datos y estados

Diseño, no implementación. Todos los documentos incluyen schema_version=1 y job_id UUID.
Tiempos ISO 8601 con zona; duración medida con reloj monótono. JSON sin NaN ni Infinity.
Las rutas del manifiesto son locales; nunca deben interpretarse como destinos de escritura sin validación.

## Entidades

| Entidad | Campos y validaciones |
| --- | --- |
| Job | job_id, created_at, finished_at opcional, input_root, output_root, job_directory, config, runtime, status, summary |
| Config | recursive=false, mode=conservative, aspect=original, margin=0.08, quality=95, umbrales y pesos del plan, device=cpu, model_path local |
| Runtime | app_version, versiones de dependencias, modelo y SHA-256, device solicitado/efectivo, OS, imagen de inferencia=640 |
| InputImage | image_id estable dentro del inventario, ruta relativa, tamaño bytes, mtime_ns, dimensiones almacenadas/orientadas al leer, orientación EXIF |
| Detection | id local, bbox_xyxy float finita, confidence [0,1], class=person, score y factores, elegibilidad, motivos |
| Composition | selection_status, selected_id nullable, crop_xyxy entero nullable, mode, aspect solicitado/efectivo, margin solicitado/efectivo, reasons |
| ImageResult | image_id, composition nullable si no se analizó, operation_status, output_path nullable, output_sha256 nullable, final_dimensions nullable, warnings, error nullable |
| Summary | total, exported, omitted, errors, not_attempted; cropped, unchanged, review_required; elapsed_seconds |

source dimensiones: stored_width/height antes de orientación; oriented_width/height después.
Bounding boxes y recorte usan exclusivamente coordenadas orientadas. Región [x1,y1,x2,y2),
0 <= x1 < x2 <= W, 0 <= y1 < y2 <= H. Redondear hacia fuera la región protegida.
Las coordenadas crop_xyxy de una copia íntegra son [0,0,W,H], aun cuando conserve EXIF original.
Calidad y parámetros validados antes de escrituras. Margen numérico finito en [0,0.5];
pesos no negativos de suma 1; retenciones en (0,1], umbrales en [0,1].

## Estados independientes

selection_status: selected / ambiguous / low_confidence / no_person / not_analyzed.
composition: cropped / unchanged / review_required, o null para error anterior al análisis.
operation_status: exported / omitted / error / not_attempted.
Omitted se reserva para exclusiones explícitas futuras; incertidumbre legible ahora es exported
con composition=review_required. Un fallo de copia es error y mantiene review_required si se conocía.

Job: preparing → running → completed | completed_with_errors | cancelled | failed.
Interrupción abrupta: el último estado persistido puede seguir running; el lector lo presenta
como interrupted cuando consta que ya no hay proceso activo. No inferir interrupción solo
por ausencia temporal de progreso. report --recover exige exclusión del proceso escritor.

Inventario inmutable; cada image_id tiene un único resultado operativo terminal derivado.
Las no intentadas no requieren filas JSONL anticipadas: se derivan del inventario y eventos.
summary.total = exported + omitted + errors + not_attempted. Review_required se cuenta aparte;
no sumar estos contadores de composición como si fueran particiones del resultado operativo.
Completed solo si todo fue intentado sin error; completed_with_errors si todo fue intentado con errores;
cancelled y failed pueden dejar no intentadas. Lote vacío es completed con total=0 y aviso.

## Diario y transacciones

Archivos por trabajo: inventory.json, job.json, events.jsonl y manifest.json final.
Cada evento tiene seq creciente, timestamp, type y image_id cuando aplica. Eventos:
image_started, export_prepared (temporal/destino relativos y hash), image_completed,
image_failed, cancel_requested y job_finished.

Antes de publicar: terminar temporal, flush/fsync y registrar export_prepared con fsync.
Publicar mediante enlace exclusivo dentro del mismo volumen; si colisiona, elegir nuevo nombre
y registrar nueva intención antes de publicarlo. Registrar image_completed solo tras publicar.
Manifiesto se escribe a temporal y se reemplaza atómicamente: reemplazar ese archivo propio
está permitido; nunca reemplazar entradas o JPEG existentes.

En recuperación, leer solo eventos JSONL completos con secuencia válida; una última línea
truncada se ignora con advertencia. Verificar los destinos preparados con su hash: si coinciden,
confirmar exportación recuperada; si faltan, marcar error interrupted_export; si difieren,
marcar conflicto y no modificar el archivo. Trabajos sin resultado confirmado no son éxito.
El lector puro no cambia archivos; --recover añade informe recuperado a nombre exclusivo,
con status=interrupted. No retoma inferencia ni borra salidas o temporales automáticamente.

Errores: code estable, message en español, stage, detalles locales mínimos. Advertencias:
ambiguous_subject, low_confidence, no_person, margin_clipped, infeasible_crop,
metadata_unverified, metadata_dropped, cpu_fallback e interrupted_export, entre otras documentadas.
