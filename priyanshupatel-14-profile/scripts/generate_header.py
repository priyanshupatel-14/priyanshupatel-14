#!/usr/bin/env python3
"""Animated profile header: glowing name, lightning strikes and a typing effect.

Pure SVG (CSS + SMIL), self-hosted, no external service. Edit NAME / SUBTITLE /
LINES below and re-run (or let the workflow do it on push):

    python scripts/generate_header.py
    FLASH=1 python scripts/generate_header.py   # dev: freeze a mid-strike frame
"""
import html
import os
import random

from generate_heatmap import (BG, BOLT, FLASH, GLOW, MUTED, SPARK, STREAK,
                              fmt, jagged)

OUT = os.environ.get("HEADER_OUT", "assets/header.svg")

NAME = "PRIYANSHU PATEL"
SUBTITLE = "AI/ML  •  FLUTTER  •  SPRING BOOT  •  WIFI PENTESTING"
LINES = [  # typed one after another, on a loop (keep each under ~45 characters)
    "Building intelligent systems with AI & ML",
    "Full-stack apps with Flutter + Spring Boot",
    "WiFi pentesting and wireless security",
    "Shipping CarbonTrack for greener campuses",
]

W, H = 799, 214            # same width as the heatmap so the two line up
CX = W / 2
TITLE_Y, TITLE_SIZE, TITLE_W = 98, 42, 450
SUB_Y, TYPE_Y, TYPE_SIZE = 126, 162, 19
CHAR_W = TYPE_SIZE * 0.6   # monospace advance; textLength pins it for every font
SLOT, TYPE_DT, ERASE_DT, HOLD = 6.0, 0.055, 0.025, 1.8
TIMINGS = [(5.4, 1.2), (6.3, 3.1), (7.1, 0.4), (5.9, 4.3)]
TARGETS = [(CX - 205, 68), (CX + 200, 76), (CX - 70, 58), (CX + 95, 62)]

CSS = """
text{font-family:-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.mono{font-family:"Fira Code","JetBrains Mono",SFMono-Regular,Consolas,"Liberation Mono",monospace}
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
@keyframes hum{0%,100%{opacity:.35}50%{opacity:.85}}
.run{animation:run 4.5s ease-in-out infinite both}
@keyframes run{from{transform:translateX(30px)}to{transform:translateX(@RUN@px)}}
@media (prefers-reduced-motion:reduce){
 .bolt,.spark,.hum,.run{animation:none!important}
 .bolt{opacity:0}.b0{opacity:.9}
}
"""


def typing(i, text, n_lines):
    """Clip-reveal typing for one line: types, holds, erases, waits its turn."""
    n = len(text)
    wtot = n * CHAR_W
    x0 = CX - wtot / 2
    period, start = SLOT * n_lines, i * SLOT
    t_hold = start + n * TYPE_DT + HOLD
    t_end = t_hold + n * ERASE_DT

    ev = [(0.0, 0.0)] + [(start + k * TYPE_DT, k * CHAR_W) for k in range(1, n + 1)]
    ev += [(t_hold + j * ERASE_DT, (n - j) * CHAR_W) for j in range(1, n + 1)]
    kt = ";".join(f"{t / period:.5f}" for t, _ in ev)
    widths = ";".join(f"{w:.1f}" for _, w in ev)
    xs = ";".join(f"{x0 + w:.1f}" for _, w in ev)

    if start > 0:
        ck, cv = f"0;{start / period:.5f};{t_end / period:.5f}", "0;1;0"
    else:
        ck, cv = f"0;{t_end / period:.5f}", "1;0"
    first = f"{wtot:.1f}" if FLASH and i == 0 else "0"
    dur = f'dur="{period}s" repeatCount="indefinite" calcMode="discrete"'

    clip = (f'<clipPath id="tc{i}"><rect x="{x0 - 2:.1f}" y="{TYPE_Y - 20}" height="30" width="{first}">'
            f'<animate attributeName="width" {dur} keyTimes="{kt}" values="{widths}"/></rect></clipPath>')
    label = (f'<text class="mono" x="{x0:.1f}" y="{TYPE_Y}" font-size="{TYPE_SIZE}" fill="{STREAK}" '
             f'textLength="{wtot:.1f}" lengthAdjust="spacing" clip-path="url(#tc{i})">'
             f'{html.escape(text)}</text>')
    caret = (f'<rect y="{TYPE_Y - 17}" width="2" height="22" rx="1" fill="{STREAK}" '
             f'opacity="0" x="{x0:.1f}">'
             f'<animate attributeName="x" {dur} keyTimes="{kt}" values="{xs}"/>'
             f'<animate attributeName="opacity" {dur} keyTimes="{ck}" values="{cv}"/></rect>')
    return clip, label, caret


