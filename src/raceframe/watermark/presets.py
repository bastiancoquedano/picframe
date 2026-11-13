"""Presets JSON locales, con rutas/hash de PNG y reemplazo atómico."""

import json
import re
from pathlib import Path
from unicodedata import normalize

from raceframe.core.watermark_models import preset_from_dict, preset_to_dict
from raceframe.export.manifest import atomic_json


class WatermarkPresetStore:
    def __init__(self, directory=None):
        self.directory = Path(
            directory or Path.home() / "Library/Application Support/Picframe/watermark-presets"
        ).expanduser()

    @staticmethod
    def _filename(name):
        base = normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
        slug = re.sub(r"[^a-z0-9_-]+", "-", base).strip("-_")[:48] or "preset"
        return f"{slug}.json"

    def save(self, name, config):
        value = preset_to_dict(name, config)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / self._filename(value["name"])
        atomic_json(path, value)
        return path

    def names(self):
        if not self.directory.is_dir():
            return ()
        return tuple(
            preset_from_dict(json.loads(path.read_text(encoding="utf-8")))[0]
            for path in sorted(self.directory.glob("*.json"))
        )

    def load(self, name):
        path = self.directory / self._filename(name)
        if not path.is_file() or path.is_symlink():
            raise ValueError("No existe el preset local solicitado")
        preset = preset_from_dict(json.loads(path.read_text(encoding="utf-8")))
        if preset[0] != name:
            raise ValueError("El nombre del preset no coincide con el archivo")
        return preset
