#!/usr/bin/env python3
"""
Generate an animated ASCII-art name banner (SVG) for a GitHub profile README.

GitHub README-te JavaScript chole na, kintu SVG-er bhitorer CSS animation chole.
Tai ei script ekta self-contained animated SVG banai:
  0. Space intro:   galaxy + black hole, camera zooms into the black hole
  1. Terminal boot:  `$ ./whoami` type hoy
  2. Decrypt effect: random ASCII glyph theke dhire dhire tomar naam reveal hoy
  3. Glow + subtitle typing + blinking cursor
  4. Loop kore abar shuru hoy

Naam / subtitle bodlate niche CONFIG edit kore abar run koro:
    python3 generate_banner.py
"""
import math
import random
from xml.sax.saxutils import escape

# ───────────────────────── CONFIG ─────────────────────────
NAME = "SANZID AHMED"
SUBTITLE = "Developer  ·  Problem Solver  ·  Lifelong Learner"
PROMPT_CMD = "./whoami --banner"
OUTPUT = "assets/ascii-name.svg"
CYCLE = 8.5           # seconds per full loop
INTRO = 2.4           # seconds of galaxy / black-hole zoom before the name
SCRAMBLE_FRAMES = 18  # frames in the decrypt phase
FRAME_TIME = 0.085    # seconds per scramble frame
SEED = 7
# ──────────────────────────────────────────────────────────

