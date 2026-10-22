"""comic2svg: High-fidelity vectorizer (SVG) and preprocessing pipeline for vintage comics, picture books, and scanned line art.
"""

from .presets import PresetConfig, get_preset, list_presets
from .preprocess import clean_image
from .vectorize import vectorize_image
from .core import convert_file, convert_batch

__version__ = "0.1.0"

__all__ = [
    "PresetConfig",
    "get_preset",
    "list_presets",
    "clean_image",
    "vectorize_image",
    "convert_file",
    "convert_batch",
    "__version__",
]
