"""Entrada inicial: solo ayuda y versión hasta integrar el procesamiento."""

import argparse

from raceframe import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="raceframe",
        description="Raceframe: motor en desarrollo; procesamiento aún no disponible.",
    )
    parser.add_argument("--version", action="version", version=f"Raceframe {__version__}")
    parser.parse_args(argv)
    parser.print_help()
    return 0
