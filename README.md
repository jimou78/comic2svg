# comic2svg 🎨⚡

<p align="center">
  <b>High-fidelity vectorizer (SVG) and smart preprocessing pipeline for vintage comics, picture books (小人书), and scanned line art.</b>
</p>

<p align="center">
  <a href="https://github.com/jimou78/comic2svg/actions/workflows/ci.yml"><img src="https://github.com/jimou78/comic2svg/actions/workflows/ci.yml/badge.svg" alt="CI Status"></a>
  <a href="https://pypi.org/project/comic2svg/"><img src="https://img.shields.io/pypi/v/comic2svg.svg?color=blue" alt="PyPI version"></a>
  <a href="https://pypi.org/project/comic2svg/"><img src="https://img.shields.io/pypi/pyversions/comic2svg.svg" alt="Python Versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT"></a>
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome"></a>
  <a href="README_CN.md"><img src="https://img.shields.io/badge/文档-简体中文-blue.svg" alt="Chinese Documentation"></a>
</p>

---

## 🌟 Why comic2svg?

Scanning and reading vintage comics, classic picture books (连环画 / 小人书), and historical line illustrations on modern 4K/Retina displays often suffers from:
- **Yellowed, uneven background paper** that distracts the reader.
- **Micro-speckles, scanner dust, and ink bleeds** that degrade visual appeal.
- **Pixelation and blur** when zooming in on desktop or mobile e-readers.

Standard bitmap-to-vector tools (like raw Potrace or Inkscape trace) treat scan artifacts as real lines, resulting in bloated, messy SVGs. 

**`comic2svg`** solves this with a domain-optimized processing pipeline:
1. **Adaptive Background Normalization & Despeckling**: Eliminates yellow tint and paper grain without eroding delicate ink strokes.
2. **High-Speed Rust-Powered Vectorization**: Powered by `vtracer` to convert raster scans into ultra-crisp, resolution-independent SVG bezier curves.
3. **Multi-Core Parallel Batching**: Utilizes multi-threading and process pools to convert entire multi-hundred-page comic books in seconds.

```
+---------------------+     +-----------------------+     +--------------------+
|  Scanned Comic PDF  | --> | Adaptive Clean & Prep | --> |  Rust Vector Engine| --> Clean Infinite SVG
| (Yellow/Speckled)   |     |  (OpenCV Denoise/CLAHE|     |   (Bezier Splines) |     (Crisp on 8K)
+---------------------+     +-----------------------+     +--------------------+
```

---

## 🚀 Quick Start

### Installation

```bash
# Recommended with uv (10x faster)
uv pip install comic2svg

# Or standard pip
pip install comic2svg
```

### 1. Two-Step HD Enhancement Workflow (PDF -> PNG -> Super-Resolution HD)

Extract PDF pages to PNG and upscale to 2x / 4x HD with background flattening and line sharpening:

```bash
# Step 1 & 2: PDF -> PNG -> 2x Super-Resolution HD line art
comic2svg hd my_comic.pdf --scale 2 --out ./hd_pages/

# 4x Ultra-HD with stroke reconnection and unsharp mask sharpening
comic2svg hd my_comic.pdf --scale 4 --sharpen --reconnect --out ./ultra_hd/
```

### 2. End-to-End Vectorization (PDF -> HD -> Clean SVG)

Convert directly from PDF to clean, infinite-zoom SVG with HD pre-enhancement:

```bash
comic2svg convert my_comic.pdf --hd --scale 2 --out ./output_svgs/
```

Convert a specific page range (e.g. pages 1 to 10):

```bash
comic2svg convert my_comic.pdf --pages "1-10" --out ./preview/
```

### 3. Interactive Web Studio (`comic2svg webui`)

Launch the built-in browser studio with a split-screen curtain comparison slider (Before vs Enhanced Vector) and real-time parameter tuning:

