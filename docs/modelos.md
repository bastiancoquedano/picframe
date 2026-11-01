# Modelo local preparado

- Modelo: YOLO11n, detección COCO, clase person.
- Origen: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt
- Archivo: `models/yolo11n.pt`, excluido de Git.
- Tamaño descargado: 5.613.764 bytes.
- SHA-256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Preparado y comprobado el 2026-11-01. Inferencia real CPU aprobada; coordenadas de personas
  comprobadas sobre bus.jpg, muestra pública incluida en Ultralytics (no fotografías del usuario).
- Uso personal inicial. Ultralytics publica código y pesos bajo sus condiciones AGPL-3.0 y
  alternativa Enterprise: [condiciones del proveedor](https://www.ultralytics.com/license).
  Este registro no constituye una licencia nueva ni una evaluación jurídica de distribución.

Preparación explícita y repetible, separada del procesamiento:

```sh
uv sync --locked --extra detector
uv run --no-sync python scripts/prepare_model.py
```

El script verifica el hash y no sobrescribe un archivo distinto. Requiere red únicamente para
la descarga inicial; `raceframe process` exige ruta local existente y no descarga modelos.
En el Mac de desarrollo las dependencias y pesos ya están preparados.
