# Implementation Plan: Reencuadre seguro por lotes

**Branch**: `main` | **Date**: 2026-11-01 | **Spec**: [spec.md](spec.md)

**Input**: especificación clarificada en `specs/001-reencuadre-cli/spec.md`.
El resolvedor Spec Kit devuelve el identificador lógico `001-reencuadre-cli`; Git continúa en main.

## Summary

Construir posteriormente un CLI local que detecta personas, selecciona un protagonista,
calcula un recorte seguro y exporta a un directorio independiente con manifiesto auditable.
Las fotos inciertas se copian byte por byte y se marcan para revisión. El diseño separa
geometría pura de modelos, lectura/exportación y orquestación. No se implementa código aquí.

## Technical Context

**Language/Version**: Python 3.11.16, uv, tipado y dataclasses.

**Primary Dependencies**: candidatas Ultralytics 8.4.197, YOLO11n, Pillow 13.0.0,
opencv-python 4.13.0.92, torch 2.15 y torchvision compatible; NumPy transitivo.
Resolver compatibilidad y fijar lock durante integración antes de descargar pesos.
No añadir headless junto a opencv-python. PySide6 diferido a GUI.

**Storage**: archivos locales, inventario JSON, eventos JSONL y manifiesto JSON final; sin base de datos.

**Testing**: pytest, ruff; detector simulado para geometría/selección, inferencia real separada;
orientaciones EXIF 1–8, exportación y fallos inyectados con imágenes sintéticas.

**Target Platform**: Mac arm64 del propietario, macOS 26.6.2; CPU referencia y MPS opcional.
macOS 14+ candidato por ruedas, sin declarar una matriz soportada hasta probarla.

**Project Type**: paquete Python y CLI; sin interfaz en este incremento.

**Performance Goals**: lotes de 2.000–3.500 fotos, una imagen activa y un modelo cargado;
medir tiempo, throughput y RSS máximo sin inventar SLA ni cifras de RAM.

**Constraints**: offline con pesos preparados, originales inmutables, sin regeneración de píxeles,
exportación sin reemplazo, incertidumbre explícita, cancelación cooperativa.

**Scale/Scope**: un trabajo secuencial por proceso; no entrenar, RAW, GUI, pose, historial ni reanudación.

## Constitution Check

Puertas de diseño comprobadas antes de investigación y repetidas al cerrar el diseño.
El cumplimiento de ejecución debe verificarse durante implementación, no se presume.

| Principio | Antes | Después / evidencia de diseño |
| --- | --- | --- |
| I. Privacidad | Conforme | Pesos locales, configuración offline, prueba con red bloqueada |
| II. Originales | Conforme | Validación de rutas, destino por trabajo, publicación sin reemplazo |
| III. Encuadre | Conforme | Restricciones geométricas y límites de pérdida de área |
| IV. Incertidumbre | Conforme | Estados separados y copia exacta para revisión |
| V. Modularidad | Conforme | Detector sustituible; geometría sin Qt, YOLO ni OpenCV |
| VI. Calidad | Conforme | Matriz de pruebas y revisión de 30–50 fotos reales |
| VII. Robustez | Conforme | Una foto activa, diario, CPU y cancelación |
| VIII. SDD | Conforme | Bootstrap aprobado, dos respuestas integradas; diseño sin implementación |

No se requiere excepción constitucional. Los riesgos de integración se convierten en puertas
verificables: dependencias conjuntas, offline real, metadatos Canon y publicación en el volumen elegido.

## Project Structure

### Documentation (this feature)

```text
specs/001-reencuadre-cli/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── clarification-review.md
├── checklists/requirements.md
└── contracts/
    ├── cli.md
    └── manifest.md
```

Tareas se generarán mediante speckit-tasks posteriormente; no se crean con este plan.

### Source Code (repository root)

Estructura propuesta para implementar; todavía no existen estos módulos.

```text
src/raceframe/
├── __init__.py
├── __main__.py
├── config.py
├── core/
│   ├── models.py
│   ├── detection.py
│   ├── selection.py
│   ├── cropping.py
│   └── processing.py
├── imaging/
│   ├── discovery.py
│   └── loader.py
├── export/
│   ├── jpeg.py
│   └── manifest.py
└── cli/
    └── main.py
tests/
├── unit/
├── integration/
└── fixtures/
```

**Structure Decision**: un solo paquete; interfaces Protocol mínimas para detector y cancelación,
sin repositorios genéricos ni capas de servicios. La geometría importa únicamente tipos puros.
El adaptador YOLO se importa tarde y una sola vez; la CLI comparte el núcleo con Qt futuro.
No crear todavía paquetes vacíos para funcionalidades futuras.

## Selección y parámetros iniciales

Valores de arranque reproducibles; deben revisarse con la muestra real antes de aceptar el MVP.
Puntuación en [0,1]: 0,35 centralidad + 0,25 tamaño + 0,25 confianza + 0,15 aislamiento.
Centralidad = 1 - distancia euclídea del centro de caja al centro de imagen, normalizada por
la semidiagonal y acotada a [0,1]. Tamaño = raíz de área de caja / área de imagen.
Aislamiento = 1 - máxima IoU con otras cajas; con una sola persona vale 1. Es una señal
espacial, no prueba de visibilidad ni de que sea corredor. No se infiere identidad deportiva.

