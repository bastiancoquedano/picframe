# Raceframe de escritorio — 0.2.1

## Abrir en este Mac

La aplicación preparada está en `dist/Raceframe.app`, dentro del proyecto. Abrirla con doble clic
en Finder. Incluye modelo y ExifTool; no necesita terminal ni red durante el procesamiento.

1. Elegir origen y destino. En **Nombre de carpeta** escribir cómo se llamará el trabajo
   (por defecto `Raceframe_AAAA-MM-DD`). Se crea dentro del destino; si ya existe, se añade
   `(2)`, `(3)`, etc., sin sobrescribir. Cambiar solo el nombre conserva el análisis. Sin subcarpetas propone `exportaciones` dentro del origen;
   con subcarpetas el destino debe quedar fuera del árbol de entrada.
2. Ajustar modo, proporción, margen y composición. Más opciones permite calidad, focal,
   resolución mínima, dispositivo y modelo local.
3. Pulsar **Analizar fotografías**. No se exportan JPEG todavía.
4. Elegir una foto de la lista. A la izquierda se ven personas y recorte; a la derecha, el resultado.
5. Para una ambigua, elegir otra persona en la lista desplegable o pulsar su caja en el original.
6. **Dibujar recorte** permite arrastrar en el original. Se conserva proporción y se rechaza un
   rectángulo que excluya al sujeto protegido o incumpla la resolución mínima.
7. **Volver a automático** restaura la decisión analizada de esa fotografía.
8. Pulsar **Exportar resultados**. Usa las decisiones revisadas sin repetir detección y verifica
   metadatos antes de publicar. **Abrir último resultado** abre la carpeta en Finder.

Cambiar parámetros/carpetas invalida el análisis anterior. Si cambiaron los archivos, se requiere
reanalizar. Cancelar y cerrar son cooperativos: puede terminar la imagen activa antes de cerrarse.
Los errores aparecen en el estado y el manifiesto; originales y salidas existentes no se sobrescriben.

No se excluyen personas por espalda ni se aplica agrupamiento automático. Las ambiguas se copian
sin cambios si no se elige manualmente un protagonista.

## Entorno de desarrollo y construcción

Comandos de referencia para el agente, no requeridos para el fotógrafo:

```sh
uv sync --locked --extra detector --extra gui --extra build
uv run --no-sync python scripts/prepare_model.py
uv run --no-sync python scripts/prepare_metadata_tool.py
uv run --no-sync raceframe-gui
uv run --no-sync python scripts/build_macos.py
```

Qt Widgets usa PySide6 Essentials 6.12.0; no incorpora WebEngine/PDF innecesarios.
Build con PyInstaller 6.22.3, arm64/onedir/windowed, pesos locales, ExifTool y su lib.
El hook propio recoge _C_stable.so/image_stable.so de torchvision 0.29.2; los hooks anteriores
solo reconocían el nombre nativo antiguo. Se incorporan metadatos de dependencias para auditoría.

## Alcance de distribución

Bundle probado localmente en este Mac, con firma ad hoc para sus binarios arm64.
No tiene Developer ID ni notarización; no se declara distribución validada para otros equipos.
ExifTool requiere `/usr/bin/perl`, presente en este Mac. No se desactiva Gatekeeper ni se
elimina cuarentena. Licencias de Qt/Ultralytics/Perl deben revisarse antes de distribuir.
El bundle, pesos, herramientas y resultados privados están fuera de Git.

## Validación

Pruebas Qt offscreen cubren selección, drag real, recorte manual exportado, invalidación,
progreso y cierre cooperativo. Detector real en QThread mantiene eventos de interfaz activos.
El diagnóstico del bundle ejecutado bajo deny network* verificó inferencia CPU y exportación
con metadata_verified; después se comprobó la ventana nativa Raceframe 0.2.1.
La muestra pequeña no completa las tareas fotográficas y de volumen del CLI.
