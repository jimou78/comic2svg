# Examples and Public Domain Samples

This directory provides public-domain sample illustrations and demonstration scripts for `comic2svg`.

## Sample Workflow

Convert a scanned sample page with the vintage comic preset:

```bash
comic2svg convert examples/sample_vintage.png --out out/ --preset vintage-comic
```

Compare presets:

```bash
# High contrast woodblock preset
comic2svg convert examples/sample_vintage.png --out out_woodblock/ --preset woodblock

# Clean thin line art preset
comic2svg convert examples/sample_vintage.png --out out_clean/ --preset clean-line
```

> **Note on Copyright**: All sample media committed to this repository are sourced from verified public domain archives (pre-1928 publications or Creative Commons zero scans) to respect copyright and maintain open-source compliance.
