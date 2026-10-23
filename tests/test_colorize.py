import pytest

from comic2svg.colorize import PaletteColorizer, get_colorizer


def test_get_colorizer_palette():
    col = get_colorizer("palette")
    assert isinstance(col, PaletteColorizer)
    assert col.name == "palette"


def test_get_colorizer_unknown():
    with pytest.raises(KeyError):
        get_colorizer("unknown_engine")
