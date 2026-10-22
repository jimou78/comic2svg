"""Standalone single-file HTML5 SVG comic flipbook generator.

Packages multi-page SVG comics into an interactive, zero-dependency offline
reader with smooth page transitions, keyboard shortcuts, and infinite vector zooming.
"""

from pathlib import Path
from typing import List, Union


def generate_flipbook(
    svg_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    title: str = "comic2svg Flipbook",
) -> Path:
    """Generate a self-contained offline HTML5 reader embedding all comic SVGs."""
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    sorted_svgs = sorted([Path(p) for p in svg_paths])
    if not sorted_svgs:
        raise ValueError("No SVG files provided to generate flipbook.")

    # Read and sanitize SVG contents
    svg_data_list = []
    for p in sorted_svgs:
        raw_svg = p.read_text(encoding="utf-8").strip()
        svg_data_list.append(raw_svg)

    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
  <title>{title}</title>
  <style>
    :root {{
      --bg: #090d16;
      --bar-bg: rgba(15, 23, 42, 0.85);
      --accent: #38bdf8;
      --text: #f8fafc;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); height: 100vh; overflow: hidden; display: flex; flex-direction: column; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    
    header {{ height: 48px; background: var(--bar-bg); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; border-bottom: 1px solid #1e293b; z-index: 10; }}
    header h1 {{ font-size: 1rem; font-weight: 600; color: var(--accent); }}
    .controls {{ display: flex; gap: 8px; align-items: center; }}
    button {{ background: #1e293b; color: var(--text); border: 1px solid #334155; padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: 0.85rem; transition: background 0.15s; }}
    button:hover {{ background: #334155; }}

    .stage {{ flex: 1; position: relative; display: flex; align-items: center; justify-content: center; overflow: auto; padding: 16px; cursor: grab; }}
    .stage:active {{ cursor: grabbing; }}
    .page-container {{ max-width: 100%; max-height: 100%; display: flex; align-items: center; justify-content: center; transition: transform 0.15s ease-out; transform-origin: center center; }}
    .page-container svg {{ max-height: 85vh; max-width: 90vw; filter: drop-shadow(0 10px 25px rgba(0,0,0,0.5)); border-radius: 4px; background: #fff; }}

    footer {{ height: 52px; background: var(--bar-bg); backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; gap: 16px; border-top: 1px solid #1e293b; padding: 0 20px; z-index: 10; }}
    .nav-btn {{ font-weight: bold; padding: 6px 16px; }}
    .page-indicator {{ font-size: 0.9rem; font-family: monospace; min-width: 80px; text-align: center; }}
    input[type="range"] {{ width: 220px; accent-color: var(--accent); cursor: pointer; }}
  </style>
</head>
<body>
  <header>
    <h1>📖 {title}</h1>
    <div class="controls">
      <button onclick="toggleZoom(0.2)">🔍 放大</button>
      <button onclick="toggleZoom(-0.2)">🔍 缩小</button>
      <button onclick="resetZoom()">⟲ 重置</button>
      <button onclick="toggleFullScreen()">⛶ 全屏</button>
    </div>
  </header>

  <div class="stage" id="stage" onclick="handleStageClick(event)">
    <div class="page-container" id="pageContainer"></div>
  </div>

  <footer>
    <button class="nav-btn" onclick="prevPage()">‹ 上一页 (←)</button>
    <input type="range" id="pageSlider" min="0" max="{len(svg_data_list) - 1}" value="0" oninput="goToPage(this.value)">
    <span class="page-indicator" id="pageIndicator">1 / {len(svg_data_list)}</span>
    <button class="nav-btn" onclick="nextPage()">下一页 (→) ›</button>
  </footer>

  <script>
    const pages = {list(range(len(svg_data_list)))};
    const totalPages = {len(svg_data_list)};
    let currentIndex = 0;
    let zoomLevel = 1.0;

    // Injected raw SVGs
    const svgStorage = [];
"""

    # Inject SVG elements safely
    for idx, svg_text in enumerate(svg_data_list):
        # Escape backticks and backslashes
        escaped = svg_text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        html_template += f"\n    svgStorage.push(`{escaped}`);"

    html_template += """

    function renderCurrentPage() {
      const container = document.getElementById('pageContainer');
      container.innerHTML = svgStorage[currentIndex];
      document.getElementById('pageIndicator').innerText = (currentIndex + 1) + ' / ' + totalPages;
      document.getElementById('pageSlider').value = currentIndex;
      applyZoom();
    }

    function nextPage() {
      if (currentIndex < totalPages - 1) {
        currentIndex++;
        renderCurrentPage();
      }
    }

    function prevPage() {
      if (currentIndex > 0) {
        currentIndex--;
        renderCurrentPage();
      }
    }

    function goToPage(idx) {
      currentIndex = parseInt(idx, 10);
      renderCurrentPage();
    }

    function toggleZoom(delta) {
      zoomLevel = Math.max(0.6, Math.min(4.0, zoomLevel + delta));
      applyZoom();
    }

    function resetZoom() {
      zoomLevel = 1.0;
      applyZoom();
    }

    function applyZoom() {
      document.getElementById('pageContainer').style.transform = `scale(${zoomLevel})`;
    }

    function handleStageClick(e) {
      if (e.target.tagName.toLowerCase() === 'button') return;
      const width = window.innerWidth;
      if (e.clientX > width * 0.65) nextPage();
      else if (e.clientX < width * 0.35) prevPage();
    }

    function toggleFullScreen() {
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        if (document.exitFullscreen) document.exitFullscreen();
      }
    }

    // Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown') {
        e.preventDefault();
        nextPage();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault();
        prevPage();
      } else if (e.key === '+' || e.key === '=') {
        toggleZoom(0.2);
      } else if (e.key === '-') {
        toggleZoom(-0.2);
      } else if (e.key === '0') {
        resetZoom();
      } else if (e.key === 'f' || e.key === 'F') {
        toggleFullScreen();
      }
    });

    // Initial render
    renderCurrentPage();
  </script>
</body>
</html>
"""

    out_file.write_text(html_template, encoding="utf-8")
    return out_file
