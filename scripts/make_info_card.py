#!/usr/bin/env python3
"""
make_info_card.py — hand-authored neofetch-style info card SVG.

A title bar plus colored key/value rows. Each line fades and slides in
on a short stagger so the panel looks like it's printing next to the
portrait. Plays once and freezes (SMIL, GitHub-safe).

Usage:
    python scripts/make_info_card.py            # animated
    STATIC=1 python scripts/make_info_card.py   # frozen frame (previews)
Output:
    info-card.svg
"""
import os

OUT = "info-card.svg"

W = 490
BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
KEY = "#39d353"      # green keys, matches the heatmap
TXT = "#c9d1d9"
DIM = "#8b949e"
ACCENT = "#58a6ff"   # blue for the handle

FS = 13
RH = 22              # row height
PAD_X = 22
TITLE_H = 36

# (key, value) — key "" means continuation / blank spacer line
LINES = [
    ("rakshit-aryan@github", None),          # header inside body, big
    ("-" * 28, None),
    ("Now",        "Student — B.Tech, 1st year"),
    ("Prev",       "Real-time collaborative editor →"),
    ("",           "github.com/rakshitaryan0-wq"),
    ("Langs",      "Java · Python · JavaScript"),
    ("Web",        "HTML5 · CSS3 · Django · Flask"),
    ("Design",     "Adobe Creative Cloud · Canva"),
    ("Tools",      "Git · GitHub · IntelliJ · VS Code"),
    ("Badges",     "Pull Shark 🦈 · YOLO · Quickdraw 🤠"),
    ("Community",  "GDG Ranchi seminar"),
    ("Learning",   "Claude certification — Aug 2026"),
    ("", ""),
    ("$",          "echo \"open to collab\""),
]


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;"))


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    body_h = len(LINES) * RH + 30
    H = TITLE_H + body_h

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
             f'font-family="\'Courier New\',Courier,monospace" '
             f'font-size="{FS}px">')
    # Panel + border
    s.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" '
             f'fill="{BG}" stroke="{BORDER}"/>')
    # Title bar
    s.append(f'<path d="M0.5 10 a10 10 0 0 1 10 -9.5 h{W-21} '
             f'a10 10 0 0 1 10 9.5 v{TITLE_H-10} h-{W-1} z" fill="{PANEL}"/>')
    s.append(f'<line x1="0.5" y1="{TITLE_H}" x2="{W-0.5}" y2="{TITLE_H}" '
             f'stroke="{BORDER}"/>')
    # Traffic lights
    for i, c in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        s.append(f'<circle cx="{20 + i*20}" cy="{TITLE_H//2}" r="5.5" '
                 f'fill="{c}"/>')
    s.append(f'<text x="{W//2}" y="{TITLE_H//2 + 4}" fill="{DIM}" '
             f'text-anchor="middle" font-size="12">rakshit — zsh</text>')

    for i, (key, val) in enumerate(LINES):
        y = TITLE_H + 26 + i * RH
        begin = 0.25 + i * 0.18
        anim = "" if static else (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{begin:.2f}s" dur="0.35s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-8 0" to="0 0" begin="{begin:.2f}s" dur="0.35s" '
            f'fill="freeze"/>')
        op = '1' if static else '0'

        if val is None:  # header / divider lines
            color = ACCENT if "@" in key else BORDER
            weight = ' font-weight="bold" font-size="16"' if "@" in key else ''
            s.append(f'<g opacity="{op}">{anim}<text x="{PAD_X}" y="{y}" '
                     f'fill="{color}"{weight}>{esc(key)}</text></g>')
            continue

        row = f'<g opacity="{op}">{anim}'
        if key == "$":
            row += (f'<text x="{PAD_X}" y="{y}" fill="{KEY}">$</text>'
                    f'<text x="{PAD_X + 18}" y="{y}" fill="{DIM}">'
                    f'{esc(val)}</text>')
        elif key:
            row += (f'<text x="{PAD_X}" y="{y}" fill="{KEY}" '
                    f'font-weight="bold">{esc(key)}</text>'
                    f'<text x="{PAD_X + 105}" y="{y}" fill="{TXT}">'
                    f'{esc(val)}</text>')
        else:
            row += (f'<text x="{PAD_X + 105}" y="{y}" fill="{DIM}">'
                    f'{esc(val)}</text>')
        row += '</g>'
        s.append(row)

    s.append('</svg>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(s))
    print(f"wrote {OUT}: {W}x{H}px, {len(LINES)} lines, static={static}")


if __name__ == "__main__":
    main()
