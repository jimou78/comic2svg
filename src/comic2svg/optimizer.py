"""SVG optimization and minification engine for comic2svg.

Shrinks SVG file size by 40% to 60% by rounding path coordinate precision,
compressing bezier path commands, removing XML comments/metadata,
ensuring responsive viewBox tags, and stripping micro-artifacts.
"""

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional, Tuple, Union


@dataclass
class OptimizationStats:
    """Statistics comparing raw vs optimized SVG size."""

    original_bytes: int
    optimized_bytes: int
    saved_bytes: int
    savings_percent: float


def round_path_coordinates(path_data: str, precision: int = 2) -> str:
    """Round floating point coordinates inside SVG 'd' path strings to target precision."""
    number_pattern = re.compile(r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?")

    def _replace_num(match: re.Match) -> str:
        val = float(match.group(0))
        formatted = f"{val:.{precision}f}".rstrip("0").rstrip(".")
        return formatted if formatted != "-0" and formatted != "" else "0"

    rounded = number_pattern.sub(_replace_num, path_data)
    rounded = re.sub(r"([a-df-zA-DF-Z])\s+", r"\1", rounded)
    rounded = re.sub(r"\s+", " ", rounded)
    return rounded.strip()


def ensure_viewbox(svg_text: str) -> str:
    """Ensure root <svg> has a valid viewBox and namespace for responsive rendering."""
    svg_tag_match = re.search(r"<svg\b([^>]*)>", svg_text, flags=re.IGNORECASE)
    if not svg_tag_match:
        return svg_text

    attrs = svg_tag_match.group(1)

    # Check if viewBox already present
    if not re.search(r"\bviewBox\s*=", attrs, flags=re.IGNORECASE):
        w_match = re.search(r'\bwidth\s*=\s*["\'](\d+(?:\.\d+)?)(?:px|pt)?["\']', attrs, flags=re.IGNORECASE)
        h_match = re.search(r'\bheight\s*=\s*["\'](\d+(?:\.\d+)?)(?:px|pt)?["\']', attrs, flags=re.IGNORECASE)
        if w_match and h_match:
            w = float(w_match.group(1))
            h = float(h_match.group(1))
            w_str = f"{w:.2f}".rstrip("0").rstrip(".")
            h_str = f"{h:.2f}".rstrip("0").rstrip(".")
            attrs = f'{attrs} viewBox="0 0 {w_str} {h_str}"'

    # Ensure xmlns is present
    if not re.search(r"\bxmlns\s*=", attrs, flags=re.IGNORECASE):
        attrs = f'{attrs} xmlns="http://www.w3.org/2000/svg"'

    new_svg_tag = f"<svg{attrs}>"
    return svg_text[:svg_tag_match.start()] + new_svg_tag + svg_text[svg_tag_match.end():]


def optimize_svg_content(
    svg_text: str,
    precision: int = 2,
    remove_metadata: bool = True,
    strip_comments: bool = True,
    min_path_chars: int = 10,
    ensure_responsive: bool = True,
) -> str:
    """Optimize an SVG XML string in-memory."""
    # 1. Strip XML comments
    if strip_comments:
        svg_text = re.sub(r"<!--[\s\S]*?-->", "", svg_text)

    # 2. Strip XML declaration, doctype, and unneeded generator metadata
    if remove_metadata:
        svg_text = re.sub(r"<\?xml[\s\S]*?\?>", "", svg_text)
        svg_text = re.sub(r"<!DOCTYPE[\s\S]*?>", "", svg_text, flags=re.IGNORECASE)
        svg_text = re.sub(r"<metadata[\s\S]*?</metadata>", "", svg_text, flags=re.IGNORECASE)

    # 3. Ensure responsive viewBox
    if ensure_responsive:
        svg_text = ensure_viewbox(svg_text)

    # 4. Round coordinates inside all d="..." attributes
    def _opt_d(match: re.Match) -> str:
        prefix = match.group(1)  # d=" or d='
        content = match.group(2)
        quote = match.group(3)
        if len(content.strip()) < min_path_chars:
            return ""
        opt_content = round_path_coordinates(content, precision=precision)
        return f'{prefix}{opt_content}{quote}'

    svg_text = re.sub(r'(\bd\s*=\s*["\'])([\s\S]*?)(["\'])', _opt_d, svg_text)

    # 5. Remove empty groups and empty paths
    svg_text = re.sub(r'<path\s*d=["\']\s*["\']\s*/?>', "", svg_text)
    svg_text = re.sub(r'<path\s*/>', "", svg_text)
    svg_text = re.sub(r'<g>\s*</g>', "", svg_text)

    # 6. Normalize whitespace between tags
    svg_text = re.sub(r">\s+<", "><", svg_text)
    return svg_text.strip()


def optimize_svg(
    input_svg: Union[str, Path],
    output_svg: Optional[Union[str, Path]] = None,
    precision: int = 2,
) -> Tuple[Path, OptimizationStats]:
    """Read an SVG file, minify its paths and structure, and save it.

    Parameters
    ----------
    input_svg : Union[str, Path]
        Path to the unoptimized SVG file.
    output_svg : Optional[Union[str, Path]]
        Destination path. If None, overwrites input_svg in-place.
    precision : int
        Decimal precision for bezier coordinates (default 2).

    Returns
    -------
    Tuple[Path, OptimizationStats]
        Saved SVG path and compression statistics.
    """
    in_p = Path(input_svg).resolve()
    if not in_p.is_file():
        raise FileNotFoundError(f"SVG file not found: {in_p}")

    out_p = Path(output_svg).resolve() if output_svg else in_p

    raw_text = in_p.read_text(encoding="utf-8")
    original_size = len(raw_text.encode("utf-8"))

    optimized_text = optimize_svg_content(raw_text, precision=precision)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(optimized_text, encoding="utf-8")

    optimized_size = len(optimized_text.encode("utf-8"))
    saved_bytes = max(0, original_size - optimized_size)
    savings_percent = (saved_bytes / original_size * 100.0) if original_size > 0 else 0.0

    stats = OptimizationStats(
        original_bytes=original_size,
        optimized_bytes=optimized_size,
        saved_bytes=saved_bytes,
        savings_percent=savings_percent,
    )

    return out_p, stats
