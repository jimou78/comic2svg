"""Command-line interface for comic2svg powered by Typer and Rich.
"""

from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.table import Table

from . import __version__
from .core import convert_batch, convert_file
from .presets import list_presets

app = typer.Typer(
    name="comic2svg",
    help="High-fidelity vectorizer (SVG) and preprocessing pipeline for vintage comics and picture books.",
    add_completion=False,
)
console = Console()


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
        help="Rendering resolution (DPI) for PDF extraction.",
    ),
    page_range: Optional[str] = typer.Option(
        None,
        "--pages",
        help="Page range to convert for PDF files (e.g. '1-10', '1,3,5').",
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
                workers=workers,
                keep_intermediate=keep_intermediate,
                progress_callback=on_progress,
            )
        else:
            results = convert_file(
                input_path,
                out,
                preset=preset,
                dpi=dpi,
                page_range=page_range,
                workers=workers,
                keep_intermediate=keep_intermediate,
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
