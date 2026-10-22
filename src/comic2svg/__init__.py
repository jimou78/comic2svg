"""comic2svg: High-fidelity vectorizer (SVG) and preprocessing pipeline for vintage comics, picture books, and scanned line art.
"""

from .presets import PresetConfig, get_preset, list_presets
from .preprocess import (
    clean_image,
    split_double_pages,
    crop_scanner_borders,
    descreen_halftone,
    filter_speckles,
)
from .enhance import enhance_to_hd, upscale_image, unsharp_mask, flat_field_correction
from .vectorize import vectorize_image
from .optimizer import optimize_svg, optimize_svg_content
from .flipbook import generate_flipbook
from .core import convert_file, convert_batch, convert_to_hd
from .webui import run_webui

__version__ = "0.1.3"

__all__ = [
    "PresetConfig",
    "get_preset",
    "list_presets",
    "clean_image",
    "split_double_pages",
    "crop_scanner_borders",
    "descreen_halftone",
    "filter_speckles",
    "enhance_to_hd",
    "upscale_image",
    "unsharp_mask",
    "flat_field_correction",
    "vectorize_image",
    "optimize_svg",
    "optimize_svg_content",
    "generate_flipbook",
    "convert_file",
    "convert_batch",
    "convert_to_hd",
    "run_webui",
    "__version__",
]
