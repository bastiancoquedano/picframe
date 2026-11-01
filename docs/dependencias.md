# Dependencias efectivas — 2026-11-01

Python 3.11.16, macOS arm64. Instalación comprobada con `uv sync --locked --extra detector`.
Dependencias principales: Ultralytics 8.4.197, OpenCV 4.13.0.92, torch 2.15.0,
torchvision 0.29.2, NumPy 2.4.6 y Pillow 13.0.0. Hay una sola distribución cv2.
La combinación pasó inferencia CPU, prueba offline y preparación MPS en este Mac.

El extra `detector` incorpora YOLO/torch/OpenCV. Sin ese extra se pueden ejecutar las pruebas
con detector simulado y la geometría. Qt/PySide6 no está incorporado en este prototipo CLI.
Hatchling es una dependencia de construcción; las dependencias efectivas se fijan en uv.lock.

Inventario extraído de los metadatos instalados, incluyendo desarrollo y transitivas:

| Distribución | Versión | Licencia declarada / referencia |
| --- | --- | --- |
| anyio | 4.16.0 | MIT |
| attrs | 26.1.0 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| charset-normalizer | 3.5.2 | MIT |
| contourpy | 1.3.3 | BSD 3-Clause License |
| cycler | 0.12.1 | Copyright (c) 2015, matplotlib project |
| filelock | 4.2.6 | MIT |
| fonttools | 4.68.0 | MIT |
| fsspec | 2026.9.0 | BSD-3-Clause |
| h11 | 0.16.0 | MIT |
| httpcore | 1.0.9 | BSD-3-Clause |
| httpx | 0.28.1 | BSD-3-Clause |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.1 | MIT |
| Jinja2 | 3.1.6 | Consultar distribución |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| kiwisolver | 1.5.1 | ========================= |
| MarkupSafe | 3.0.4 | BSD-3-Clause |
| matplotlib | 3.11.2 | License agreement for matplotlib versions 1.3.0 and later |
| mpmath | 1.3.0 | BSD |
| networkx | 3.6.1 | BSD-3-Clause |
| numpy | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| nvidia-ml-py | 13.615.71 | BSD |
| opencv-python | 4.13.0.92 | Apache 2.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pillow | 13.0.0 | MIT-CMU |
| pluggy | 1.7.0 | MIT |
| polars | 2.1.0 | Copyright (c) 2025 Ritchie Vink |
| polars-runtime-32 | 2.1.0 | Consultar distribución |
| psutil | 7.2.2 | BSD-3-Clause |
| Pygments | 2.21.0 | BSD-2-Clause |
| pyparsing | 3.3.3 | MIT |
| pytest | 9.2.0 | MIT |
| python-dateutil | 4.0.0 | BSD-3-Clause |
| referencing | 0.37.0 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| rpds-py | 2026.9.1 | MIT |
| ruff | 0.17.3 | MIT |
| setuptools | 84.2.1 | MIT |
| sympy | 1.14.0 | BSD |
| torch | 2.15.0 | Consultar metadatos y LICENSE de la distribución |
| torchvision | 0.29.2 | BSD |
| typing_extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.6 | Apache-2.0 |
| ultralytics | 8.4.197 | AGPL-3.0 |
| ultralytics-platform | 0.1.102 | AGPL-3.0-only |
| ultralytics-thop | 2.2.4 | AGPL-3.0 |
| urllib3 | 2.8.0 | MIT |

Las expresiones anteriores son metadatos declarados, no una conclusión de compatibilidad legal.
Consultar también los archivos LICENSE y avisos de cada distribución antes de distribuir.
No se ha elegido licencia propia de distribución para Raceframe. El propietario autorizó subir
el código del proyecto a GitHub; no se suben dependencias, modelos ni fotografías.

Fuentes primarias:
- [Dependencias de Ultralytics fijado](https://raw.githubusercontent.com/ultralytics/ultralytics/v8.4.197/pyproject.toml).
- [Licencia Ultralytics](https://github.com/ultralytics/ultralytics/blob/main/LICENSE).
- [OpenCV](https://pypi.org/project/opencv-python/4.13.0.92/).
- [PyTorch](https://pypi.org/project/torch/2.15.0/).
- [Pillow](https://pypi.org/project/pillow/13.0.0/).

## Conservación estricta de metadatos

ExifTool oficial 13.58 (Perl), revisión 38bdbace3037a89d2c332664fc60bddad118958a,
preparado en .runtime/exiftool y excluido de Git. Fuente: https://github.com/exiftool/exiftool .
Licencias: https://exiftool.org/#license (mismas condiciones que Perl, consultar distribución).
Alternativa: exiftool del sistema o variable RACEFRAME_EXIFTOOL. CI instala el paquete oficial
de la distribución Ubuntu. El script de preparación verifica la revisión local fijada.
