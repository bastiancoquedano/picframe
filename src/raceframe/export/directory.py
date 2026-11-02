"""Reserva exclusiva de carpetas de trabajo sin sobrescrituras."""

from pathlib import Path


def validate_job_name(name):
    if not isinstance(name, str) or any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise ValueError("El nombre de carpeta contiene caracteres no válidos.")
    name = name.strip()
    if not name or name in {".", ".."} or any(char in name for char in "/\\:"):
        raise ValueError("Escribe un nombre de carpeta, sin rutas ni /, \\ o :.")
    if len(name.encode("utf-8")) > 200:
        raise ValueError("El nombre de carpeta es demasiado largo (máximo 200 bytes UTF-8).")
    return name


def create_job_directory(root, name, job_id):
    base = f"job-{job_id}" if name is None else validate_job_name(name)
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        candidate = root / (base if index == 1 else f"{base} ({index})")
        try:
            candidate.mkdir()
        except FileExistsError:
            index += 1
        else:
            return candidate