def build():
    css = CSS.replace("@RUN@", str(W - 130))
    if FLASH:
        css += ".bolt{opacity:1!important;animation:none!important}" \
               ".spark{opacity:var(--pk)!important;animation:none!important}"
    x_title = CX - TITLE_W / 2

    defs = [
        f'<radialGradient id="sky" gradientUnits="userSpaceOnUse" cx="{CX}" cy="70" r="430">'
        f'<stop offset="0" stop-color="#12285A"/><stop offset=".55" stop-color="#0A1633"/>'
        f'<stop offset="1" stop-color="{BG}"/></radialGradient>',
        f'<linearGradient id="tg" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="#7DE3FF"/><stop offset=".5" stop-color="#EAF8FF"/>'
        f'<stop offset="1" stop-color="#3C9BFF"/></linearGradient>',
        f'<linearGradient id="ig" x1="0" x2="0" y1="0" y2="1">'
        f'<stop offset="0" stop-color="#D8F3FF"/><stop offset="1" stop-color="#2D7BFF"/></linearGradient>',
        f'<radialGradient id="halo"><stop offset="0" stop-color="#D8F3FF" stop-opacity=".9"/>'
        f'<stop offset=".45" stop-color="{GLOW}" stop-opacity=".35"/>'
        f'<stop offset="1" stop-color="{GLOW}" stop-opacity="0"/></radialGradient>',
        f'<linearGradient id="hz" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="#24407A" stop-opacity="0"/><stop offset=".5" stop-color="#24407A"/>'
        f'<stop offset="1" stop-color="#24407A" stop-opacity="0"/></linearGradient>',
        f'<linearGradient id="pg" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{STREAK}" stop-opacity="0"/><stop offset=".5" stop-color="{STREAK}"/>'
        f'<stop offset="1" stop-color="{STREAK}" stop-opacity="0"/></linearGradient>',
        '<pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">'
        '<circle cx="1.5" cy="1.5" r="1" fill="#14336B"/></pattern>',
        f'<filter id="glow" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<feGaussianBlur stdDeviation="2.2"/></filter>',
        f'<filter id="blur" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
        f'<feGaussianBlur stdDeviation="7"/></filter>',
    ]

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
         f'role="img" aria-label="{html.escape(NAME.title())} — {html.escape(SUBTITLE)}">',
         f"<style>{css}</style>", "<defs>" + "".join(defs), "</defs>",
         f'<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>',
         f'<rect width="{W}" height="{H}" rx="12" fill="url(#sky)"/>',
         f'<rect width="{W}" height="{H}" rx="12" fill="url(#dots)" opacity=".5"/>',
         f'<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="#1B2B52"/>']

    # glowing title (blurred twin behind the crisp text) + bolt icons
    title = (f'x="{x_title:.1f}" y="{TITLE_Y}" font-size="{TITLE_SIZE}" font-weight="800" '
             f'textLength="{TITLE_W}" lengthAdjust="spacing"')
    o.append(f'<text class="hum" {title} fill="{GLOW}" filter="url(#blur)">{NAME}</text>')
    o.append(f'<text {title} fill="url(#tg)">{NAME}</text>')
    icon = "13,0 1,18 9.5,18 6,32 23,10.5 14.5,10.5 19,0"
    for ix in (x_title - 44, x_title + TITLE_W + 18):
        g = f'transform="translate({ix:.1f},{TITLE_Y - 40})"'
        o.append(f'<polygon class="hum" {g} points="{icon}" fill="{GLOW}" filter="url(#blur)"/>')
        o.append(f'<polygon {g} points="{icon}" fill="url(#ig)"/>')

    o.append(f'<text x="{CX}" y="{SUB_Y}" font-size="12.5" letter-spacing="3" fill="#8FB2FF" '
             f'text-anchor="middle">{html.escape(SUBTITLE)}</text>')

    # typing lines
    clips, labels, carets = [], [], []
    for i, text in enumerate(LINES):
        c, t, k = typing(i, text, len(LINES))
        clips.append(c), labels.append(t), carets.append(k)
    o[o.index("</defs>")] = "".join(clips) + "</defs>"
    o += labels + carets

    # lightning striking the name
    for i, (tx, ty) in enumerate(TARGETS):
        t, off = TIMINGS[i % len(TIMINGS)]
        var = f"--t:{t}s;--o:{off}s"
        rnd = random.Random(f"header-{i}")
        sx, sy = tx + rnd.uniform(-70, 70), -4
        main = jagged(rnd, sx, sy, tx, ty, 14, 5)
        bx, by = main[rnd.randint(len(main) // 3, 2 * len(main) // 3)]
        branch = jagged(rnd, bx, by, min(max(bx + rnd.uniform(-60, 60), 20), W - 20),
                        min(by + rnd.uniform(14, 28), 100), 6, 3)
        o.append(
            f'<g class="bolt b{i}" style="{var};--pk:1">'
            f'<rect width="{W}" height="{H}" rx="12" fill="{SPARK}" opacity=".05"/>'
            f'<circle cx="{tx:.1f}" cy="{ty}" r="26" fill="url(#halo)"/>'
            f'<polyline points="{fmt(main)}" fill="none" stroke="{GLOW}" stroke-width="5" '
            f'stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>'
            f'<polyline points="{fmt(branch)}" fill="none" stroke="{GLOW}" stroke-width="3" '
            f'filter="url(#glow)"/>'
            f'<polyline points="{fmt(branch)}" fill="none" stroke="{BOLT}" stroke-width=".9" opacity=".8"/>'
            f'<polyline points="{fmt(main)}" fill="none" stroke="{BOLT}" stroke-width="1.6" '
            f'stroke-linejoin="round" stroke-linecap="round"/></g>')

    # energy line with a travelling pulse
    o.append(f'<line x1="40" y1="194" x2="{W - 40}" y2="194" stroke="url(#hz)" stroke-width="1"/>')
    o.append(f'<rect class="run" x="0" y="193" width="100" height="2" fill="url(#pg)"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build())
    print(f"Wrote {OUT}")
