"""PDF page rendering and extraction using PyMuPDF.

Extracts each page from scanned comic/book PDFs into crisp, high-resolution
images ready for preprocessing, HD enhancement, and vectorization.
"""

from pathlib import Path
from typing import Generator, List, Optional, Union
import numpy as np

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import cv2
except ImportError:
    cv2 = None


def parse_page_range(page_spec: Optional[str], total_pages: int) -> List[int]:
    """Parse a page specification string (e.g. '1-5', '1,3,7', '2-') into 0-based page indices."""
    if not page_spec:
        return list(range(total_pages))

    pages = set()
    parts = [p.strip() for p in page_spec.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            sub = part.split("-", 1)
            start_str, end_str = sub[0].strip(), sub[1].strip()
            start = int(start_str) - 1 if start_str else 0
            end = int(end_str) if end_str else total_pages
            start = max(0, min(start, total_pages - 1))
            end = max(start + 1, min(end, total_pages))
            pages.update(range(start, end))
        else:
            val = int(part) - 1
            if 0 <= val < total_pages:
                pages.add(val)

    return sorted(list(pages))


def calculate_adaptive_dpi(page, target_min_dimension: int = 2400, default_dpi: int = 300) -> int:
    """Calculate adaptive DPI based on physical page dimensions.

    Vintage picture books (小人书 / 64开本) have small physical dimensions.
    Standard 300 DPI might result in sub-optimal raster pixel density.
    This dynamically calculates the ideal DPI (300 to 600) to guarantee
    at least `target_min_dimension` pixels along the primary axis.
    """
    rect = page.rect
    max_pts = max(rect.width, rect.height)
    if max_pts <= 0:
        return default_dpi

    # pts to inches (72 pts per inch)
    dimension_inches = max_pts / 72.0
    computed_dpi = int(target_min_dimension / dimension_inches)
    # Clamp between 300 and 600 DPI
    return max(default_dpi, min(600, computed_dpi))


def render_pdf_pages(
    pdf_path: Union[str, Path],
    output_dir: Union[str, Path],
    dpi: int = 300,
    adaptive_dpi: bool = True,
    page_range: Optional[str] = None,
    extract_raw_images: bool = False,
    split_double_pages: bool = False,
    split_direction: str = "ltr",
) -> Generator[Path, None, None]:
    """Render or extract pages of a PDF to PNG images at specified DPI.

    Parameters
    ----------
    pdf_path : Union[str, Path]
        Path to the PDF file.
    output_dir : Union[str, Path]
        Directory where page PNG files will be saved.
    dpi : int
        Base rendering DPI (default 300).
    adaptive_dpi : bool
        Whether to automatically scale up DPI for small pocket book formats.
    page_range : Optional[str]
        Optional page filter (e.g. '1-10', '1,3,5').
    extract_raw_images : bool
        Attempts to extract original raw scanned pixmaps directly.
    split_double_pages : bool
        Detects wide landscape 2-page scans and splits them at the binding gutter.
    split_direction : str
        'ltr' for left-to-right (comics), 'rtl' for right-to-left (manga).

    Yields
    ------
    Path
        Path to each extracted/rendered PNG page.
    """
    if fitz is None:
        raise ImportError(
            "PyMuPDF is required to process PDF files: pip install pymupdf"
        )

    pdf_file = Path(pdf_path).resolve()
    if not pdf_file.is_file():
        raise FileNotFoundError(f"PDF file not found: {pdf_file}")

    out_directory = Path(output_dir).resolve()
    out_directory.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_file))
    try:
        total_pages = len(doc)
        selected_pages = parse_page_range(page_range, total_pages)

        for page_idx in selected_pages:
            page = doc[page_idx]

            # Calculate adaptive DPI
            render_dpi = calculate_adaptive_dpi(page, default_dpi=dpi) if adaptive_dpi else dpi

            extracted = False
            page_name = f"page_{page_idx + 1:04d}.png"
            page_path = out_directory / page_name

            if extract_raw_images:
                image_list = page.get_images(full=True)
                if image_list:
                    xref = image_list[0][0]
                    base_img = doc.extract_image(xref)
                    if base_img and "image" in base_img:
                        with open(page_path, "wb") as f:
                            f.write(base_img["image"])
                        extracted = True

            if not extracted:
                zoom = max(1.0, render_dpi / 72.0)
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                pix.save(str(page_path))

            # Check if double page split is requested
            if split_double_pages and cv2 is not None:
                from .preprocess import split_double_pages as split_fn, read_image, write_image
                img = read_image(page_path, grayscale=False)
                pages = split_fn(img, direction=split_direction)
                if len(pages) > 1:
                    # Remove original wide image and save split sub-pages
                    page_path.unlink()
                    for sub_idx, sub_img in enumerate(pages, start=1):
                        sub_name = f"page_{page_idx + 1:04d}_{chr(96 + sub_idx)}.png"
                        sub_path = out_directory / sub_name
                        write_image(sub_path, sub_img)
                        yield sub_path
                    continue

            yield page_path
    finally:
        doc.close()
