"""Command-line interface for comic2svg powered by Typer and Rich.
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
import typer

from . import __version__
from .core import convert_batch, convert_file, convert_to_hd
from .flipbook import generate_flipbook
from .optimizer import optimize_svg
from .presets import list_presets
from .webui import run_webui

app = typer.Typer(
    name="comic2svg",
    help="High-fidelity vectorizer (SVG) and smart preprocessing pipeline for vintage comics and picture books.",
    add_completion=False,
)
console = Console()


@app.command(name="webui")
def webui_cmd(
    host: str = typer.Option(
        "127.0.0.1",
        "--host",
        "-h",
        help="Host address to bind the studio web server.",
    ),
    port: int = typer.Option(
        8080,
        "--port",
        "-p",
        help="Port number for the studio web server.",
    ),
    no_browser: bool = typer.Option(
        False,
        "--no-browser",
        help="Do not automatically launch the browser.",
    ),
):
    """Launch the interactive comic2svg Studio in your browser."""
    console.print(f"[bold cyan]Launching comic2svg Studio v{__version__}...[/bold cyan]")
    run_webui(host=host, port=port, open_browser=not no_browser)


@app.command(name="flipbook")
def flipbook_cmd(
    svg_dir: Path = typer.Argument(
        ...,
        help="Directory containing generated SVG pages.",
        exists=True,
    ),
    out: Path = typer.Option(
        Path("flipbook.html"),
        "--out",
        "-o",
        help="Output HTML flipbook path.",
    ),
    title: str = typer.Option(
        "Comic Book",
        "--title",
        "-t",
        help="Title of the comic book reader.",
    ),
):
    """Generate a standalone offline HTML5 reader embedding all comic SVGs."""
    svgs = sorted(list(svg_dir.glob("*.svg")))
    if not svgs:
        console.print("[red]No SVG files found in directory.[/red]")
        return
    res = generate_flipbook(svgs, out, title=title)
    console.print(
        f"[bold green]✓ Flipbook generated successfully![/bold green] Open in any browser: [underline]{res}[/underline]"
    )


@app.command(name="optimize")
def optimize_cmd(
    input_path: Path = typer.Argument(
        ...,
        help="Path to an SVG file or a directory containing SVG files to minify.",
        exists=True,
    ),
    out: Optional[Path] = typer.Option(
        None,
        "--out",
        "-o",
        help="Destination path or directory. If omitted, optimizes in-place.",
    ),
    precision: int = typer.Option(
        2,
        "--precision",
        help="Decimal precision for bezier coordinates (1 to 4).",
    ),
):
    """Minify and compress SVG files (reduce size by 40%~60% without quality loss)."""
    console.print(f"[bold cyan]comic2svg SVG Optimizer v{__version__}[/bold cyan]")

    svg_files = []
    if input_path.is_file():
        svg_files = [input_path]
    elif input_path.is_dir():
        svg_files = sorted(list(input_path.glob("*.svg")))

    if not svg_files:
        console.print("[yellow]No SVG files found to optimize.[/yellow]")
        return

    table = Table(title="Optimization Results", header_style="bold magenta")
    table.add_column("File", style="cyan")
    table.add_column("Original", style="dim")
    table.add_column("Optimized", style="green")
    table.add_column("Saved", style="bold yellow")

    total_orig = 0
    total_opt = 0

    for f in svg_files:
        out_f = out / f.name if (out and out.is_dir()) else (out if (out and len(svg_files) == 1) else f)
        _, stats = optimize_svg(f, out_f, precision=precision)
        total_orig += stats.original_bytes
        total_opt += stats.optimized_bytes

        table.add_row(
            f.name,
            f"{stats.original_bytes / 1024:.1f} KB",
            f"{stats.optimized_bytes / 1024:.1f} KB",
            f"-{stats.savings_percent:.1f}%",
        )

    console.print(table)
    overall_saved = ((total_orig - total_opt) / total_orig * 100) if total_orig > 0 else 0
    console.print(
        f"[bold green]✓ Done![/bold green] Total saved: [bold]{(total_orig - total_opt)/1024:.1f} KB[/bold] ({overall_saved:.1f}% reduction)"
    )


@app.command(name="hd")
def hd_cmd(
    input_path: Path = typer.Argument(
        ...,
        help="Path to an input PDF, image file (.png, .jpg, .webp), or folder of images.",
        exists=True,
    ),
    out: Path = typer.Option(
        Path("out_hd"),
        "--out",
        "-o",
        help="Output directory for generated HD PNG files.",
    ),
    scale: float = typer.Option(
        2.0,
        "--scale",
        "-s",
        help="Super-resolution scaling factor (e.g. 2.0 for 2x, 4.0 for 4x).",
    ),
    dpi: int = typer.Option(
        300,
        "--dpi",
        help="Rendering resolution (DPI) for PDF extraction.",
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        help="Page range to convert for PDF files (e.g. '1-10', '1,3,5').",
    ),
    sharpen: bool = typer.Option(
        True,
        "--sharpen/--no-sharpen",
        help="Apply line-edge unsharp masking to sharpen ink strokes.",
    ),
    flat_field: bool = typer.Option(
        True,
        "--flat-field/--no-flat-field",
        help="Normalize background lighting to remove yellowing and shadows.",
    ),
    reconnect: bool = typer.Option(
        True,
        "--reconnect/--no-reconnect",
        help="Reconnect micro-breaks in lines caused by age or degradation.",
    ),
    fast: bool = typer.Option(
        False,
        "--fast/--no-fast",
        help="Use fast bilateral filter instead of heavy NLMeans denoising (50x faster).",
    ),
    binarize: bool = typer.Option(
        False,
        "--binarize/--no-binarize",
        help="Binarize output to pure black & white instead of enhanced grayscale.",
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers",
        "-w",
        help="Number of parallel worker processes (default: CPU cores).",
    ),
):
    """Step 1 & 2: Extract PDF to PNG and enhance to super-resolution HD line art."""
    console.print(
        f"[bold cyan]comic2svg HD Enhancer v{__version__}[/bold cyan] - Starting HD restoration"
    )
    console.print(f"[dim]Input:[/dim] {input_path}")
    console.print(f"[dim]Output directory:[/dim] {out}")
    console.print(f"[dim]Upscale:[/dim] [green]{scale}x (Lanczos-4)[/green]")
    console.print(f"[dim]Sharpening:[/dim] {'Enabled' if sharpen else 'Disabled'}")
    console.print(f"[dim]Flat-field normalization:[/dim] {'Enabled' if flat_field else 'Disabled'}")
    if fast:
        console.print("[dim]Denoise Mode:[/dim] [yellow]High-Speed Bilateral (<30ms)[/yellow]")

    out.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Enhancing pages to HD...", total=1)

        def on_progress(completed: int, total: int, current_name: str):
            progress.update(
                task_id,
                total=total,
                completed=completed,
                description=f"[cyan]{current_name}[/cyan]",
            )

        results = convert_to_hd(
            input_path=input_path,
            output_dir=out,
            scale=scale,
            dpi=dpi,
            page_range=pages,
            sharpen=sharpen,
            flat_field=flat_field,
            reconnect=reconnect,
            binarize=binarize,
            fast=fast,
            workers=workers,
            progress_callback=on_progress,
        )

    console.print(
        f"\n[bold green]✓ HD Enhancement complete![/bold green] Generated [bold]{len(results)}[/bold] HD images in [underline]{out}[/underline]"
    )


@app.command(name="convert")
def convert_cmd(
    input_path: Path = typer.Argument(
        ...,
        help="Path to an input PDF, image file (.png, .jpg, .webp), or folder of images.",
        exists=True,
    ),
    out: Path = typer.Option(
        Path("out"),
        "--out",
        "-o",
        help="Output directory for generated SVG files.",
    ),
    preset: str = typer.Option(
        "vintage-comic",
        "--preset",
        "-p",
        help="Parameter preset ('vintage-comic', 'clean-line', 'woodblock', 'color-flat').",
    ),
    dpi: int = typer.Option(
        300,
        "--dpi",
        help="Base rendering resolution (DPI) for PDF extraction.",
    ),
    adaptive_dpi: bool = typer.Option(
        True,
        "--adaptive-dpi/--no-adaptive-dpi",
        help="Dynamically scale DPI for small pocket books (小人书).",
    ),
    pages: Optional[str] = typer.Option(
        None,
        "--pages",
        help="Page range to convert for PDF files (e.g. '1-10', '1,3,5').",
    ),
    split_pages: bool = typer.Option(
        False,
        "--split-pages/--no-split-pages",
        help="Auto-detect wide double-page scans and split them at the gutter.",
    ),
    split_direction: str = typer.Option(
        "ltr",
        "--split-direction",
        help="Double-page order: 'ltr' (Left-to-Right, standard) or 'rtl' (Right-to-Left, manga).",
    ),
    crop_borders: bool = typer.Option(
        False,
        "--crop-borders/--no-crop-borders",
        help="Automatically crop away black scanner cover margins and shadows.",
    ),
    descreen: bool = typer.Option(
        False,
        "--descreen/--no-descreen",
        help="Remove printing halftone dot screens (半色调网点).",
    ),
    flipbook: bool = typer.Option(
        False,
        "--flipbook/--no-flipbook",
        help="Automatically generate a standalone offline HTML5 flipbook reader.",
    ),
    fast: bool = typer.Option(
        False,
        "--fast/--no-fast",
        help="Use high-speed bilateral filtering for denoise to maximize throughput.",
    ),
    hd: bool = typer.Option(
        False,
        "--hd",
        help="Enable HD super-resolution and line enhancement before vectorizing.",
    ),
    scale: float = typer.Option(
        2.0,
        "--scale",
        "-s",
        help="HD scaling factor if --hd is enabled (e.g. 2.0).",
    ),
    optimize: bool = typer.Option(
        True,
        "--optimize/--no-optimize",
        "-O",
        help="Automatically minify and compress the resulting SVG files (reduces size by 40-60%).",
    ),
    precision: int = typer.Option(
        2,
        "--precision",
        help="Bezier coordinate decimal precision for optimization (default 2).",
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers",
        "-w",
        help="Number of parallel worker processes (default: all CPU cores).",
    ),
    keep_intermediate: bool = typer.Option(
        False,
        "--keep-intermediate",
        help="Keep preprocessed cleaned images (.clean.png) alongside SVGs.",
    ),
):
    """Convert scanned comics, picture books, or line art to clean vector SVG files."""
    console.print(
        f"[bold cyan]comic2svg v{__version__}[/bold cyan] - Starting conversion pipeline"
    )
    console.print(f"[dim]Input:[/dim] {input_path}")
    console.print(f"[dim]Output directory:[/dim] {out}")
    console.print(f"[dim]Preset:[/dim] [green]{preset}[/green]")
    if hd:
        console.print(f"[dim]HD Pre-enhancement:[/dim] [green]Enabled ({scale}x)[/green]")
    if fast:
        console.print("[dim]Denoise Mode:[/dim] [yellow]High-Speed Bilateral[/yellow]")
    if split_pages:
        console.print(f"[dim]Double-page split:[/dim] [green]Enabled ({split_direction.upper()})[/green]")
    if crop_borders:
        console.print("[dim]Scanner margin cropping:[/dim] [green]Enabled[/green]")
    if descreen:
        console.print("[dim]Halftone descreening:[/dim] [green]Enabled[/green]")
    if flipbook:
        console.print("[dim]HTML5 Flipbook Reader:[/dim] [green]Enabled[/green]")

    out.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Processing pages...", total=1)

        def on_progress(completed: int, total: int, current_name: str):
            progress.update(
                task_id,
                total=total,
                completed=completed,
                description=f"[cyan]{current_name}[/cyan]",
            )

        if input_path.is_dir():
            results = convert_batch(
                [input_path],
                out,
                preset=preset,
                dpi=dpi,
                adaptive_dpi=adaptive_dpi,
                page_range=pages,
                split_pages=split_pages,
                split_direction=split_direction,
                crop_borders=crop_borders,
                descreen=descreen,
                flipbook=flipbook,
                fast=fast,
                workers=workers,
                keep_intermediate=keep_intermediate,
                use_hd=hd,
                hd_scale=scale,
                optimize=optimize,
                precision=precision,
                progress_callback=on_progress,
            )
        else:
            results = convert_file(
                input_path,
                out,
                preset=preset,
                dpi=dpi,
                adaptive_dpi=adaptive_dpi,
                page_range=pages,
                split_pages=split_pages,
                split_direction=split_direction,
                crop_borders=crop_borders,
                descreen=descreen,
                flipbook=flipbook,
                fast=fast,
                workers=workers,
                keep_intermediate=keep_intermediate,
                use_hd=hd,
                hd_scale=scale,
                optimize=optimize,
                precision=precision,
                progress_callback=on_progress,
            )

    console.print(
        f"\n[bold green]✓ Conversion completed![/bold green] Generated [bold]{len(results)}[/bold] SVG files in [underline]{out}[/underline]"
    )


@app.command(name="presets")
def presets_cmd():
    """List all available preprocessing and vectorization presets."""
    presets = list_presets()

    table = Table(title="comic2svg Presets", show_header=True, header_style="bold magenta")
    table.add_column("Preset Name", style="cyan", width=16)
    table.add_column("Color Mode", style="yellow", width=12)
    table.add_column("Denoise / Speckle", style="dim", width=18)
    table.add_column("Description", style="white")

    for p in presets:
        table.add_row(
            p.name,
            p.color_mode,
            f"h={p.denoise_h} / spk={p.filter_speckle}",
            p.description,
        )

    console.print(table)


@app.command(name="version")
def version_cmd():
    """Show the comic2svg version."""
    console.print(f"comic2svg version [bold green]{__version__}[/bold green]")


if __name__ == "__main__":
    app()
