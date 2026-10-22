"""comic2svg: High-fidelity vectorizer (SVG) and preprocessing pipeline for vintage comics, picture books, and scanned line art.
"""

from .presets import PresetConfig, get_preset, list_presets
from .preprocess import clean_image
from .enhance import enhance_to_hd, upscale_image, unsharp_mask, flat_field_correction
from .vectorize import vectorize_image
from .optimizer import optimize_svg, optimize_svg_content
from .core import convert_file, convert_batch, convert_to_hd
from .webui import run_webui

__version__ = "0.1.2"

__all__ = [
    "PresetConfig",
    "get_preset",
    "list_presets",
    "clean_image",
    "enhance_to_hd",
    "upscale_image",
    "unsharp_mask",
    "flat_field_correction",
    "vectorize_image",
    "optimize_svg",
    "optimize_svg_content",
    "convert_file",
    "convert_batch",
    "convert_to_hd",
    "run_webui",
    "__version__",
]
