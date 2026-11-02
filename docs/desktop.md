# Picframe de escritorio — 0.3.0

## Abrir en este Mac

La aplicación preparada está en `dist/Picframe.app`, dentro del proyecto. Abrirla con doble clic
en Finder. Incluye modelo y ExifTool; no necesita terminal ni red durante el procesamiento.

1. Elegir origen y destino. En **Nombre de carpeta** escribir cómo se llamará el trabajo
   (por defecto `Picframe_AAAA-MM-DD`). Se crea dentro del destino; si ya existe, se añade
   `(2)`, `(3)`, etc., sin sobrescribir. Cambiar solo el nombre conserva el análisis. Sin subcarpetas propone `exportaciones` dentro del origen;
   con subcarpetas el destino debe quedar fuera del árbol de entrada.
2. Ajustar modo, proporción, margen y composición. Más opciones permite calidad, focal,
   resolución mínima, dispositivo y modelo local.
3. Pulsar **Analizar fotografías**. No se exportan JPEG todavía.
4. Elegir una foto de la lista. A la izquierda se ven sujetos y recorte; a la derecha, el resultado.
   Sobre la lista, **Necesitan revisión** muestra las fotos ambiguas, sin protagonista o
   con errores; **Todas** recupera el lote completo. El contador muestra visibles y pendientes.
   Elegir una persona válida retira la foto del filtro y avanza a la siguiente pendiente;
   para ajustar después su recorte, vuelve a **Todas**. Si no quedan pendientes, se limpian
   las vistas previas. El filtro conserva los ajustes y **no limita la exportación**.
5. Para una ambigua, elegir otro sujeto en la lista desplegable o pulsar su caja en el original.
6. **Dibujar recorte** permite arrastrar en el original. Se conserva proporción y se rechaza un
   rectángulo que excluya al sujeto protegido o incumpla la resolución mínima.
7. **Volver a automático** restaura la decisión analizada de esa fotografía.
8. Pulsar **Exportar resultados**. Usa las decisiones revisadas sin repetir detección y verifica
   metadatos antes de publicar. **Abrir último resultado** abre la carpeta en Finder.

Cambiar parámetros/carpetas invalida el análisis anterior. Si cambiaron los archivos, se requiere
reanalizar. Cancelar y cerrar son cooperativos: puede terminar la imagen activa antes de cerrarse.
Los errores aparecen en el estado y el manifiesto; originales y salidas existentes no se sobrescriben.

No se excluyen personas por espalda. **Conservar grupo** es una opción explícita. Las ambiguas
se copian sin cambios mientras no se resuelva su selección.

## Entorno de desarrollo y construcción

Comandos de referencia para el agente, no requeridos para el fotógrafo:

```sh
uv sync --locked --extra detector --extra gui --extra build
uv run --no-sync python scripts/prepare_model.py
uv run --no-sync python scripts/prepare_metadata_tool.py
uv run --no-sync picframe-gui
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
con metadata_verified. La apertura nativa se observó en Raceframe 0.2.0; los incrementos
Picframe incluyen regresión Qt offscreen, captura sintética y diagnóstico del bundle.
La muestra pequeña no completa las tareas fotográficas y de volumen del CLI.

## Categoría y selección

En **Encuadre → Sujetos** elegir Personas, Animales o Vehículos. En **Selección**:
- **Protagonista dominante** (inicial): área claramente mayor, al menos 1,5 veces la segunda.
  Confianza/área mínimas siguen siendo necesarias. Más opciones permite cambiar Ventaja de tamaño.
- **Conservar grupo**: unión de candidatos confiables de la categoría elegida; si no cabe, revisión.
- **Revisión manual**: puntuación conservadora previa; permite elegir entre candidatos inciertos.

Personas puede proteger también bicicletas, motos o caballos asociados geométricamente.
Animales/Vehículos incluyen personas asociadas a caballo/bicicleta/moto. Parejas dudosas requieren
revisión; una elección manual protege todos sus compañeros plausibles. No reconoce montar
semánticamente. Las cajas y selección alternativa muestran el nombre de cada clase.

Animales admitidos: aves, gatos, perros, caballos, ovejas, vacas, elefantes, osos, cebras y jirafas.
Vehículos admitidos: bicicletas, autos, motos, aviones, buses, trenes, camiones y embarcaciones.
Otras especies/tipos pueden no detectarse. No usa clasificación de espectadores ni poses.
Tercio superior solo persona individual. Conjuntos, grupos y objetos se encuadran por su eje
limitante con focal larga; con focal corta/ausente se conserva contexto. Integridad y resolución
tienen prioridad; una escena sin margen de recorte puede conservarse completa.

Cambiar categoría, estrategia o ventaja de tamaño exige volver a analizar. Filtro Necesitan
revisión incluye las incertidumbres nuevas. Un sujeto grande cercano aún podría ser un espectador;
revise la propuesta antes de exportar. Precisión de las asociaciones pendiente de evaluación real.
