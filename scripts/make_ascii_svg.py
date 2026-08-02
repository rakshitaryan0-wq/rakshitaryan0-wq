#!/usr/bin/env python3
"""
make_ascii_svg.py — convert the prepped grayscale photo into a
self-typing monochrome ASCII-art SVG.

Design choices (deliberate):
  * Monochrome — one light-gray fill. Per-character rainbow coloring is
    what makes most ASCII portraits look like static.
  * High contrast — the white background maps to the leading space in
    the ramp, so only the subject prints.
  * Each row is wrapped in a horizontal clip that wipes left-to-right
    with a small block "cursor" riding the wipe edge, staggered top to
    bottom. Prints once and freezes — no looping. SMIL, so GitHub plays it.

Usage:
    python scripts/make_ascii_svg.py            # animated
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame (previews)
Output:
    rakshit-ascii.svg
"""
import os

import numpy as np
from PIL import Image

SRC = "source-prepped.png"
OUT = "rakshit-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
COLS = 100

FS = 8.0                  # font size (px)
CW = FS * 0.60            # monospace char advance
RH = FS * 1.08            # row height
PAD = 16                  # inner padding
BG = "#0d1117"            # GitHub dark canvas
FG = "#c9d1d9"            # light gray glyphs
CURSOR = "#39d353"        # green cursor block

ROW_DUR = 0.55            # seconds per row wipe
STAGGER = 0.055           # start offset between rows


def load_grid() -> np.ndarray:
    img = Image.open(SRC).convert("L")
    a = np.asarray(img, dtype=np.float32)

    # Crop to the subject (non-white content) with a small margin.
    ys, xs = np.where(a < 250)
    m = 12
    y0, y1 = max(ys.min() - m, 0), min(ys.max() + m, a.shape[0])
    x0, x1 = max(xs.min() - m, 0), min(xs.max() + m, a.shape[1])
    a = a[y0:y1, x0:x1]

    # Rows follow from the crop aspect and the char cell aspect.
    rows = max(1, round((a.shape[0] / a.shape[1]) * COLS * (CW / RH)))
    small = Image.fromarray(a.astype(np.uint8)).resize(
        (COLS, rows), Image.Resampling.LANCZOS)
    return np.asarray(small, dtype=np.float32) / 255.0


def to_ascii(grid: np.ndarray) -> list[str]:
    # Slight gamma to enrich midtones before quantizing to the ramp.
    g = np.clip(grid, 0.0, 1.0) ** 1.45
    idx = np.round((1.0 - g) * (len(RAMP) - 1)).astype(int)
    return ["".join(RAMP[i] for i in row) for row in idx]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    lines = to_ascii(load_grid())
    rows = len(lines)

    text_w = COLS * CW
    width = text_w + PAD * 2
    height = rows * RH + PAD * 2

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" '
        f'width="{width:.0f}" height="{height:.0f}" '
        f'font-family="\'Courier New\',Courier,monospace" '
        f'font-size="{FS}px">')
    svg.append(f'<rect width="100%" height="100%" rx="8" fill="{BG}"/>')

    for r, line in enumerate(lines):
        if not line.strip():
            continue
        y = PAD + (r + 0.85) * RH
        begin = r * STAGGER
        if static:
            svg.append(
                f'<text x="{PAD}" y="{y:.1f}" fill="{FG}" '
                f'xml:space="preserve" textLength="{text_w:.0f}">'
                f'{esc(line)}</text>')
            continue

        # Row clipped by a rect whose width wipes 0 -> full.
        svg.append(f'<clipPath id="c{r}"><rect x="{PAD}" y="{y - RH:.1f}" '
                   f'width="0" height="{RH + 2:.1f}">'
                   f'<animate attributeName="width" from="0" to="{text_w:.0f}" '
                   f'begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>'
                   f'</rect></clipPath>')
        svg.append(
            f'<text x="{PAD}" y="{y:.1f}" fill="{FG}" xml:space="preserve" '
            f'textLength="{text_w:.0f}" clip-path="url(#c{r})">'
            f'{esc(line)}</text>')
        # Block cursor riding the wipe edge, then vanishing.
        svg.append(
            f'<rect x="{PAD}" y="{y - FS + 1:.1f}" width="{CW * 1.4:.1f}" '
            f'height="{FS:.1f}" fill="{CURSOR}" opacity="0">'
            f'<animate attributeName="opacity" from="1" to="1" '
            f'begin="{begin:.2f}s" dur="{ROW_DUR}s"/>'
            f'<animate attributeName="x" from="{PAD}" '
            f'to="{PAD + text_w:.0f}" begin="{begin:.2f}s" '
            f'dur="{ROW_DUR}s"/></rect>')

    svg.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))
    print(f"wrote {OUT}: {rows} rows x {COLS} cols, "
          f"{width:.0f}x{height:.0f}px, static={static}")


if __name__ == "__main__":
    main()
