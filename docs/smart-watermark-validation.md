# Validación de Smart Watermark — 2026-11-14

Picframe 0.4.1 se construyó en macOS 26.6.2 arm64 con Python 3.11, PyInstaller 6.22.3,
PyObjC Vision 13.0 y los recursos locales del proyecto.

- `uv lock --check` confirmó sincronía con `pyproject.toml`.
- `ruff check .` y `ruff format --check .` pasaron.
- Suite sin marcadores de runtime real: **246 passed, 5 deselected**. Incluye compositor RGBA,
  resolución/orientación/metadatos, presets, UI, los tres fallbacks, fallos por foto, cancelación,
  publicación atómica y un inventario sintético de 1.000 fotos.
- Marcadores `real_model or real_vision`: **5 passed, 246 deselected**. Incluyen detector local,
  ejecución sin red y llamada local Apple Vision con una imagen sintética.
- `dist/Picframe.app` contiene PyObjC Vision. El smoke de la app con `sandbox-exec` y `deny network*`
  verificó creación Qt, pestaña Marcas de agua, import de Vision, inferencia local del detector y
  exportación con `metadata_verified`. La figura sintética produjo máscara de baja confianza; Smart
  registró revisión y aplicó el fallback configurado de copia byte-a-byte.
- `codesign --verify --deep --strict` pasó para el bundle firmado ad hoc.

La figura geométrica sintética no es una prueba de precisión con personas. El siguiente chequeo visual
debe hacerse con fotografías reales locales, mirando bordes, movimiento, grupos, ropa de bajo contraste
y personas pequeñas; esas fotos no se agregan al repositorio. El bundle no tiene Developer ID ni
notarización, por lo que la validación es local para este Mac. No se probó la ejecución en el mínimo
de macOS 12 ni en otro equipo.

## Corrección posterior al primer lote real

El lote Smart de prueba del propietario confirmó `mode=smart`, pero todas las fotos fallaron al crear
`VNImageRequestHandler` con `ValueError: NSInvalidArgumentException - key does not exist`. La causa fue
pasar `{}` como diccionario de opciones a `initWithCGImage_options_`; en el runtime actual ese argumento
vacío lanza una excepción. Picframe 0.4.1 pasa `None` (sin opciones). La misma prueba Vision sintética
vuelve a completar la solicitud: el smoke del bundle bajo `deny network*` devuelve `low_confidence_mask`
para la figura, en vez de la excepción de inicialización. El fallback de baja confianza de esa figura
sigue siendo esperado y no acredita precisión con corredores reales.
