"""Vectorization engine wrapping vtracer to produce clean SVG vector files.

Transforms raster line art and colored comic pages into scale-invariant,
compact SVG bezier curves.
"""

from pathlib import Path
from typing import Optional, Union

try:
    import vtracer
except ImportError:
    vtracer = None

from .presets import PresetConfig


def vectorize_image(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    preset: Optional[PresetConfig] = None,
    color_mode: Optional[str] = None,
) -> Path:
    """Convert an image to an SVG vector file.

    Parameters
    ----------
    input_path : Union[str, Path]
        Path to the source raster image (preferably preprocessed).
    output_path : Optional[Union[str, Path]]
        Destination path for the output .svg file.
    preset : Optional[PresetConfig]
        Preset configuration containing default vectorizer parameters.
    color_mode : Optional[str]
        Override mode: "binary" for black & white line art, "color" for colored pages.

    Returns
    -------
    Path
        Path to the generated SVG file.
    """
    if vtracer is None:
        raise ImportError(
            "vtracer is required for vectorization: pip install vtracer"
        )

    in_p = Path(input_path).resolve()
    if not in_p.is_file():
        raise FileNotFoundError(f"Input file not found: {in_p}")

    if output_path is None:
        out_p = in_p.with_suffix(".svg")
    else:
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

    if preset is None:
        from .presets import get_preset
        preset = get_preset("vintage-comic")

    mode = color_mode or preset.color_mode

    # Invoke vtracer high-performance Rust engine
    vtracer.convert_image_to_svg_py(
        image_path=str(in_p),
        out_path=str(out_p),
        colormode=mode,
        hierarchical="stacked",
        mode="spline",
        filter_speckle=preset.filter_speckle,
        color_precision=6 if mode == "color" else 8,
        layer_difference=16,
        corner_threshold=preset.corner_threshold,
        length_threshold=preset.length_threshold,
        max_iterations=10,
        splice_threshold=preset.splice_threshold,
        path_precision=preset.path_precision,
    )

    if not out_p.is_file() or out_p.stat().st_size == 0:
        raise RuntimeError(f"Vectorization failed or generated an empty file: {out_p}")

    return out_p
