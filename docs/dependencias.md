# Dependencias incorporadas — primer incremento

- Python 3.11.16: runtime existente en el Mac.
- Pillow 13.0.0: lectura JPEG, EXIF y perfil ICC; MIT-CMU según metadatos publicados.
- Hatchling: backend de construcción, rango >=1.27,<2; dependencia de build, sin ejecución fotográfica.
- pytest y ruff: desarrollo; versiones efectivas fijadas en uv.lock.

No se han incorporado Ultralytics, OpenCV, torch, torchvision ni Qt. Su evaluación conjunta,
versiones e inventario de licencias completo siguen pendientes en T019.
No se ha elegido una licencia de distribución propia para Raceframe.

Fuentes oficiales consultadas:
- [Pillow publicado](https://pypi.org/project/pillow/13.0.0/).
- [Normalización EXIF](https://pillow.readthedocs.io/en/stable/reference/ImageOps.html).
