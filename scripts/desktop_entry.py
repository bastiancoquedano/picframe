"""Punto de entrada para el bundle; diagnóstico local independiente de la interfaz."""

import sys


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--bundle-smoke":
        from raceframe.ui.smoke import run_smoke

        run_smoke(sys.argv[2])
        return 0
    from raceframe.ui.__main__ import main as gui_main

    return gui_main()


if __name__ == "__main__":
    raise SystemExit(main())