Descartar cajas degeneradas/no finitas; limitar cajas a la imagen con advertencia.
Detector: confianza mínima 0,35, clase persona; elegible para recorte: confianza >=0,50,
área relativa >=0,005 y puntuación >=0,55. Si el candidato mejor no es elegible, revisión.
Si el segundo candidato válido queda a distancia <=0,08 del primero, revisión por ambigüedad,
aunque ese segundo no alcance el umbral de recorte. Orden determinista por puntuación,
confianza y coordenadas; no resolver un empate eligiendo por orden de detección.
Registrar todas las detecciones devueltas y los motivos de descarte.

## Geometría propuesta

- Cajas continuas xyxy en coordenadas de imagen orientada, límites superiores exclusivos.
- Región protegida: caja seleccionada ampliada por margen fraccional de su propio ancho/alto,
  recortada a límites de imagen. Margen predeterminado 0,08 en todos los modos, configurable entre 0 y 0,5.
- Área de referencia: el mayor rectángulo inscrito de la proporción solicitada. Para original,
  equivale al área completa; para otra proporción, separa la pérdida obligatoria de formato de
  la pérdida adicional de composición. Retención mínima de esa área: conservador 0,85;
  equilibrado 0,70; cerrado 0,50. Registrar también la fracción del área original preservada.
  Estos límites no garantizan que se pueda centrar al sujeto ni que quepa su región protegida.
- Proporción original o ancho:alto literal 3:2 / 4:5. No ampliar ni estirar.
- Enumerar tamaños de recorte enteros por ancho; altura es la más cercana a ancho/proporción,
  con error máximo de un píxel, descartando tamaños fuera de imagen, menores al área mínima
  o que no contengan la región protegida (redondeada hacia fuera).
- Para cada tamaño, determinar el intervalo de x que mantiene la región protegida y el recorte
  dentro de imagen. Elegir el x entero más próximo al centrado horizontal del protagonista.
  Elegir y próximo al centro vertical original sujeto a contener la región protegida.
- Elegir primero el mínimo error horizontal normalizado por ancho del recorte; a igualdad
  numérica, máxima área, menor desplazamiento vertical y orden estable de coordenadas.
  Si no hay candidato, copiar original para revisión y registrar proporción/contexto inviable.
- El conjunto de tamaños es anidado por modo, con el mismo margen: la solución no pierde
  más área en conservador que en equilibrado ni en equilibrado que en cerrado. Verificar esta
  propiedad con pruebas; no asumirla cuando el usuario cambie otros parámetros entre trabajos.
- Si la proporción es original y el sujeto está a <=0,03 del centro en unidades de ancho
  original, conservar encuadre completo. También conservar si la mejora normalizada es <0,005.
  Aplicar esta regla a los tres modos para evitar recortes sin mejora; no impide proporciones explícitas.
- Ante incertidumbre, nunca ejecutar la optimización: copiar sin cambios y marcar para revisión.

## Exportación y recuperación

Ver contratos. Mantener un modelo y una imagen orientada; liberar arrays intermedios por foto.
JPEG recortado: calidad inicial 95, rango 1–95, sin escalado, ICC y EXIF explícitos.
Prueba en CPU obligatoria; comparar MPS en una muestra solo tras establecer referencia.

El inventario se materializa antes de procesar. Crear carpeta exclusiva job-<uuid> bajo destino
con mkdir sin exist_ok. Archivos JPEG al mismo nivel, sufijos __2, __3 para homónimos sin
alterar el nombre base. Preparar temporal en ese mismo volumen, calcular hash, registrar intención,
publicar sin reemplazo y confirmar en diario. Fallo de auditoría detiene el trabajo.
Las rutas de entrada se revalidan al abrir para no seguir enlaces fuera del inventario permitido.

## Verificación y secuencia de entrega posterior

1. Tipos/configuración y geometría con pruebas de restricciones; sin YOLO.
2. Selección explicable y casos de ambigüedad con detector simulado.
3. Descubrimiento, EXIF y exportación con preservación de originales y fallos inyectados.
4. Diario, manifiesto, cancelación y CLI integrada con detector simulado.
5. Resolver y fijar dependencias; inventariar licencias; preparar pesos explícitamente;
   inferencia real CPU y prueba offline con red bloqueada.
6. Revisión conjunta de 30–50 fotos y medición de lote grande; corregir antes de declarar aceptación.

Esta secuencia orienta la siguiente etapa; no reemplaza tasks.md ni autoriza omitirla.

## Complexity Tracking

Sin violaciones ni complejidad adicional que justificar. El diario se necesita para distinguir
salidas completas de trabajos interrumpidos; no introduce una base de datos ni reanudación automática.

## Refinamiento de metadatos y composición por focal — 2026-11-01

Reemplazar exportación EXIF reconstruida selectivamente por conservación de APP/COM originales.
ExifTool oficial 13.58 en .runtime o instalación del sistema actualiza solo los campos derivados.
Comparar todos los valores extraídos, incluidos MakerNotes; comprobar literalmente los otros
bloques APP/COM. Rechazar un recorte si la comparación falla o hay metadatos entre escaneos
JPEG aún no soportados. No modificar originales. Las advertencias de pérdida de MakerNotes
son comportamiento histórico sustituido por FR-028.

Política por focal real: umbral >=70 mm, ocupación objetivo 0,75 y lado largo mínimo 3000 px,
configurables. Geometría pura evalúa tamaños que contienen región protegida y minimiza distancia
al objetivo de ocupación, luego desplazamiento del sujeto. Evitar recortar más una imagen que
ya tiene protagonista grande. Para angular/focal desconocida reutilizar motor de contexto.
El manifiesto añade focal, ocupación original/final y configuración efectiva. Esta política
prima sobre la retención de área de los modos; --framing-policy context recupera el criterio previo.
