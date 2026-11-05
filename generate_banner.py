#!/usr/bin/env python3
"""
Generate an animated ASCII-art name banner (SVG) for a GitHub profile README.

GitHub README-te JavaScript chole na, kintu SVG-er bhitorer CSS animation chole.
Tai ei script ekta self-contained animated SVG banai:
  1. Terminal boot:  `$ ./whoami` type hoy
  2. Decrypt effect: random ASCII glyph theke dhire dhire tomar naam reveal hoy
  3. Glow + subtitle typing + blinking cursor
  4. Loop kore abar shuru hoy

Naam / subtitle bodlate niche CONFIG edit kore abar run koro:
    python3 generate_banner.py
"""
import random
from xml.sax.saxutils import escape

# ───────────────────────── CONFIG ─────────────────────────
NAME = "SANZID AHMED"
SUBTITLE = "Developer  ·  Problem Solver  ·  Lifelong Learner"
PROMPT_CMD = "./whoami --banner"
OUTPUT = "assets/ascii-name.svg"
CYCLE = 12.0          # seconds per full loop
SCRAMBLE_FRAMES = 22  # frames in the decrypt phase
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

    t_type_end = 0.25 + len(PROMPT_CMD) * 0.045
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
    css.append(f"@keyframes fin{{0%,{pct(t_final)}{{opacity:0}}{pct(t_final)},{pct(t_out)}{{opacity:1}}100%{{opacity:0}}}}"
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
    css.append(f"@keyframes typ{{0%,{pct(0.25)}{{width:0}}{pct(t_type_end)},{pct(t_out)}{{width:{prompt_w:.0f}px}}100%{{width:0}}}}"
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
  <clipPath id="cs"><rect class="sub" x="{PAD_X:.1f}" y="{sub_y - 16}" height="24" width="0"/></clipPath>
</defs>
<style>{style}</style>
<rect width="100%" height="100%" rx="12" fill="#0d1117"/>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="12" fill="none" stroke="#30363d"/>
<circle cx="20" cy="16" r="5" fill="#ff5f56"/><circle cx="37" cy="16" r="5" fill="#ffbd2e"/><circle cx="54" cy="16" r="5" fill="#27c93f"/>
<text class="ui" x="{width / 2:.0f}" y="20" fill="#6e7681" text-anchor="middle">sanzid@github: ~</text>
<text class="ui" x="{PAD_X}" y="44" fill="#00f5a0">$</text>
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
