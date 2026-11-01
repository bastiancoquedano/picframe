# Investigación y decisiones — 2026-11-01

Investigación documental con fuentes primarias; no se instalaron dependencias de ejecución,
no se descargaron modelos y no se ejecutó inferencia. Las candidatas no constituyen una
combinación validada. La integración deberá resolverlas, fijarlas en uv.lock y probarlas.

## Dependencias y plataforma

**Decisión:** mantener Python 3.11.16; evaluar primero ultralytics 8.4.197, Pillow 13.0.0,
opencv-python 4.13.0.92 y PyTorch 2.15 con torchvision compatible resuelto por sus metadatos.
Usar NumPy transitivo fijado en el lock. El paquete estándar de Ultralytics requiere
opencv-python: no añadir otra distribución cv2 en paralelo. Python argparse, dataclasses,
json, pathlib y signal cubren los demás contratos sin incorporar frameworks.

**Razón:** base publicada para Python 3.11 y arm64, conservando el ecosistema solicitado.
La compatibilidad de versiones conjuntas es una puerta de integración, no un resultado probado.
Primera plataforma de prueba: macOS 26.6.2 arm64, observada con sw_vers. Objetivo técnico inicial
macOS 14+ para estas ruedas; no implica soporte validado para todos esos sistemas.
La lectura de RAM mediante sysctl fue denegada por el sandbox; no se inventa una cifra.

**Alternativas:** variante oficial ultralytics-opencv-headless y OpenCV headless evitan
componentes GUI, pero cambiar de distribución no es necesario para el primer CLI. Nunca
instalar ambas variantes: comparten namespace. Qt/PySide6 se evalúa en la fase de interfaz.

Fuentes: [Ultralytics publicado](https://pypi.org/project/ultralytics/8.4.197/),
[dependencias oficiales](https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.197/pyproject.toml),
[OpenCV 4.13](https://pypi.org/project/opencv-python/4.13.0.92/),
[Pillow](https://pypi.org/project/pillow/), [PyTorch](https://pypi.org/project/torch/),
[torchvision](https://pypi.org/project/torchvision/).

## Modelo y dispositivo

**Decisión:** YOLO11n de detección de personas, pesos locales y entrada 640 como referencia
inicial, sin entrenamiento ni pose. CPU predeterminada; MPS opcional solo tras comprobación
real y prueba de inferencia. Registrar dispositivo efectivo, versión y hash del modelo.

**Razón:** el modelo pequeño permite empezar midiendo precisión/coste. No se afirma que sea
el más preciso ni rápido para este Mac. Evaluar un modelo mayor si falla la muestra real.
En auto, comprobar MPS y volver a CPU con advertencia si no está disponible o falla; en
mps explícito, informar error de preparación en lugar de cambiar silenciosamente la petición.

**Alternativas:** YOLO26 y modelos mayores se difieren para comparar con una base medida;
Core ML pertenece a optimización. La disponibilidad de MPS depende de sistema y runtime.

Fuentes: [YOLO11](https://docs.ultralytics.com/models/yolo11/),
[MPS oficial](https://docs.pytorch.org/docs/2.15/notes/mps.html).

## Procesamiento local y sin telemetría

**Decisión:** el procesamiento acepta exclusivamente una ruta de pesos existente y verificada;
no admite URLs ni descarga automática. Preparación de pesos fuera del trabajo fotográfico,
con origen y SHA-256 registrados. Configuración propia, sync=false y trackers desactivados;
verificar YOLO_OFFLINE=true y YOLO_AUTOINSTALL=false en la versión fijada antes de importarla.
No usar cuentas, HUB ni servicios de inferencia. Comprobar import e inferencia con red bloqueada.

**Razón:** los valores predeterminados de Ultralytics incluyen sincronización de analítica y
rutas de descarga. Configurar indicadores no demuestra por sí solo ausencia de conexiones.

**Alternativas:** confiar en los predeterminados o permitir descarga durante process incumple
la separación entre preparación y trabajo offline.

Fuentes: [settings](https://docs.ultralytics.com/usage/settings),
[código de inicialización](https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/utils/__init__.py).

## Orientación, coordenadas y metadatos

**Decisión:** Pillow abre y normaliza EXIF antes del detector; exporta JPEG y EXIF/ICC explícitos.
El adaptador recibe el array BGR orientado y devuelve cajas en dimensiones de esa entrada;
no aplicar dos veces el escalado que Ultralytics ya revierte. Verificar orig_shape y la
transformación con una prueba conocida. OpenCV convierte RGB/BGR; geometría pura sin cv2.

Copias sin cambios: bytes idénticos. Recortes: orientación 1 o ausente, dimensiones nuevas,
ICC conservado, EXIF conocido preservado, miniatura antigua eliminada. Auditar diferencias
con etiquetas legibles y advertir bloques no garantizados (MakerNotes/XMP/IPTC/APP desconocidos).
No prometer preservación universal de metadatos. Si un bloque no puede validarse, registrarlo.

Fuentes: [ImageOps](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html),
[JPEG](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html),
[Results](https://docs.ultralytics.com/modes/predict/).

## Geometría y selección

**Decisión:** puntuación explicable, motor de rectángulos con restricciones y conservación
mínima de área por modo; parámetros iniciales especificados en plan.md. Son hipótesis de
composición a validar, no constantes respaldadas por una medición fotográfica.

**Razón:** mover el recorte hacia un corredor manteniendo la proporción puede exigir perder
mucho entorno. Optimizar centrado sin un límite de área contradice el modo conservador.
La integridad de la caja y el margen factible tienen precedencia sobre todos los demás objetivos.

**Alternativas:** seleccionar solo por tamaño o forzar siempre el centrado ignora la idea fuente.
Pose, segmentación y reconocimiento de dorsal no se necesitan en este incremento.

## Escrituras y recuperación

**Decisión:** directorio exclusivo por trabajo, inventario y diario incremental; exportación a
un temporal del mismo volumen, flush/fsync, publicación sin reemplazo y registro confirmado.
Preferir enlace duro exclusivo os.link en volúmenes que lo soporten; si no, rechazar ese destino
con explicación antes de exportar. No asumir que os.replace evita sobrescribir fotografías.
El manifiesto final se deriva del diario; un trabajo abruptamente detenido se presenta como
interrumpido, nunca completado. Detalles en contracts/cli.md y data-model.md.

**Alternativas:** escribir directamente el JPEG final permite archivos parciales; reescribir
un manifiesto completo después de cada foto incurre en coste cuadrático evitable.

Fuente: [interfaces de archivos Python 3.11](https://docs.python.org/3.11/library/os.html).

## Licencias y uso

**Decisión:** uso personal confirmado, sin publicación ni empaquetado distributivo. Inventariar
licencias de dependencias y procedencia de pesos antes de incorporarlos. Ultralytics declara
AGPL-3.0 y alternativa Enterprise. La decisión personal no equivale a una exención general.
Pillow usa MIT-CMU; revisar las licencias transitivas del lock. PySide6/Qt puede involucrar
LGPL/GPL/comercial según componentes y modalidad: reabrir la evaluación al introducir GUI.

**Alternativas:** no elegir licencia definitiva de Raceframe ni comprometer distribución ahora.
Esta es una revisión de condiciones publicadas, no una conclusión jurídica de compatibilidad.

Fuentes: [proveedor Ultralytics](https://www.ultralytics.com/license),
[licencia del código](https://github.com/ultralytics/ultralytics/blob/main/LICENSE),
[Pillow](https://pypi.org/project/pillow/), [Qt para Python](https://doc.qt.io/qtforpython-6/licenses.html).
