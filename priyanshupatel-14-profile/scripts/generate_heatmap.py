#!/usr/bin/env python3
"""Wardenclyffe-themed contribution heatmap: lightning strikes your calendar.

Tesla's tower stands above your contribution grid and fires lightning at your
most active days (the latest contribution is always one of the targets).
Output is a standalone animated SVG (CSS animations only, works inside <img>).

    MOCK=1 python scripts/generate_heatmap.py          # fake data, no token
    GITHUB_TOKEN=... python scripts/generate_heatmap.py
    MOCK=1 FLASH=1 python scripts/generate_heatmap.py  # freeze a "mid-strike" frame

The output has no timestamps, so the bot only commits when your data changes.
"""
import json
import math
import os
import random
import urllib.request
from datetime import date, timedelta

LOGIN = os.environ.get("GH_USER", "priyanshupatel-14")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = os.environ.get("OUT", "assets/contribution-heatmap.svg")
MOCK = os.environ.get("MOCK") == "1"
FLASH = os.environ.get("FLASH") == "1"

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
# deep navy -> electric blue -> cyan
COLORS = ["#0E1A33", "#14336B", "#1E5BC6", "#3C9BFF", "#7DE3FF"]
BOLT, GLOW, STREAK = "#D8F3FF", "#2D7BFF", "#5CC8FF"
SPARK = "#A8E6FF"
BG = "#060B18"
MUTED = "#5D739E"
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