FONT = {  # ANSI Shadow style, 6 rows high
    "A": [" █████╗ ", "██╔══██╗", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "D": ["██████╗ ", "██╔══██╗", "██║  ██║", "██║  ██║", "██████╔╝", "╚═════╝ "],
    "E": ["███████╗", "██╔════╝", "█████╗  ", "██╔══╝  ", "███████╗", "╚══════╝"],
    "H": ["██╗  ██╗", "██║  ██║", "███████║", "██╔══██║", "██║  ██║", "╚═╝  ╚═╝"],
    "I": ["██╗", "██║", "██║", "██║", "██║", "╚═╝"],
    "M": ["███╗   ███╗", "████╗ ████║", "██╔████╔██║", "██║╚██╔╝██║", "██║ ╚═╝ ██║", "╚═╝     ╚═╝"],
    "N": ["███╗   ██╗", "████╗  ██║", "██╔██╗ ██║", "██║╚██╗██║", "██║ ╚████║", "╚═╝  ╚═══╝"],
    "S": ["███████╗", "██╔════╝", "███████╗", "╚════██║", "███████║", "╚══════╝"],
    "Z": ["███████╗", "╚══███╔╝", "  ███╔╝ ", " ███╔╝  ", "███████╗", "╚══════╝"],
    " ": ["   "] * 6,
}
GLYPHS = "!@#$%&*+=?/\\|<>{}[]~^;:01"

CW, LH = 9.6, 17.0          # char width, line height (px) for font-size 16
PAD_X, TOP = 34, 70         # left padding, y of first art row


def render(name):
    rows = [""] * 6
    for ch in name.upper():
        glyph = FONT.get(ch)
        if glyph is None:
            raise SystemExit(f"Letter '{ch}' FONT-e nei — FONT dict-e add koro.")
        for i in range(6):
            rows[i] += glyph[i]
    return rows


def text_row(chars, y, cls):
    """chars: list of (col, char). Each glyph gets an explicit x so the art never
    drifts, whatever monospace font the viewer's browser picks."""
    if not chars:
        return ""
    xs = " ".join(f"{PAD_X + c * CW:.1f}" for c, _ in chars)
    s = escape("".join(ch for _, ch in chars))
    return f'<text class="{cls}" x="{xs}" y="{y:.1f}">{s}</text>'


def pct(t):
    return f"{max(0.0, min(100.0, t / CYCLE * 100)):.3f}%"


def space_layer(width, height, rnd):
    """Starfield + tilted spiral galaxy + black hole with accretion disk; zooms into the hole."""
    cx, cy, R = width / 2, height / 2 + 8, 28
    css = [
        # camera: drift in, then accelerate into the event horizon
        f"@keyframes bhz{{0%{{transform:scale(1);animation-timing-function:ease-out}}"
        f"{pct(1.2)}{{transform:scale(1.3);animation-timing-function:cubic-bezier(.6,0,.95,.35)}}"
        f"{pct(INTRO - 0.1)},100%{{transform:scale(36)}}}}"
        f".bhz{{transform-origin:{cx:.1f}px {cy:.1f}px;animation:bhz {CYCLE}s infinite}}",
        f"@keyframes bhv{{0%{{opacity:0}}{pct(0.35)},{pct(INTRO - 0.15)}{{opacity:1}}{pct(INTRO + 0.1)},100%{{opacity:0}}}}"
        f".bhv{{animation:bhv {CYCLE}s linear infinite}}",
        f"@keyframes gal{{0%{{transform:rotate(0deg)}}{pct(INTRO)},100%{{transform:rotate(-45deg)}}}}"
        f".gal{{transform-origin:0 0;animation:gal {CYCLE}s linear infinite}}",
        "@keyframes tw{0%,100%{opacity:1}50%{opacity:.15}}"
        ".tw0{animation:tw 1.7s infinite}.tw1{animation:tw 2.4s .5s infinite}.tw2{animation:tw 3.2s 1.1s infinite}",
        "@keyframes spin{to{stroke-dashoffset:-200}}",
    ]
    stars = "".join(
        f'<circle class="tw{i % 3}" cx="{rnd.uniform(0, width):.1f}" cy="{rnd.uniform(0, height):.1f}" '
        f'r="{rnd.choice([0.5, 0.7, 0.9, 1.2])}" fill="#fff"/>' for i in range(170))

    palette = ["#ffffff", "#7ee7ff", "#00d9f5", "#00f5a0", "#a855f7", "#c084fc"]
    dots = []
    for i in range(820):
        k, t = i % 2, rnd.random() ** 0.85
        ang = k * math.pi + t * 3.4 * math.pi + rnd.gauss(0, 0.28)
        rad = 50 + t * 440 + rnd.gauss(0, 12)
        col = palette[max(0, min(len(palette) - 1, int(t * len(palette) + rnd.uniform(-1, 1))))]
        dots.append(f'<circle cx="{rad * math.cos(ang):.1f}" cy="{rad * math.sin(ang):.1f}" '
                    f'r="{rnd.uniform(0.5, 1.5) * (1.25 - 0.5 * t):.2f}" fill="{col}" '
                    f'opacity="{(1 - 0.45 * t) * rnd.uniform(0.45, 1.0):.2f}"/>')
    galaxy = (f'<g transform="translate({cx:.1f} {cy:.1f}) scale(1 0.34) rotate(-14)">'
              f'<ellipse rx="330" ry="150" fill="url(#galglow)"/><g class="gal">{"".join(dots)}</g></g>')

    dashes = ["34 2 2 2", "18 2 18 2", "36 4", "26 2 10 2", "30 3 4 3", "20 2 16 2", "36 2 1 1", "12 2 24 2", "28 4 6 2"]
    rings = []
    for j, rx in enumerate([40, 46, 53, 61, 70, 80, 92, 105, 120]):
        dur = 0.8 + j * 0.35
        css.append(f".s{j}{{animation:spin {dur:.2f}s linear infinite}}")
        rings.append(f'<ellipse class="s{j}" cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx}" ry="{rx * 0.2:.1f}" fill="none" '
                     f'stroke="url(#disk)" stroke-width="{rx / 13:.1f}" stroke-dasharray="{dashes[j]}" '
                     f'opacity="{1 - j * 0.09:.2f}"/>')
    disk = "".join(rings)
    hole = (f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="150" fill="url(#halo)"/>'
            f'<g filter="url(#soft)">{disk}</g>'
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{R + 13}" ry="{R + 11}" fill="none" stroke="url(#disk)" '
            f'stroke-width="8" opacity=".6" filter="url(#wide)"/>'
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{R + 6}" ry="{R + 5}" fill="none" stroke="#bff6ff" '
            f'stroke-width="2.5" opacity=".7" filter="url(#soft)"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R}" fill="#020305"/>'
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R + 1.2}" fill="none" stroke="#effcff" stroke-width="1.2" opacity=".9"/>'
            f'<g clip-path="url(#front)" filter="url(#soft)">{disk}</g>')
    defs = (
        f'<clipPath id="win"><rect width="{width}" height="{height}" rx="12"/></clipPath>\n'
        f'  <clipPath id="front"><rect x="0" y="{cy:.1f}" width="{width}" height="{height}"/></clipPath>\n'
        '  <radialGradient id="halo"><stop offset="0" stop-color="#bff6ff" stop-opacity=".55"/>'
        '<stop offset=".35" stop-color="#00d9f5" stop-opacity=".18"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/></radialGradient>\n'
        '  <radialGradient id="galglow"><stop offset="0" stop-color="#7ee7ff" stop-opacity=".3"/>'
        '<stop offset=".5" stop-color="#a855f7" stop-opacity=".08"/><stop offset="1" stop-color="#a855f7" stop-opacity="0"/></radialGradient>\n'
        '  <linearGradient id="disk" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ffffff"/>'
        '<stop offset=".3" stop-color="#7ee7ff"/><stop offset=".65" stop-color="#00f5a0"/><stop offset="1" stop-color="#a855f7"/></linearGradient>\n'
        '  <filter id="soft" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="1.6" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>\n'
        '  <filter id="wide" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="4"/></filter>')
    svg = f'<g clip-path="url(#win)"><g class="bhv"><g class="bhz">{stars}{galaxy}{hole}</g></g></g>'
    return css, defs, svg


def main():
    rnd = random.Random(SEED)
    art = render(NAME)
    cols = max(len(r) for r in art)
    width = int(PAD_X * 2 + cols * CW)
    height = 250
    cells = [(r, c) for r in range(6) for c, ch in enumerate(art[r]) if ch != " "]

    # Each cell "locks" to its real character at a random frame, sweeping roughly left→right.
    lock = {}
    for r, c in cells:
        base = c / cols * (SCRAMBLE_FRAMES - 4)
        lock[(r, c)] = int(min(SCRAMBLE_FRAMES - 1, max(1, base + rnd.uniform(0, 4))))

    t_type_end = INTRO + 0.25 + len(PROMPT_CMD) * 0.04
    t_scr = t_type_end + 0.25
    t_final = t_scr + SCRAMBLE_FRAMES * FRAME_TIME
    t_sub = t_final + 0.5
    t_sub_end = t_sub + len(SUBTITLE) * 0.03
    t_out = CYCLE - 0.6

    css, body = [], []

    # ── scramble frames ──
    for f in range(SCRAMBLE_FRAMES):
        a, b = t_scr + f * FRAME_TIME, t_scr + (f + 1) * FRAME_TIME
        css.append(f"@keyframes f{f}{{0%,{pct(a)}{{opacity:0}}{pct(a)},{pct(b)}{{opacity:1}}"
                   f"{pct(b)},100%{{opacity:0}}}}.f{f}{{animation:f{f} {CYCLE}s step-end infinite}}")
        g = []
        for r in range(6):
            y = TOP + r * LH
            locked, noise = [], []
            for c, ch in enumerate(art[r]):
                if ch == " ":
                    # sparse noise in the gaps for a "matrix" feel early on
                    if f < SCRAMBLE_FRAMES // 2 and rnd.random() < 0.08:
                        noise.append((c, rnd.choice(GLYPHS)))
                    continue
                if f >= lock[(r, c)]:
                    locked.append((c, ch))
                else:
                    noise.append((c, rnd.choice(GLYPHS)))
            g.append(text_row(locked, y, "art"))
            g.append(text_row(noise, y, "noise"))
        body.append(f'<g class="f{f}" opacity="0">{"".join(g)}</g>')

    # ── final name ──
    css.append(f"@keyframes fin{{0%,{pct(t_final - 0.02)}{{opacity:0}}{pct(t_final)},{pct(t_out)}{{opacity:1}}100%{{opacity:0}}}}"
               f".fin{{animation:fin {CYCLE}s linear infinite}}")
    final = "".join(text_row([(c, ch) for c, ch in enumerate(art[r]) if ch != " "], TOP + r * LH, "art")
                    for r in range(6))
    body.append(f'<g class="fin" opacity="0"><g filter="url(#glow)">{final}</g>'
                f'<rect class="scan" x="0" y="{TOP - 14}" width="{width}" height="3" fill="#7ee7ff" opacity=".35"/></g>')
    css.append(f"@keyframes scan{{0%,{pct(t_final)}{{transform:translateY(0);opacity:0}}"
               f"{pct(t_final + 0.05)}{{opacity:.5}}{pct(t_final + 0.9)}{{transform:translateY({6 * LH}px);opacity:0}}100%{{opacity:0}}}}"
               f".scan{{animation:scan {CYCLE}s linear infinite}}")

    # ── prompt line typing (clip-path reveal) ──
    prompt_w = (len(PROMPT_CMD) + 2) * CW * 14 / 16
    css.append(f"@keyframes typ{{0%,{pct(INTRO + 0.25)}{{width:0}}{pct(t_type_end)},{pct(t_out)}{{width:{prompt_w:.0f}px}}100%{{width:0}}}}"
               f".typ{{animation:typ {CYCLE}s steps({len(PROMPT_CMD)}) infinite}}")
    # ── subtitle typing ──
    sub_y = TOP + 6 * LH + 40
    sub_w = len(SUBTITLE) * CW * 14 / 16
    css.append(f"@keyframes sub{{0%,{pct(t_sub)}{{width:0}}{pct(t_sub_end)},{pct(t_out)}{{width:{sub_w:.0f}px}}100%{{width:0}}}}"
               f".sub{{animation:sub {CYCLE}s steps({len(SUBTITLE)}) infinite}}")
    # ── cursor follows the typing ──
    css.append(f"@keyframes cur{{0%,{pct(t_sub)}{{transform:translate(0,0)}}{pct(t_sub_end)},100%{{transform:translate({sub_w + 4:.0f}px,0)}}}}"
               f"@keyframes blink{{0%,50%{{opacity:1}}50.01%,100%{{opacity:0}}}}"
               f".cur{{animation:cur {CYCLE}s steps({len(SUBTITLE)}) infinite}}.cur rect{{animation:blink 1s infinite}}")
    css.append(f"@keyframes subv{{0%,{pct(t_sub - 0.01)}{{opacity:0}}{pct(t_sub)},{pct(t_out)}{{opacity:1}}100%{{opacity:0}}}}"
               f".subv{{animation:subv {CYCLE}s step-end infinite}}")

    css.append(f"@keyframes term{{0%,{pct(INTRO)}{{opacity:0}}{pct(INTRO + 0.01)},{pct(t_out)}{{opacity:1}}100%{{opacity:0}}}}"
               f".term{{animation:term {CYCLE}s step-end infinite}}")
    sp_css, sp_defs, sp_svg = space_layer(width, height, rnd)
    css.extend(sp_css)

    style = """
    .art{font:16px 'Fira Code','JetBrains Mono','Cascadia Code',Consolas,Menlo,'DejaVu Sans Mono',monospace;fill:url(#grad);white-space:pre}
    .noise{font:16px Consolas,Menlo,'DejaVu Sans Mono',monospace;fill:#2ea043;opacity:.75}
    .ui{font:14px Consolas,Menlo,'DejaVu Sans Mono',monospace;white-space:pre}
    """ + "\n".join(css)

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(NAME.title())} — {escape(SUBTITLE)}">
<title>{escape(NAME.title())}</title>
<defs>
  <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#00f5a0"/><stop offset=".5" stop-color="#00d9f5"/><stop offset="1" stop-color="#a855f7"/>
  </linearGradient>
  <filter id="glow" x="-5%" y="-20%" width="110%" height="140%">
    <feGaussianBlur stdDeviation="2.2" result="b"/>
    <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="cp"><rect class="typ" x="{PAD_X + 2 * CW:.1f}" y="28" height="22" width="0"/></clipPath>
  {sp_defs}
  <clipPath id="cs"><rect class="sub" x="{PAD_X:.1f}" y="{sub_y - 16}" height="24" width="0"/></clipPath>
