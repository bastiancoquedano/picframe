# Contrato de interfaz y puente al núcleo

Ventana: origen/destino con diálogos nativos, contador, parámetros, Analizar, Exportar,
Cancelar, Abrir resultados, lista por foto, original con detecciones/recorte y resultado.
Botones exportar/resultados solo habilitados con sus estados válidos. Mensajes en español.

Worker: señales progress(int,int), record(object), result(object), failed(str), finished.
Cancelación con Event. No widgets/QPixmap en worker. Previews QImage.copy desde RGB orientado;
scene usa píxeles originales para overlays y drag, con imagen reducida escalada a ese espacio.

Core: analyze_loaded comparte selección/geometría entre CLI y UI. process_folder acepta
analysis_overrides opcional: valida entrada/config/modelo antes de usar crop y selección.
El análisis base queda registrado en el manifiesto; correcciones llevan manual_selection/manual_crop.
Se rechaza ROI fuera del lienzo, con proporción incorrecta, menor al límite o que corte región protegida.

Entradas: raceframe-gui y python -m raceframe.ui. CLI anterior sin cambios incompatibles.
Bundle: recursos en directorio PyInstaller; resolver sin cwd/PATH de shell. ExifTool incluye lib;
Perl del Mac se invoca con ruta absoluta. Sin descargas durante uso ni filtros por orientación.

Nombre de carpeta: componente opcional job_name del núcleo; UI lo exige y propone Raceframe_YYYY-MM-DD.
Se añade bajo Destino, con sufijo numérico si existe. No altera Config ni la caché. job_id sigue siendo UUID.
