"""PDF page rendering and extraction using PyMuPDF.

Extracts each page from scanned comic/book PDFs into crisp, high-resolution
images ready for preprocessing and vectorization.
"""

from pathlib import Path
from typing import Generator, List, Optional, Union

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


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


def render_pdf_pages(
    pdf_path: Union[str, Path],
    output_dir: Union[str, Path],
    dpi: int = 300,
    page_range: Optional[str] = None,
) -> Generator[Path, None, None]:
    """Render pages of a PDF to PNG images at specified DPI.

    Yields the Path to each rendered PNG page.
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
            # Convert DPI to scale factor (72 standard points/inch)
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            page_name = f"page_{page_idx + 1:04d}.png"
            page_path = out_directory / page_name
            pix.save(str(page_path))

            yield page_path
    finally:
        doc.close()
