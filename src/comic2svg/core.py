"""Core orchestration pipeline for comic2svg.

Combines PDF rendering, HD enhancement, image preprocessing, and vectorization
into a seamless batch processing engine with multi-core parallelism.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from .pdf import render_pdf_pages
from .presets import PresetConfig, get_preset
from .preprocess import clean_image
from .enhance import enhance_to_hd
from .vectorize import vectorize_image
from .optimizer import optimize_svg

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def _process_single_page(
    image_path_str: str,
    output_svg_str: str,
    preset_name: str,
    keep_intermediate: bool,
    use_hd: bool = False,
    hd_scale: float = 2.0,
    optimize: bool = True,
    precision: int = 2,
) -> Tuple[str, bool, str]:
    """Worker function for parallel page processing."""
    try:
        preset = get_preset(preset_name)
        img_p = Path(image_path_str)
        svg_p = Path(output_svg_str)

        # 1. HD Enhancement if requested
        if use_hd:
            hd_p = img_p.with_suffix(f".hd_{int(hd_scale)}x.png")
            enhance_to_hd(
                img_p,
                hd_p,
                scale=hd_scale,
                sharpen=True,
                flat_field=True,
                reconnect=True,
                denoise_strength=preset.denoise_h,
            )
            working_img = hd_p
        else:
            working_img = img_p

        # 2. Clean and binarize
        clean_p = working_img.with_suffix(".clean.png")
        clean_image(working_img, clean_p, preset=preset)

        # 3. Vectorize
        vectorize_image(clean_p, svg_p, preset=preset)

        # 4. SVG Optimization / Minification
        if optimize and svg_p.exists():
            optimize_svg(svg_p, svg_p, precision=precision)

        # 4. Clean up intermediate if not needed
        if not keep_intermediate:
            for intermediate in [clean_p]:
                if intermediate.exists() and intermediate != img_p:
                    try:
                        intermediate.unlink()
                    except OSError:
                        pass
            if use_hd and working_img.exists() and working_img != img_p:
                try:
                    working_img.unlink()
                except OSError:
                    pass

        return (str(svg_p), True, "")
    except Exception as exc:
        return (str(image_path_str), False, str(exc))


def _process_hd_only_page(
    image_path_str: str,
    output_png_str: str,
    scale: float,
    sharpen: bool,
    flat_field: bool,
    reconnect: bool,
    binarize: bool,
) -> Tuple[str, bool, str]:
    """Worker function for PDF -> PNG -> HD PNG enhancement without SVG conversion."""
    try:
        img_p = Path(image_path_str)
        out_p = Path(output_png_str)

        enhance_to_hd(
            input_path=img_p,
            output_path=out_p,
            scale=scale,
            sharpen=sharpen,
            flat_field=flat_field,
            reconnect=reconnect,
            binarize=binarize,
        )
        return (str(out_p), True, "")
    except Exception as exc:
        return (str(image_path_str), False, str(exc))


def convert_to_hd(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    scale: float = 2.0,
    dpi: int = 300,
    page_range: Optional[str] = None,
    sharpen: bool = True,
    flat_field: bool = True,
    reconnect: bool = True,
    binarize: bool = False,
    workers: Optional[int] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[Path]:
    """Two-step pipeline:

    1. Extract PDF pages to PNG (or take existing images).
    2. Enhance each page to high-definition (HD) with super-resolution,
       background flattening, and line sharpening.

    Returns list of HD PNG paths.
    """
    in_file = Path(input_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not in_file.exists():
        raise FileNotFoundError(f"Input file not found: {in_file}")

    # Step 1: PDF to PNG
    if in_file.suffix.lower() == ".pdf":
        raw_pages_dir = out_dir / f"_{in_file.stem}_raw_pages"
        raw_pages_dir.mkdir(parents=True, exist_ok=True)

        pages = list(
            render_pdf_pages(in_file, raw_pages_dir, dpi=dpi, page_range=page_range)
        )
        task_list = [
            (str(p), str(out_dir / f"{p.stem}_hd_{int(scale)}x.png"))
            for p in pages
        ]
    elif in_file.suffix.lower() in IMAGE_EXTENSIONS:
        task_list = [(str(in_file), str(out_dir / f"{in_file.stem}_hd_{int(scale)}x.png"))]
    elif in_file.is_dir():
        sub_files = [
            f for f in sorted(in_file.iterdir())
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        task_list = [
            (str(sf), str(out_dir / f"{sf.stem}_hd_{int(scale)}x.png"))
            for sf in sub_files
        ]
    else:
        raise ValueError(f"Unsupported file format: {in_file.suffix}")

    # Step 2: PNG to HD
    total = len(task_list)
    if total == 0:
        return []

    num_workers = workers or min(os.cpu_count() or 4, total)
    successful_paths: List[Path] = []
    completed = 0

    if num_workers <= 1 or total == 1:
        for in_str, out_str in task_list:
            res_path, ok, err = _process_hd_only_page(
                in_str, out_str, scale, sharpen, flat_field, reconnect, binarize
            )
            completed += 1
            if ok:
                successful_paths.append(Path(res_path))
            if progress_callback:
                progress_callback(completed, total, Path(in_str).name)
            if not ok:
                print(f"[Warning] Failed to enhance {in_str}: {err}")
        return successful_paths

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {
            executor.submit(
                _process_hd_only_page,
                in_str,
                out_str,
                scale,
                sharpen,
                flat_field,
                reconnect,
                binarize,
            ): in_str
            for in_str, out_str in task_list
        }

        for future in as_completed(futures):
            in_file_str = futures[future]
            completed += 1
            try:
                res_path, ok, err = future.result()
                if ok:
                    successful_paths.append(Path(res_path))
                else:
                    print(f"[Warning] Error enhancing {in_file_str}: {err}")
            except Exception as e:
                print(f"[Error] Task failed on {in_file_str}: {e}")

            if progress_callback:
                progress_callback(completed, total, Path(in_file_str).name)

    return sorted(successful_paths)


def convert_file(
    input_path: Union[str, Path],
    output_dir: Union[str, Path],
    preset: Optional[Union[str, PresetConfig]] = None,
    dpi: int = 300,
    page_range: Optional[str] = None,
    workers: Optional[int] = None,
    keep_intermediate: bool = False,
    use_hd: bool = False,
    hd_scale: float = 2.0,
    optimize: bool = True,
    precision: int = 2,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[Path]:
    """Convert a single PDF file or single image to SVG(s)."""
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
        use_hd=use_hd,
        hd_scale=hd_scale,
        optimize=optimize,
        precision=precision,
        progress_callback=progress_callback,
    )


def convert_batch(
    input_paths: List[Union[str, Path]],
    output_dir: Union[str, Path],
    preset: Optional[Union[str, PresetConfig]] = None,
    dpi: int = 300,
    workers: Optional[int] = None,
    keep_intermediate: bool = False,
    use_hd: bool = False,
    hd_scale: float = 2.0,
    optimize: bool = True,
    precision: int = 2,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[Path]:
    """Convert multiple files or directories of images/PDFs."""
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    all_generated: List[Path] = []
    for item in input_paths:
        p = Path(item).resolve()
        if p.is_dir():
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
                    use_hd=use_hd,
                    hd_scale=hd_scale,
                    optimize=optimize,
                    precision=precision,
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
                use_hd=use_hd,
                hd_scale=hd_scale,
                progress_callback=progress_callback,
            )
            all_generated.extend(results)

    return all_generated


def _run_parallel_tasks(
    tasks: List[Tuple[str, str]],
    preset_name: str,
    workers: Optional[int] = None,
    keep_intermediate: bool = False,
    use_hd: bool = False,
    hd_scale: float = 2.0,
    optimize: bool = True,
    precision: int = 2,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> List[Path]:
    total = len(tasks)
    if total == 0:
        return []

    num_workers = workers or min(os.cpu_count() or 4, total)
    successful_paths: List[Path] = []
    completed = 0

    if num_workers <= 1 or total == 1:
        for in_str, out_str in tasks:
            res_path, ok, err = _process_single_page(
                in_str, out_str, preset_name, keep_intermediate, use_hd, hd_scale, optimize, precision
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
                _process_single_page,
                in_str,
                out_str,
                preset_name,
                keep_intermediate,
                use_hd,
                hd_scale,
                optimize,
                precision,
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
