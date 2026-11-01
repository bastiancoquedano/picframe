# Modelo de sesión y estados

Session: source, output, Config, Inventory, decisiones por image_id, selección actual,
analysis_complete, detector preparado, tarea activa y resultado de exportación.

Análisis: fila del motor + firma de entrada (size/mtime/dev/inode), huella de Config,
identidad del modelo y correcciones manuales. No contiene imágenes originales.
Preview: buffer RGB reducido y dimensiones originales; se libera al cambiar selección.

Estados: idle → analyzing → ready | cancelled | error; ready → exporting → finished | cancelled | error.
Cambiar parámetros/carpetas invalida ready; exportación deshabilitada hasta reanalizar.
La selección manual y el recorte actualizan solo la decisión de esa imagen, sin alterar Config.
Al exportar se verifica firma y huella; una entrada obsoleta genera error, no salida incorrecta.
Cerrar con tarea activa: requesting_close → cancel → finished → close, sin terminate().
