"""Core orchestration pipeline for comic2svg.

Combines PDF rendering, image preprocessing, and vectorization into a seamless
batch processing engine with multi-core parallelism.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from .pdf import render_pdf_pages
from .presets import PresetConfig, get_preset
from .preprocess import clean_image
from .vectorize import vectorize_image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _process_single_page(
    image_path_str: str,
    output_svg_str: str,
    preset_name: str,
    keep_intermediate: bool,
) -> Tuple[str, bool, str]:
    """Worker function for parallel page processing."""
    try:
        preset = get_preset(preset_name)
        img_p = Path(image_path_str)
        svg_p = Path(output_svg_str)

        # 1. Clean image
        clean_p = img_p.with_suffix(".clean.png")
        clean_image(img_p, clean_p, preset=preset)

        # 2. Vectorize
        vectorize_image(clean_p, svg_p, preset=preset)

        # 3. Clean up intermediate if not needed
        if not keep_intermediate and clean_p.exists() and clean_p != img_p:
            try:
                clean_p.unlink()
            except OSError:
                pass

        return (str(svg_p), True, "")
    except Exception as exc:
        return (str(image_path_str), False, str(exc))


def convert_file(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    preset: Optional[Union[str, PresetConfig]] = None,
    dpi: int = 300,
    page_range: Optional[str] = None,
    workers: Optional[int] = None,
    keep_intermediate: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[Path]:
    """Convert a single PDF file or single image to SVG(s).

    Parameters
    ----------
    input_path : Union[str, Path]
        Path to a PDF or an image file.
    output_dir : Union[str, Path]
        Directory where output SVGs will be stored.
    preset : Optional[Union[str, PresetConfig]]
        Preset name or PresetConfig object. Defaults to 'vintage-comic'.
    dpi : int
        DPI for PDF rendering (default 300).
    page_range : Optional[str]
        Page selection for PDFs (e.g. '1-10', '1,3,5').
    workers : Optional[int]
        Number of parallel worker processes. Defaults to CPU count.
    keep_intermediate : bool
        Whether to keep preprocessed intermediate images.
    progress_callback : Optional[Callable[[int, int, str], None]]
        Callback func(completed_count, total_count, current_filename).

    Returns
    -------
    List[Path]
        List of generated SVG paths.
    """
    in_file = Path(input_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if isinstance(preset, PresetConfig):
        preset_cfg = preset
    elif isinstance(preset, str):
        preset_cfg = get_preset(preset)
    else:
        preset_cfg = get_preset("vintage-comic")

    if not in_file.exists():
        raise FileNotFoundError(f"Input file not found: {in_file}")

    # Determine input type
    if in_file.suffix.lower() == ".pdf":
        temp_pages_dir = out_dir / f"_{in_file.stem}_pages"
        temp_pages_dir.mkdir(parents=True, exist_ok=True)

        pages = list(
            render_pdf_pages(in_file, temp_pages_dir, dpi=dpi, page_range=page_range)
        )
        task_list = [
            (str(p), str(out_dir / f"{in_file.stem}_{p.stem}.svg"))
            for p in pages
        ]
    elif in_file.suffix.lower() in IMAGE_EXTENSIONS:
        target_svg = out_dir / f"{in_file.stem}.svg"
        task_list = [(str(in_file), str(target_svg))]
    else:
        raise ValueError(
            f"Unsupported file format '{in_file.suffix}'. Supported: PDF, {', '.join(sorted(IMAGE_EXTENSIONS))}"
        )

    return _run_parallel_tasks(
        task_list,
        preset_cfg.name,
        workers=workers,
        keep_intermediate=keep_intermediate,
        progress_callback=progress_callback,
    )


def convert_batch(
    input_paths: List[Union[str, Path]],
    output_dir: Union[str, Path],
    preset: Optional[Union[str, PresetConfig]] = None,
    dpi: int = 300,
    workers: Optional[int] = None,
    keep_intermediate: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[Path]:
    """Convert multiple files or directories of images/PDFs."""
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    all_generated: List[Path] = []
    for item in input_paths:
        p = Path(item).resolve()
        if p.is_dir():
            # Gather all images in folder
            sub_files = [
                f for f in sorted(p.iterdir())
                if f.is_file() and (f.suffix.lower() in IMAGE_EXTENSIONS or f.suffix.lower() == ".pdf")
            ]
            for sf in sub_files:
                sub_out = convert_file(
                    sf,
                    out_dir,
                    preset=preset,
                    dpi=dpi,
                    workers=workers,
                    keep_intermediate=keep_intermediate,
                    progress_callback=progress_callback,
                )
                all_generated.extend(sub_out)
        elif p.is_file():
            results = convert_file(
                p,
                out_dir,
                preset=preset,
                dpi=dpi,
                workers=workers,
                keep_intermediate=keep_intermediate,
                progress_callback=progress_callback,
            )
            all_generated.extend(results)

    return all_generated


def _run_parallel_tasks(
    tasks: List[Tuple[str, str]],
    preset_name: str,
    workers: Optional[int] = None,
    keep_intermediate: bool = False,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[Path]:
    """Execute page conversion tasks using a ProcessPoolExecutor."""
    total = len(tasks)
    if total == 0:
        return []

    num_workers = workers or min(os.cpu_count() or 4, total)
    successful_paths: List[Path] = []
    completed = 0

    if num_workers <= 1 or total == 1:
        # Run sequentially for single items to save spawn overhead
        for in_str, out_str in tasks:
            res_path, ok, err = _process_single_page(
                in_str, out_str, preset_name, keep_intermediate
            )
            completed += 1
            if ok:
                successful_paths.append(Path(res_path))
            if progress_callback:
                progress_callback(completed, total, Path(in_str).name)
            if not ok:
                print(f"[Warning] Failed to process {in_str}: {err}")
        return successful_paths

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(
                _process_single_page, in_str, out_str, preset_name, keep_intermediate
            ): in_str
            for in_str, out_str in tasks
        }

        for future in as_completed(futures):
            in_file_str = futures[future]
            completed += 1
            try:
                res_path, ok, err = future.result()
                if ok:
                    successful_paths.append(Path(res_path))
                else:
                    print(f"[Warning] Error converting {in_file_str}: {err}")
            except Exception as e:
                print(f"[Error] Task failed unexpectedly on {in_file_str}: {e}")

            if progress_callback:
                progress_callback(completed, total, Path(in_file_str).name)

    return sorted(successful_paths)
