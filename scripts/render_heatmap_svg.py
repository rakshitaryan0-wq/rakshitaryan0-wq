#!/usr/bin/env python3
"""
render_heatmap_svg.py — draw data/contributions.json as the classic
53-week x 7-day calendar of rounded green boxes.

Reveal: a diagonal, line-after-line slide-down (SMIL keyframes that play
on load, then freeze — no looping glow). Includes a Less->More legend
and a stats footer.

Output: contrib-heatmap.svg (860 wide to match the README layout).
"""
import datetime as dt
import json
import os

SRC = os.path.join("data", "contributions.json")
OUT = "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32",
           "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end)

BG = "#0d1117"
BORDER = "#30363d"
TXT = "#c9d1d9"
DIM = "#8b949e"

CELL = 13
GAP = 3
STEP = CELL + GAP
LEFT = 46          # room for weekday labels
TOP = 42           # room for month labels
W = 860

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_for(count: int, level: int | None) -> int:
    if level is not None:
        # GitHub gives 0..4; promote heavy days to our neon 5th level.
        return min(5, level + (1 if level == 4 and count >= 30 else 0))
    for lvl, cap in ((0, 0), (1, 3), (2, 9), (3, 19), (4, 29)):
        if count <= cap:
            return lvl
    return 5


def main() -> None:
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    days = data["days"]
    stats = data["stats"]

    # Arrange into weeks (columns), Sunday-first like GitHub.
    weeks: list[list[dict | None]] = []
    col: list[dict | None] = []
    first_dow = (dt.date.fromisoformat(days[0]["date"]).weekday() + 1) % 7
    col = [None] * first_dow
    for d in days:
        col.append(d)
        if len(col) == 7:
            weeks.append(col)
            col = []
    if col:
        weeks.append(col + [None] * (7 - len(col)))

    n_weeks = len(weeks)
    grid_w = n_weeks * STEP - GAP
    scale = 1.0
    inner = LEFT + grid_w + 18
    if inner > W:
        scale = (W - LEFT - 18) / grid_w

    H = TOP + 7 * STEP + 84

    s = []
    s.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
             f'font-family="\'Segoe UI\',Helvetica,Arial,sans-serif" '
             f'font-size="12px">')
    s.append(f'<rect width="100%" height="100%" rx="10" fill="{BG}" '
             f'stroke="{BORDER}"/>')
    s.append(f'<text x="{LEFT}" y="24" fill="{TXT}" font-size="14" '
             f'font-weight="600">@{data["username"]} — last 12 months</text>')

    # Month labels — first week where a new month starts; skip a label if
    # it would crowd the previous one (partial first month).
    seen = set()
    last_x = -1e9
    for wi, week in enumerate(weeks):
        d0 = next((d for d in week if d), None)
        if not d0:
            continue
        mo = d0["date"][:7]
        if mo in seen:
            continue
        seen.add(mo)
        x = LEFT + wi * STEP * scale
        if x - last_x < 30:
            continue
        last_x = x
        m = int(mo[5:7]) - 1
        s.append(f'<text x="{x:.0f}" y="{TOP - 8}" fill="{DIM}">'
                 f'{MONTHS[m]}</text>')

    # Weekday labels.
    for dow, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        y = TOP + dow * STEP + CELL - 3
        s.append(f'<text x="8" y="{y}" fill="{DIM}">{label}</text>')

    # Cells with diagonal slide-in: delay = f(col + row).
    static = os.environ.get("STATIC") == "1"
    for wi, week in enumerate(weeks):
        for di, d in enumerate(week):
            if d is None:
                continue
            x = LEFT + wi * STEP * scale
            y = TOP + di * STEP
            lvl = level_for(d["count"], d.get("level"))
            if static:
                s.append(f'<rect x="{x:.1f}" y="{y}" '
                         f'width="{CELL * scale:.1f}" height="{CELL}" '
                         f'rx="3" fill="{PALETTE[lvl]}"/>')
                continue
            begin = 0.10 + (wi + di) * 0.018
            s.append(
                f'<rect x="{x:.1f}" y="{y}" width="{CELL * scale:.1f}" '
                f'height="{CELL}" rx="3" fill="{PALETTE[lvl]}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.3f}s" dur="0.30s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" '
                f'type="translate" from="0 -10" to="0 0" '
                f'begin="{begin:.3f}s" dur="0.30s" fill="freeze"/></rect>')

    # Footer: stats left, legend right.
    fy = TOP + 7 * STEP + 34
    total = stats.get("total", 0)
    cur = stats.get("current_streak", 0)
    lng = stats.get("longest_streak", 0)
    note = " · sample data, refreshes on first push" if data.get("sample") \
        else ""
    s.append(f'<text x="{LEFT}" y="{fy}" fill="{TXT}" font-weight="600">'
             f'{total:,} contributions in the last year</text>')
    s.append(f'<text x="{LEFT}" y="{fy + 19}" fill="{DIM}">'
             f'current streak {cur}d · longest {lng}d{note}</text>')

    lx = W - 200
    s.append(f'<text x="{lx - 34}" y="{fy}" fill="{DIM}">Less</text>')
    for i, c in enumerate(PALETTE):
        s.append(f'<rect x="{lx + i * 17}" y="{fy - 10}" width="13" '
                 f'height="13" rx="3" fill="{c}"/>')
    s.append(f'<text x="{lx + 6 * 17 + 6}" y="{fy}" fill="{DIM}">More</text>')

    s.append('</svg>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(s))
    print(f"wrote {OUT}: {n_weeks} weeks, total={total}")


if __name__ == "__main__":
    main()
