"""Built-in lightweight Web UI server for comic2svg.

Provides an interactive browser studio with split-screen curtain slider,
real-time parameter tuning, and one-click SVG/HD-PNG export. Zero extra
framework dependencies required.
"""

import cgi
import http.server
import json
import os
from pathlib import Path
import tempfile
from typing import Optional
import urllib.parse
import webbrowser

from .enhance import enhance_to_hd
from .optimizer import optimize_svg_content
from .preprocess import clean_image
from .presets import get_preset
from .vectorize import vectorize_image

STATIC_DIR = Path(__file__).parent / "web"


class StudioRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler serving the studio interface and processing APIs."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path in ["", "/", "/index.html"]:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_file = STATIC_DIR / "index.html"
            self.wfile.write(html_file.read_bytes())
            return
        elif parsed.path.startswith("/temp/"):
            # Serve temporary image file
            filename = os.path.basename(parsed.path)
            tmp_path = Path(tempfile.gettempdir()) / "comic2svg_web" / filename
            if tmp_path.exists():
                self.send_response(200)
                if filename.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                elif filename.endswith(".svg"):
                    self.send_header("Content-Type", "image/svg+xml")
                self.end_headers()
                self.wfile.write(tmp_path.read_bytes())
                return
            else:
                self.send_error(404, "File not found")
                return

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/process":
            try:
                self._handle_process_api()
            except Exception as e:
                self._send_json({"success": False, "error": str(e)}, status=500)
            return

        self.send_error(404, "Not Found")

    def _send_json(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def _handle_process_api(self):
        # Parse multipart form data
        ctype, pdict = cgi.parse_header(self.headers.get("content-type"))
        if ctype != "multipart/form-data":
            self._send_json({"success": False, "error": "Expected multipart/form-data"}, status=400)
            return

        pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
        fields = cgi.parse_multipart(self.rfile, pdict)

        file_data_list = fields.get("file")
        if not file_data_list or len(file_data_list) == 0:
            self._send_json({"success": False, "error": "No file uploaded"}, status=400)
            return

        file_bytes = file_data_list[0]
        preset_name = fields.get("preset", ["vintage-comic"])[0]
        scale = float(fields.get("scale", [2.0])[0])
        flat_field = fields.get("flat_field", ["true"])[0].lower() == "true"
        sharpen = fields.get("sharpen", ["true"])[0].lower() == "true"
        reconnect = fields.get("reconnect", ["true"])[0].lower() == "true"
        optimize = fields.get("optimize", ["true"])[0].lower() == "true"
        precision = int(fields.get("precision", [2])[0])

        # Prepare temporary workspace
        tmp_dir = Path(tempfile.gettempdir()) / "comic2svg_web"
        tmp_dir.mkdir(parents=True, exist_ok=True)

        raw_in = tmp_dir / "uploaded_input.png"
        raw_in.write_bytes(file_bytes)
        orig_bytes = len(file_bytes)

        # 1. HD Enhancement
        hd_out = tmp_dir / "preview_hd.png"
        enhance_to_hd(
            input_path=raw_in,
            output_path=hd_out,
            scale=scale,
            sharpen=sharpen,
            flat_field=flat_field,
            reconnect=reconnect,
        )

        # 2. Preprocess & Clean
        preset = get_preset(preset_name)
        cleaned_out = tmp_dir / "preview_cleaned.png"
        clean_image(hd_out, cleaned_out, preset=preset)

        # 3. Vectorize to SVG
        svg_out = tmp_dir / "preview.svg"
        vectorize_image(cleaned_out, svg_out, preset=preset)

        # 4. Minification / Optimization if requested
        svg_text = svg_out.read_text(encoding="utf-8")
        unopt_bytes = len(svg_text.encode("utf-8"))

        if optimize:
            svg_text = optimize_svg_content(svg_text, precision=precision)
            svg_out.write_text(svg_text, encoding="utf-8")

        final_svg_bytes = len(svg_text.encode("utf-8"))
        savings_percent = ((unopt_bytes - final_svg_bytes) / unopt_bytes * 100.0) if unopt_bytes > 0 else 0.0

        self._send_json({
            "success": True,
            "svg_content": svg_text,
            "orig_bytes": orig_bytes,
            "svg_bytes": final_svg_bytes,
            "savings_percent": savings_percent,
            "hd_png_url": "/temp/preview_hd.png",
        })


def run_webui(host: str = "127.0.0.1", port: int = 8080, open_browser: bool = True):
    """Launch the interactive comic2svg Studio in the user's browser."""
    server_address = (host, port)
    httpd = http.server.HTTPServer(server_address, StudioRequestHandler)
    url = f"http://{host}:{port}"

    print(f"\n========================================================")
    print(f"🚀 comic2svg Studio is running at: {url}")
    print(f"Press Ctrl+C to stop the server.")
    print(f"========================================================\n")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping comic2svg Studio server...")
        httpd.server_close()
