# Validación del primer incremento — 2026-11-01

## Alcance real

T001–T011 y T013 completadas (12/44). Paquete instalable, ayuda/versión, CI configurada,
fixtures sintéticos, tipos puros, configuración, inventario revalidado, lectura JPEG y
geometría conservadora/original. No incluye selección automática, exportación, lotes,
manifiesto, cancelación, YOLO ni GUI. No declara aceptación del MVP.

## Evidencia de desarrollo

- Las pruebas de configuración/descubrimiento se escribieron antes de sus módulos y fallaron
  inicialmente por ausencia de implementación. Tras implementarlos: 37 pruebas aprobadas.
- Las pruebas de orientación se escribieron antes del loader y fallaron inicialmente por
  módulo ausente. Con Pillow y lectura implementados: 50 pruebas aprobadas.
- Las pruebas de recorte se escribieron antes del motor y fallaron inicialmente por módulo
  ausente. Se añadieron regresiones de redondeo en imágenes estrechas y números enormes.
- La regresión JSON null reprodujo la aceptación incorrecta de configuración no objeto;
  se corrigió para rechazarla explícitamente.
- Verificaciones finales: pytest, ruff check, ruff format --check, instalación reproducible
  y entry point --version. Ver resultado exacto en el resumen del commit/informe de entrega.

## Casos cubiertos

Conservación de imagen centrada, sujeto lateral, cuerpo completo junto al borde, plano medio,
márgenes recortados al lienzo, redondeo exterior, proporción original, imágenes verticales,
dimensiones pequeñas y 200 cajas pseudoaleatorias reproducibles. La suite comprueba que el
recorte conserva al menos el 85 % del área, contiene la región protegida y mejora el centrado.

EXIF 1–8: dimensiones y color de una esquina asimétrica para comprobar rotación/reflejo,
etiqueta de cámara conservada, archivo original sin cambios, ICC capturado y recursos cerrados.
JPEG dañado y formato ajeno disfrazado de .jpg se rechazan.

Inventario: nombres Unicode, mayúsculas, recursión, enlaces de directorio, enlaces fuera de
raíz, destinos equivalentes al origen y entrada sustituida/modificada. Configuración: JSON
no objeto, claves duplicadas/desconocidas, valores no finitos, bool numérico y parámetros inválidos.

Una prueba en proceso nuevo confirma que importar la geometría no carga PIL, cv2, torch,
ultralytics ni PySide6. Todas las fotografías se generan en carpetas temporales.

## Limitaciones y siguiente incremento

La geometría recibe la caja del sujeto; todavía no la detecta. Solo se admiten modo conservador
y proporción original; los otros modos/proporciones se rechazan explícitamente hasta US4.
Proteger una caja no garantiza identificar todas las extremidades reales. No se procesaron
fotos privadas ni se midió un evento. CI está configurada; una ejecución remota aprobada
solo se afirmará si se comprueba en GitHub.

Siguiente: T012/T014, pruebas e implementación de exportación JPEG/copia segura sin reemplazo.
T044 y T041 permanecen pendientes porque incluyen validación del prototipo completo.
