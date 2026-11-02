import pytest

from raceframe.config import Config
from raceframe.core.cropping import preserves_well_framed
from raceframe.core.models import Box


@pytest.mark.parametrize(
    "box,person,expected",
    [
        (Box(900, 1170, 1800, 3870), True, True),  # rostro alto, cuerpo íntegro y margen
        (Box(100, 100, 2900, 4400), True, False),  # extremo inferior toca casi el borde
        (Box(900, 500, 1800, 2300), True, False),  # demasiado pequeño
        (Box(300, 500, 2700, 4100), False, True),  # vehículo/grupo bien proporcionado
        (Box(10, 500, 2410, 4100), False, False),  # margen lateral insuficiente
        (Box(200, 500, 800, 1100), False, False),  # ocupa poco encuadre
    ],
)
def test_well_framed_gate(box, person, expected):
    assert preserves_well_framed(3000, 4500, box, Config(), person=person) is expected


def test_explicit_crop_style_and_aspect_bypass_preservation():
    frame = Box(900, 1170, 1800, 3870)
    assert not preserves_well_framed(3000, 4500, frame, Config(mode="tight"), person=True)
    assert not preserves_well_framed(3000, 4500, frame, Config(aspect="3:2"), person=True)


def test_head_reference_position_and_occupancy_both_matter():
    config = Config(head_fraction=0.4)
    centered = Box(900, 850, 1800, 3550)
    assert preserves_well_framed(3000, 4500, centered, config, person=True)
    off_center = Box(1950, 1170, 2850, 3870)
    assert preserves_well_framed(3000, 4500, off_center, Config(), person=True)
    assert not preserves_well_framed(3000, 4500, off_center, config, person=True)
