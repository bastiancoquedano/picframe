# Marcas de agua en Picframe 0.4.1

La pestaña **Marcas de agua** aplica marcas a JPEG completos sin recortarlos. Los originales se abren
solo para lectura. Cada lote crea una carpeta de trabajo con manifiesto, diario y salidas exclusivas;
el nombre visible del trabajo se puede elegir y las colisiones reciben sufijos.

En **Tradicional**, elige uno o varios PNG con transparencia, su tamaño, posición, opacidad y si quieres
repetirlos como patrón. También puedes añadir una identificación en texto o PNG, dibujada encima de las
marcas principales. El preview compara la primera fotografía antes y después. La exportación JPEG
conserva dimensiones orientadas y verifica la transferencia de EXIF, MakerNotes, ICC, IPTC, XMP y otros
bloques admitidos antes de publicar.

En **Smart**, se usa un PNG principal y una máscara local de personas de Apple Vision. La marca se
compone detrás de las siluetas detectadas; la identificación opcional se dibuja al final. Vision trabaja
con el mapa semántico conjunto de personas y no separa individuos para esta primera versión. Animales,
vehículos y otros objetos no se segmentan.

Si Vision falla, la máscara está vacía de forma sospechosa o no alcanza confianza suficiente, Picframe
registra la causa y marca la foto para revisión. El fallback inicial aprobado pone la marca delante de la
persona. Puedes cambiarlo por copia byte-a-byte del original (también marcada para revisión) u omitir
la foto y registrar error. El lote sigue con las demás fotos. Una máscara válida completamente vacía
significa que no se detectaron personas: Smart aplica la marca al marco completo y no marca revisión.

Los presets son JSON locales con versión, rutas y SHA-256 de los PNG, guardados en
`~/Library/Application Support/Picframe/watermark-presets`. Si se mueve o reemplaza un PNG, el preset
indica que falta o cambió el recurso. Los archivos de marca, presets, fotografías y resultados no se
incorporan al repositorio.

Tradicional solo requiere Pillow y no importa NumPy ni Vision. Smart necesita el extra opcional
`watermark-vision` en macOS; si el framework no está disponible, activa el fallback elegido y marca
las fotos para revisión. Aunque
las pruebas sintéticas verifican orden de composición, exportación, fallback, auditoría y tamaño, no
miden la precisión visual con corredores reales. Antes de usar Smart en un lote de entrega, revisa las
fotos con personas pequeñas, ropa de bajo contraste, movimiento, oclusiones y bordes complejos.

Desarrollo y build local:

```sh
uv sync --locked --extra detector --extra gui --extra build --extra watermark-vision
uv run --no-sync python scripts/vision_spike.py /ruta/local/foto.jpg
uv run --no-sync python scripts/build_macos.py
```

El diagnóstico `vision_spike.py` no guarda ni transmite la foto; imprime dimensiones, revisión, backend,
estado de máscara y píxeles confiables. Una figura geométrica sintética se trata como baja confianza,
así que ese resultado confirma que el fallback se activa, no que la máscara sirva para corredores reales.
