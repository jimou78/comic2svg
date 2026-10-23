"""Colorization module architecture for comic2svg.

Provides pluggable base interfaces for rule-based palette filling and
deep-learning-based line art colorization (v0.2 Roadmap).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Type


class ColorizeEngine(ABC):
    """Abstract Base Class for colorization backends."""

    name: str = "base"

    @abstractmethod
    def colorize(self, lineart_path: Path, output_path: Path, **kwargs) -> Path:
        """Apply colorization to a line art image or SVG path."""
        pass


class PaletteColorizer(ColorizeEngine):
    """Rule-based flood fill colorizer using predefined color swatches."""

    name: str = "palette"

    def __init__(self, palette: Optional[Dict[str, str]] = None):
        self.palette = palette or {
            "skin": "#FCD0A1",
            "hair": "#3B2F2F",
            "cloth_primary": "#4A6FA5",
            "paper": "#FAF3E0",
        }

    def colorize(self, lineart_path: Path, output_path: Path, **kwargs) -> Path:
        """Placeholder for palette-based region colorization."""
        # Future v0.2 implementation: Connected-component contour segmentation
        # and seed-based flood fill with specified color palette
        raise NotImplementedError(
            "PaletteColorizer will be available in v0.2.0. "
            "Track progress at https://github.com/jimou78/comic2svg/issues"
        )


# Engine Registry
_REGISTRY: Dict[str, Type[ColorizeEngine]] = {
    "palette": PaletteColorizer,
}


def get_colorizer(name: str) -> ColorizeEngine:
    """Instantiate a colorizer by backend name."""
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown colorizer '{name}'. Available: {list(_REGISTRY.keys())}"
        )
    return _REGISTRY[name]()