</defs>
<style>{style}</style>
<rect width="100%" height="100%" rx="12" fill="#0d1117"/>
{sp_svg}
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="none" stroke="#30363d"/>
<circle cx="20" cy="16" r="5" fill="#ff5f56"/><circle cx="37" cy="16" r="5" fill="#ffbd2e"/><circle cx="54" cy="16" r="5" fill="#27c93f"/>
<text class="ui" x="{width / 2:.0f}" y="20" fill="#6e7681" text-anchor="middle">sanzid@github: ~</text>
<text class="ui term" x="{PAD_X}" y="44" fill="#00f5a0">$</text>
<text class="ui" x="{PAD_X + 2 * CW:.1f}" y="44" fill="#c9d1d9" clip-path="url(#cp)">{escape(PROMPT_CMD)}</text>
{"".join(body)}
<g class="subv" opacity="0">
  <text class="ui" x="{PAD_X}" y="{sub_y}" fill="#8b949e" clip-path="url(#cs)">{escape(SUBTITLE)}</text>
  <g class="cur"><rect x="{PAD_X}" y="{sub_y - 13}" width="8" height="16" fill="#00d9f5"/></g>
</g>
</svg>
'''
    import os
    os.makedirs(os.path.dirname(OUTPUT) or ".", exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUTPUT}  ({len(svg) / 1024:.1f} KB, {width}x{height})")


if __name__ == "__main__":
    main()