```bash
comic2svg webui
# Opens http://127.0.0.1:8080 automatically (zero extra web framework dependencies!)
```

### 4. Standalone SVG Minification & Optimization (`comic2svg optimize`)

Minify and compress SVG files by rounding bezier coordinates and stripping metadata (reduces file size by 40% ~ 60% without quality loss):

```bash
# Minify an entire directory of SVGs in-place
comic2svg optimize ./svg_pages/ --precision 2

### 5. Generate Standalone HTML5 Flipbook (`comic2svg flipbook`)

Package all generated SVG pages into a self-contained, offline HTML5 flipbook reader with keyboard navigation, full-screen mode, and infinite zooming:

```bash
# Generate flipbook directly during conversion
comic2svg convert my_comic.pdf --flipbook --out ./dist/

# Or package existing SVG files into a flipbook
comic2svg flipbook ./svg_pages/ -o ./dist/comic_reader.html --title "Classic Romance of Three Kingdoms"
```

### 6. Advanced Digitization Flags

```bash
# Auto-split landscape double-page scans at the binding gutter
comic2svg convert double_spread.pdf --split-pages --out ./pages/

# Auto-crop black scanner margins and shadows
comic2svg convert scan.pdf --crop-borders --out ./cleaned/

# Eliminate printing halftone dot screens (半色调网点)
comic2svg convert press_print.pdf --descreen --out ./smooth/
```

---

## 🎛️ Tuned Presets

Different eras of prints require different image processing strategies. `comic2svg` provides out-of-the-box presets:

| Preset Name | Target Medium | Key Characteristics |
| :--- | :--- | :--- |
| `vintage-comic` *(default)* | Aged picture books (小人书), pulp comics | Adaptive background extraction, medium despeckle, ink-bleed suppression |
| `clean-line` | Modern line art, crisp manga scans | Razor-thin stroke preservation, minimal filtering |
| `woodblock` | Block prints, heavy contrast engravings | Strong black silhouette extraction, sharp corners |
| `color-flat` | Color comics, flat cel-shaded panels | Segmented color quantization with vector boundaries |

View details from your terminal:
```bash
comic2svg presets
```

---

## 🐍 Python API

You can easily integrate `comic2svg` into your own Python pipelines:

```python
from pathlib import Path
from comic2svg import convert_file, get_preset

# Convert a PDF with custom options
results = convert_file(
    input_path="classic_story.pdf",
    output_dir="./dist_svg",
    preset="vintage-comic",
    dpi=300,
    page_range="1-5",
)

for svg_path in results:
    print(f"Generated: {svg_path}")
```

---

## 🗺️ Roadmap & Ecosystem

- [x] **v0.1.0**: Core adaptive binarization, PDF batch rendering, VTracer engine integration, preset system, parallel execution.
- [x] **v0.1.1**: Two-step HD super-resolution line restoration pipeline (Lanczos-4, flat-field illumination, unsharp mask sharpening, micro-break reconnection).
- [x] **v0.1.2**: Built-in interactive Web Studio (`comic2svg webui`) with split-view curtain slider & standalone SVG minification optimizer (`comic2svg optimize`).
- [x] **v0.1.3**: Advanced digitization suite: auto double-page split, black scanner margin cropping, halftone descreening, adaptive DPI, and standalone HTML5 vector flipbook generator.
- [ ] **v0.2.0**: Pluggable **Colorization Pipeline**:
  - Palette-based flood-fill color segmentation.
  - Optional local diffusion model / ControlNet line art colorization plugin (`pip install comic2svg[ai]`).
- [ ] **v0.3.0**: Interactive Web preview interface (Streamlit / Gradio) for instant side-by-side parameter tuning.

---

## 🤝 Contributing & Community

Contributions are warmly welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for local development instructions, test guidelines, and coding conventions.

To run the test suite locally:

```bash
pip install -e ".[dev]"
pytest -v
ruff check .
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
