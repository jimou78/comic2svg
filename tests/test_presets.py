import pytest

from comic2svg.presets import PresetConfig, get_preset, list_presets


def test_list_presets():
    presets = list_presets()
    assert len(presets) >= 4
    names = [p.name for p in presets]
    assert "vintage-comic" in names
    assert "clean-line" in names
    assert "woodblock" in names
    assert "color-flat" in names


def test_get_preset_success():
    cfg = get_preset("vintage-comic")
    assert isinstance(cfg, PresetConfig)
    assert cfg.name == "vintage-comic"
    assert cfg.color_mode == "binary"
    assert cfg.adaptive_block_size % 2 == 1  # must be odd


def test_get_preset_case_insensitive():
    cfg = get_preset("VINTAGE-COMIC")
    assert cfg.name == "vintage-comic"


def test_get_preset_invalid():
    with pytest.raises(ValueError) as exc:
        get_preset("non_existent_preset")
    assert "Unknown preset" in str(exc.value)