CELL, GAP = 11, 3
PITCH = CELL + GAP
LEFT, TOP = 36, 56
# (cycle seconds, start offset) per bolt: staggered so strikes never sync up
TIMINGS = [(5.4, 1.2), (6.3, 3.1), (7.1, 0.4), (5.9, 4.3), (6.7, 2.2)]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel weekday } }
      }
    }
  }
}
"""


# ---------------------------------------------------------------- data
def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {TOKEN}",
                 "Content-Type": "application/json",
                 "User-Agent": "heatmap-bot"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], cal["weeks"]


def mock():
    rnd = random.Random(7)
    end = date.today()
    start = end - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back up to a Sunday
    weeks, total, d = [], 0, start
    while d <= end:
        days = []
        for _ in range(7):
            if d > end:
                break
            lvl = rnd.choice([0, 0, 0, 1, 1, 2, 3, 4])
            cnt = lvl * rnd.randint(1, 3)
            total += cnt
            days.append({"date": d.isoformat(), "contributionCount": cnt,
                         "contributionLevel": list(LEVELS)[lvl],
                         "weekday": (d.weekday() + 1) % 7})
            d += timedelta(days=1)
        weeks.append({"contributionDays": days})
    return total, weeks


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    seq = list(days)
    if seq and seq[-1]["contributionCount"] == 0:  # today not done yet
        seq = seq[:-1]
    current = 0
    for d in reversed(seq):
        if d["contributionCount"] > 0:
            current += 1
        else:
            break
    return current, longest


# ------------------------------------------------------------ lightning
def jagged(rnd, x1, y1, x2, y2, disp, depth):
    """Midpoint-displacement lightning path from (x1,y1) to (x2,y2)."""
    pts = [(x1, y1), (x2, y2)]
    for _ in range(depth):
        out = [pts[0]]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            dx, dy = bx - ax, by - ay
            length = math.hypot(dx, dy) or 1.0
            nx, ny = -dy / length, dx / length
            off = rnd.uniform(-1, 1) * disp
            out += [((ax + bx) / 2 + nx * off, (ay + by) / 2 + ny * off), (bx, by)]
        pts = out
        disp *= 0.55
    return pts


def fmt(pts):
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def pick_targets(weeks, k=5):
    """Latest active day first, then the busiest days, spread across the year."""
    cells = [(LEVELS.get(d["contributionLevel"], 0), d["contributionCount"], w, d["weekday"])
             for w, wk in enumerate(weeks) for d in wk["contributionDays"]]
    active = [c for c in cells if c[1] > 0] or cells[-k:]
    picks = [max(active, key=lambda c: (c[2], c[3]))]
    ranked = sorted(active, key=lambda c: (-c[0], -c[1], -c[2], c[3]))
    for gap in (6, 3, 1, 0):
        for c in ranked:
            if len(picks) >= k:
                break
            if c not in picks and all(abs(c[2] - p[2]) >= gap for p in picks):
                picks.append(c)
    return picks[:k]


# ------------------------------------------------------------ drawing
CSS = """
text{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.c0{fill:@C0@}.c1{fill:@C1@}.c2{fill:@C2@}.c3{fill:@C3@}.c4{fill:@C4@}
.bolt,.spark{opacity:0;animation:zap var(--t) linear var(--o) infinite}
@keyframes zap{
 0%,100%{opacity:0}
 1%{opacity:var(--pk)}
 3%{opacity:calc(var(--pk)*.15)}
 5%{opacity:var(--pk)}
 8%{opacity:calc(var(--pk)*.45)}
 14%{opacity:calc(var(--pk)*.12)}
 20%{opacity:0}
}
.hum{opacity:.6;animation:hum 3.4s ease-in-out infinite}
@keyframes hum{0%,100%{opacity:.4}50%{opacity:.9}}
@media (prefers-reduced-motion:reduce){
 .bolt,.spark,.hum{animation:none!important}
 .bolt{opacity:0}.b0{opacity:.9}
}
"""


def tower(cx):
    g, top_y, base_y = 112, 44, 112 - 19
    hw_top, hw_base = 4.5, 15
    o = [f'<polygon points="{cx - 40},{g - 13} {cx - 34},{g - 19} {cx + 34},{g - 19} '
         f'{cx + 40},{g - 13}" fill="#040810"/>',
         f'<rect x="{cx - 38}" y="{g - 13}" width="76" height="13" fill="#040810"/>']
    for i in range(7):  # arched windows of the brick laboratory
        o.append(f'<rect x="{cx - 31 + i * 10}" y="{g - 9}" width="3" height="6" rx="1.5" '
                 f'fill="#1F4FA3"/>')
    o.append(f'<polygon points="{cx - hw_base},{base_y} {cx - hw_top},{top_y} '
             f'{cx + hw_top},{top_y} {cx + hw_base},{base_y}" fill="#0B1630" '
             f'stroke="#040810" stroke-width="1.4"/>')
    n = 5
    for i in range(n):  # lattice cross-bracing
        y1 = top_y + (base_y - top_y) * i / n
        y2 = top_y + (base_y - top_y) * (i + 1) / n
        h1 = hw_top + (hw_base - hw_top) * i / n
        h2 = hw_top + (hw_base - hw_top) * (i + 1) / n
        o.append(f'<path d="M{cx - h1:.1f} {y1:.1f}L{cx + h2:.1f} {y2:.1f}'
                 f'M{cx + h1:.1f} {y1:.1f}L{cx - h2:.1f} {y2:.1f}'
                 f'M{cx - h2:.1f} {y2:.1f}L{cx + h2:.1f} {y2:.1f}" '
                 f'stroke="#040810" stroke-width="1.1" fill="none"/>')
    o.append(f'<rect x="{cx - 1.4}" y="{top_y}" width="2.8" height="{base_y - top_y}" fill="#040810"/>')
    o.append(f'<rect x="{cx - 10}" y="{top_y - 4}" width="20" height="4" fill="#040810"/>')
    o.append(f'<path d="M{cx - 24} 37C{cx - 24} 17 {cx + 24} 17 {cx + 24} 37Z" '
             f'fill="#050A16" stroke="#1B2B52" stroke-width=".8"/>')
    o.append(f'<path d="M{cx - 16} 36Q{cx - 12} 25 {cx} 22Q{cx + 12} 25 {cx + 16} 36" '
             f'stroke="#1B2B52" stroke-width=".7" fill="none"/>')
    o.append(f'<rect x="{cx - 25}" y="36" width="50" height="3" rx="1" fill="#040810"/>')
    o.append(f'<rect x="{cx - .8}" y="16" width="1.6" height="7" fill="#040810"/>')
    return o


def build(total, weeks):
    days = [d for w in weeks for d in w["contributionDays"]]
    cur, longest = streaks(days)
    n = len(weeks)
    grid_w, grid_h = n * PITCH - GAP, 7 * PITCH - GAP
    width = LEFT + grid_w + 24
    oy = TOP + grid_h + 10          # tower origin (below the calendar)
    ground, dome_y = oy + 112, oy + 30
    height = ground + 28
    cx = round(LEFT + grid_w / 2)

    css = CSS
    for i, c in enumerate(COLORS):
        css = css.replace(f"@C{i}@", c)
    if FLASH:  # dev preview: freeze a mid-strike frame
        css += ".bolt{opacity:1!important;animation:none!important}" \
               ".spark{opacity:var(--pk)!important;animation:none!important}"

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
         f'viewBox="0 0 {width} {height}" role="img" '
         f'aria-label="Wardenclyffe Tower striking lightning on a contribution calendar: '
         f'{total} contributions in the last year">',
         f"<style>{css}</style>",
         f'<defs>'
         f'<radialGradient id="sky" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{dome_y}" r="400">'
         f'<stop offset="0" stop-color="#12285A"/><stop offset=".55" stop-color="#0A1633"/>'
         f'<stop offset="1" stop-color="{BG}"/></radialGradient>'
         f'<radialGradient id="halo"><stop offset="0" stop-color="#D8F3FF" stop-opacity=".9"/>'
         f'<stop offset=".45" stop-color="{GLOW}" stop-opacity=".35"/>'
         f'<stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></radialGradient>'
         f'<radialGradient id="amb"><stop offset="0" stop-color="{GLOW}" stop-opacity=".4"/>'
         f'<stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></radialGradient>'
         f'<linearGradient id="hz" x1="0" x2="1" y1="0" y2="0">'
         f'<stop offset="0" stop-color="#24407A" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="#24407A"/>'
         f'<stop offset="1" stop-color="#24407A" stop-opacity="0"/></linearGradient>'
         f'<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="{width}" '
         f'height="{height}"><feGaussianBlur stdDeviation="2.2"/></filter>'
         f'</defs>',
         f'<rect width="{width}" height="{height}" rx="12" fill="{BG}"/>',
         f'<rect width="{width}" height="{height}" rx="12" fill="url(#sky)"/>',
         f'<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" '
         f'fill="none" stroke="#1B2B52"/>',
         f'<text x="{LEFT}" y="28" font-size="15" font-weight="600" fill="#DCE8FF">'
         f'{total:,} contributions in the last year</text>',
         f'<text x="{width - 24}" y="28" font-size="12" fill="#6F86B3" text-anchor="end">'
         f'Streak <tspan fill="{STREAK}" font-weight="600">{cur}d</tspan>'
         f' · Longest <tspan fill="#8FB2FF" font-weight="600">{longest}d</tspan></text>',
         f'<line x1="{LEFT}" y1="{ground}" x2="{width - 24}" y2="{ground}" '
         f'stroke="url(#hz)" stroke-width="1"/>']

    last_m, last_w = None, -10
    for w, wk in enumerate(weeks):  # month labels
        m = int(wk["contributionDays"][0]["date"][5:7])
        if m != last_m:
            if w - last_w >= 3:
                o.append(f'<text x="{LEFT + w * PITCH}" y="{TOP - 8}" font-size="10" '
                         f'fill="#5D739E">{MONTHS[m - 1]}</text>')
                last_w = w
            last_m = m
    for wd, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="{LEFT - 8}" y="{TOP + wd * PITCH + 9}" font-size="10" '
                 f'fill="#5D739E" text-anchor="end">{name}</text>')

    exist = set()
    for w, wk in enumerate(weeks):  # the calendar board
        for d in wk["contributionDays"]:
            lvl = LEVELS.get(d["contributionLevel"], 0)
            exist.add((w, d["weekday"]))
            o.append(f'<rect class="c{lvl}" x="{LEFT + w * PITCH}" '
                     f'y="{TOP + d["weekday"] * PITCH}" width="{CELL}" height="{CELL}" rx="2.5"/>')

    picks = pick_targets(weeks)
    sparks, bolts, halos = [], [], []
    for i, (lvl, cnt, w, wd) in enumerate(picks):
        t, off = TIMINGS[i % len(TIMINGS)]
        var = f"--t:{t}s;--o:{off}s"
        rnd = random.Random(f"{w}-{wd}-{cnt}")
        tx, ty = LEFT + w * PITCH + CELL / 2, TOP + wd * PITCH + CELL / 2
        sx, sy = cx + rnd.uniform(-18, 18), oy + 27

        # cells flash white where the bolt lands (centre hardest, neighbours softer)
        for dw in (-1, 0, 1):
            for dd in (-1, 0, 1):
                if (w + dw, wd + dd) in exist:
                    pk = .95 if (dw, dd) == (0, 0) else (.5 if 0 in (dw, dd) else .32)
                    sparks.append(
                        f'<rect class="spark" x="{LEFT + (w + dw) * PITCH}" '
                        f'y="{TOP + (wd + dd) * PITCH}" width="{CELL}" height="{CELL}" '
                        f'rx="2.5" fill="{SPARK}" style="{var};--pk:{pk}"/>')

        main = jagged(rnd, sx, sy, tx, ty, min(26, math.hypot(tx - sx, ty - sy) * .14), 5)
        g = [f'<g class="bolt b{i}" style="{var};--pk:1">',
             f'<rect width="{width}" height="{height}" rx="12" fill="{SPARK}" opacity=".06"/>',
             f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="22" fill="url(#halo)"/>',
             f'<polyline points="{fmt(main)}" fill="none" stroke="{GLOW}" stroke-width="5" '
             f'stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>']
        branches = []
        for _ in range(2):
            bx, by = main[rnd.randint(len(main) // 4, 3 * len(main) // 4)]
            ex = min(max(bx + rnd.uniform(-70, 70), LEFT), width - 24)
            ey = max(by - rnd.uniform(20, 45), TOP + 2)
            branches.append(jagged(rnd, bx, by, ex, ey, 8, 3))
        for b in branches:
            g.append(f'<polyline points="{fmt(b)}" fill="none" stroke="{GLOW}" '
                     f'stroke-width="3" stroke-linejoin="round" filter="url(#glow)"/>')
        for b in branches:
            g.append(f'<polyline points="{fmt(b)}" fill="none" stroke="{BOLT}" '
                     f'stroke-width=".9" stroke-linejoin="round" opacity=".8"/>')
        g.append(f'<polyline points="{fmt(main)}" fill="none" stroke="{BOLT}" '
                 f'stroke-width="1.6" stroke-linejoin="round" stroke-linecap="round"/>')
        g.append("</g>")
        bolts.append("\n".join(g))
        halos.append(f'<circle class="spark" cx="{cx}" cy="{dome_y}" r="30" fill="url(#halo)" '
                     f'style="{var};--pk:.9"/>')

    o += sparks + bolts + [f'<g transform="translate(0,{oy})">'] + tower(cx) + ["</g>"] + halos
    o.append(f'<circle class="hum" cx="{cx}" cy="{dome_y}" r="36" fill="url(#amb)"/>')

    ly = ground + 7  # legend
    sq0 = width - 24 - 36 - 5 * PITCH
    o.append(f'<text x="{sq0 - 6}" y="{ly + 9}" font-size="10" fill="#5D739E" '
             f'text-anchor="end">Less</text>')
    for i in range(5):
        o.append(f'<rect x="{sq0 + i * PITCH}" y="{ly}" width="{CELL}" height="{CELL}" '
                 f'rx="2.5" fill="{COLORS[i]}" stroke="#1B2B52" stroke-width=".6"/>')
    o.append(f'<text x="{width - 24}" y="{ly + 9}" font-size="10" fill="#5D739E" '
             f'text-anchor="end">More</text>')
    o.append(f'<text x="{LEFT}" y="{ly + 9}" font-size="10" letter-spacing="1" '
             f'fill="{MUTED}">POWERED BY COMMITS</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    total, weeks = mock() if MOCK else fetch()
    svg = build(total, weeks)
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote {OUT} ({total} contributions, {len(weeks)} weeks)")


if __name__ == "__main__":
    main()
