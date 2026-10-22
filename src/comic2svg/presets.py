"""Preset configurations for comic2svg.

Presets provide finely tuned preprocessing and vectorization parameters
for various types of scanned artwork, from yellowed vintage paperbacks to
modern crisp line drawings.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class PresetConfig:
    """Configuration settings for preprocessing and vectorization."""

    name: str
    description: str

    # Preprocessing parameters
    denoise_h: float = 10.0
    adaptive_block_size: int = 31
    adaptive_c: float = 12.0
    despeckle_size: int = 4
    contrast_stretch: bool = True
    deskew: bool = False

    # Vectorization parameters
    color_mode: str = "binary"  # "binary" or "color"
    filter_speckle: int = 4
    corner_threshold: int = 60
    length_threshold: float = 4.0
    splice_threshold: int = 45
    path_precision: int = 3


PRESETS: Dict[str, PresetConfig] = {
    "vintage-comic": PresetConfig(
        name="vintage-comic",
        description=(
            "Optimized for aged/yellowed picture books (小人书) and vintage comics. "
            "Applies adaptive thresholding to remove yellow backgrounds and ink bleed "
            "while retaining fragile line strokes."
        ),
        denoise_h=12.0,
        adaptive_block_size=35,
        adaptive_c=12.0,
        despeckle_size=5,
        contrast_stretch=True,
        deskew=True,
        color_mode="binary",
        filter_speckle=4,
        corner_threshold=60,
        path_precision=3,
    ),
    "clean-line": PresetConfig(
        name="clean-line",
        description=(
            "Optimized for modern scans or clean high-contrast line drawings. "
            "Applies minimal filtering to keep sharp, razor-thin lines and fine cross-hatching."
        ),
        denoise_h=5.0,
        adaptive_block_size=21,
        adaptive_c=8.0,
        despeckle_size=2,
        contrast_stretch=False,
        deskew=False,
        color_mode="binary",
        filter_speckle=2,
        corner_threshold=50,
        path_precision=4,
    ),
    "woodblock": PresetConfig(
        name="woodblock",
        description=(
            "Optimized for heavy contrast prints, woodcut illustrations, and bold calligraphy. "
            "Emphasizes solid black fills and clean silhouette boundaries."
        ),
        denoise_h=14.0,
        adaptive_block_size=45,
        adaptive_c=15.0,
        despeckle_size=6,
        contrast_stretch=True,
        deskew=False,
        color_mode="binary",
        filter_speckle=6,
        corner_threshold=70,
        path_precision=3,
    ),
    "color-flat": PresetConfig(
        name="color-flat",
        description=(
            "For color comic pages with flat cell shading. "
            "Preserves primary ink lines while quantizing and vectorizing distinct color regions."
        ),
        denoise_h=6.0,
        adaptive_block_size=25,
        adaptive_c=10.0,
        despeckle_size=3,
        contrast_stretch=False,
        deskew=False,
        color_mode="color",
        filter_speckle=4,
        corner_threshold=60,
        path_precision=3,
    ),
}


def get_preset(name: str) -> PresetConfig:
    """Retrieve a preset by name. Falls back to 'vintage-comic' if not found."""
    normalized = name.lower().strip()
    if normalized in PRESETS:
        return PRESETS[normalized]
    raise ValueError(
        f"Unknown preset '{name}'. Available presets: {', '.join(PRESETS.keys())}"
    )


def list_presets() -> List[PresetConfig]:
    """List all registered presets."""
    return list(PRESETS.values())
