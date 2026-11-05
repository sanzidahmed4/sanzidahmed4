#!/usr/bin/env python3
"""
Generates every custom SVG card used in the profile README (standard library only,
so it also runs inside GitHub Actions):

  assets/divider-*.svg      section headers
  assets/mission.svg        "Mission Log" about-me terminal
  assets/skills.svg         skill constellation
  assets/project-*.svg      planet project cards
  assets/commit-galaxy.svg  last year's contributions drawn as a spiral galaxy (live data)
  assets/journey.svg        timeline along an orbit
  assets/transmission.svg   contact header

    python3 generate_sections.py            # everything
    python3 generate_sections.py --galaxy   # only refresh the commit galaxy (used by the daily Action)

Edit the CONFIG block to change any text.
"""
import datetime as dt
import math
import os
import random
import re
import sys
import urllib.request
from xml.sax.saxutils import escape as esc

# ═════════════════════════════════ CONFIG ═════════════════════════════════
USER = "sanzidahmed4"
MISSION = [  # (key, value) lines typed in the Mission Log
    ("name", "Sanzid Ahmed"),
    ("role", "Frontend Web Developer"),
    ("base", "Bogura, Bangladesh"),
    ("building", "responsive websites & small web apps"),
    ("learning", "deeper JavaScript  →  React"),
    ("motto", '"Hope for the best, prepare for the worst."'),
]
SKILLS = {  # cluster -> stars (name, brightness 1..3)
    "FRONTEND": [("HTML5", 3), ("CSS3", 3), ("JavaScript", 3), ("Responsive UI", 2)],
    "SCRIPTING": [("Python", 2)],
    "TOOLS": [("Git", 2), ("GitHub", 3), ("VS Code", 2), ("GitHub Pages", 1)],
    "NEXT ORBIT": [("React", 0), ("Tailwind CSS", 0)],          # 0 = still learning (dim, dashed)
}
PROJECTS = [  # slug, title, language, stars, description, link label
    ("ClickCounter", "ClickCounter", "JavaScript", 1,
     "A modern click counter web app built with JavaScript, HTML & CSS.", "live demo ↗"),
    ("portfolio", "Portfolio", "CSS", 0,
     "My personal portfolio site: the home base for everything I build.", "view repo ↗"),
    ("catering-service", "Catering Service", "HTML", 0,
     "Front end for a food delivery & catering business website.", "view repo ↗"),
]
JOURNEY = [  # (date label, title, detail, reached?)
    ("JUL 2024", "Launch", "joined GitHub, first site", True),
    ("AUG 2024", "Warm-up", "restaurant & food sites", True),
    ("NOV 2024", "Hyperdrive", "4 front ends in a month", True),
    ("MAY 2025", "Home base", "built my portfolio", True),
    ("NOV 2025", "First app live", "ClickCounter on Pages", True),
    ("NOV 2026", "Deep space", "this profile ✦", True),
    ("NEXT", "React orbit", "bigger builds ahead", False),
]
TRANSMISSION = ("TRANSMISSION OPEN", "Got an idea, a project, or just want to say hi?", "Pick a channel below ↓")
# ══════════════════════════════════════════════════════════════════════════

BG, CARD, BORDER = "#0d1117", "#0b1016", "#30363d"
G, C, P = "#00f5a0", "#00d9f5", "#a855f7"
TEXT, MUTED, DIM = "#e6edf3", "#8b949e", "#484f58"
FONT = "ui-monospace,SFMono-Regular,'JetBrains Mono','Fira Code',Menlo,Consolas,'DejaVu Sans Mono',monospace"
LANG_COLOR = {"JavaScript": "#f1e05a", "CSS": "#8a5bd6", "HTML": "#e34c26", "Python": "#3572A5"}
REDUCED = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"
OUT = "assets"


def grad_defs(gid="grad"):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{G}"/>'
            f'<stop offset=".5" stop-color="{C}"/><stop offset="1" stop-color="{P}"/></linearGradient>')


def starfield(w, h, n, seed, op=(0.15, 0.55)):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        out.append(f'<circle class="tw{i % 3}" cx="{rnd.uniform(0, w):.1f}" cy="{rnd.uniform(0, h):.1f}" '
                   f'r="{rnd.choice([0.5, 0.6, 0.8, 1.0])}" fill="#fff" opacity="{rnd.uniform(*op):.2f}"/>')
    return "".join(out)


TWINKLE = ("@keyframes tw{0%,100%{opacity:.7}50%{opacity:.1}}"
           ".tw0{animation:tw 2.2s infinite}.tw1{animation:tw 3.1s .7s infinite}.tw2{animation:tw 4s 1.4s infinite}")


def card(w, h, body, css="", title="", seed=1, stars=60, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>'
            f'<defs>{grad_defs()}<clipPath id="frame"><rect width="{w}" height="{h}" rx="12"/></clipPath>{defs}</defs>'
            f'<style>text{{font-family:{FONT}}}{TWINKLE}{css}{REDUCED}</style>'
            f'<g clip-path="url(#frame)"><rect width="{w}" height="{h}" fill="{CARD}"/>{starfield(w, h, stars, seed)}{body}</g>'
            f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="12" fill="none" stroke="{BORDER}"/></svg>\n')


def write(name, svg):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT}/{name:24s} {len(svg) / 1024:6.1f} KB")


# ───────────────────────────── section divider ─────────────────────────────
def divider(num, title):
    w, h = 900, 46
    label = f"{num} ── {title}"
    tw = len(label) * 18 * 0.6 + 18
    css = (f"@keyframes run{{0%{{transform:translateX(0);opacity:0}}10%{{opacity:1}}90%{{opacity:1}}"
           f"100%{{transform:translateX({w - tw - 30:.0f}px);opacity:0}}}}.dot{{animation:run 4.5s cubic-bezier(.5,0,.5,1) infinite}}"
           "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}.dia{animation:pulse 2s infinite}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{esc(title.title())}"><title>{esc(title.title())}</title>'
            f'<defs>{grad_defs()}<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{C}" stop-opacity=".8"/>'
            f'<stop offset="1" stop-color="{P}" stop-opacity="0"/></linearGradient>'
            f'<filter id="gl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5"/></filter></defs>'
            f'<style>text{{font-family:{FONT}}}{css}{REDUCED}</style>'
            f'<rect class="dia" x="4" y="17" width="12" height="12" transform="rotate(45 10 23)" fill="url(#grad)"/>'
            f'<text x="26" y="30" font-size="18" font-weight="700" fill="url(#grad)" letter-spacing="1">{esc(label)}</text>'
            f'<line x1="{tw + 14:.0f}" y1="23" x2="{w}" y2="23" stroke="url(#fade)" stroke-width="1.5"/>'
            f'<g class="dot"><circle cx="{tw + 14:.0f}" cy="23" r="5" fill="{C}" filter="url(#gl)"/>'
            f'<circle cx="{tw + 14:.0f}" cy="23" r="2" fill="#fff"/></g></svg>\n')


# ───────────────────────────── mission log ─────────────────────────────
def mission():
    w, h = 900, 300
    css, body = [], []
    body.append(f'<circle cx="22" cy="20" r="5" fill="#ff5f56"/><circle cx="39" cy="20" r="5" fill="#ffbd2e"/>'
                f'<circle cx="56" cy="20" r="5" fill="#27c93f"/>'
                f'<text x="{w / 2}" y="24" font-size="13" fill="{MUTED}" text-anchor="middle">~/sanzid/mission.log</text>'
                f'<line x1="0" y1="38" x2="{w}" y2="38" stroke="{BORDER}"/>')
    y0, lh, x0 = 72, 29, 34
    body.append(f'<text x="{x0}" y="{y0}" font-size="15"><tspan fill="{G}">$</tspan>'
                f'<tspan fill="{TEXT}"> cat mission.log</tspan></text>')
    clips = []
    for i, (k, v) in enumerate(MISSION):
        y = y0 + (i + 1) * lh
        n = len(k) + len(v) + 14
        full = n * 15 * 0.6 + 10
        delay, dur = 0.5 + i * 0.55, 0.45
        clips.append(f'<clipPath id="l{i}"><rect class="ty{i}" x="{x0}" y="{y - 18}" height="26" width="{full:.0f}"/></clipPath>')
        css.append(f"@keyframes ty{i}{{from{{width:0}}to{{width:{full:.0f}px}}}}"
                   f".ty{i}{{animation:ty{i} {dur}s steps({n}) {delay:.2f}s both}}")
        vcol = P if k == "motto" else TEXT
        style = ' font-style="italic"' if k == "motto" else ""
        body.append(f'<text x="{x0}" y="{y}" font-size="15" clip-path="url(#l{i})">'
                    f'<tspan fill="{DIM}">&gt; </tspan><tspan fill="{C}">{esc(k.ljust(9))}</tspan>'
                    f'<tspan fill="{DIM}">: </tspan><tspan fill="{vcol}"{style}>{esc(v)}</tspan></text>')
    yc = y0 + (len(MISSION) + 1) * lh
    css.append("@keyframes bl{0%,50%{opacity:1}50.01%,100%{opacity:0}}.cur{animation:bl 1s step-end infinite}")
    body.append(f'<text x="{x0}" y="{yc}" font-size="15" fill="{G}">$</text>'
                f'<rect class="cur" x="{x0 + 18}" y="{yc - 13}" width="9" height="17" fill="{C}"/>')
    # orbiting planet on the right
    px, py = 760, 165
    css.append("@keyframes orb{to{transform:rotate(360deg)}}"
               f".orb{{transform-origin:{px}px {py}px;animation:orb 9s linear infinite}}"
               "@keyframes band{from{transform:translateX(0)}to{transform:translateX(-60px)}}.band{animation:band 6s linear infinite}")
    defs = (f'<radialGradient id="pl" cx=".35" cy=".35" r=".75"><stop offset="0" stop-color="#7ee7ff"/>'
            f'<stop offset=".55" stop-color="#1b6f8f"/><stop offset="1" stop-color="#081a26"/></radialGradient>'
            f'<radialGradient id="atm"><stop offset=".72" stop-color="{C}" stop-opacity="0"/>'
            f'<stop offset=".82" stop-color="{C}" stop-opacity=".35"/><stop offset="1" stop-color="{C}" stop-opacity="0"/></radialGradient>'
            f'<clipPath id="pc"><circle cx="{px}" cy="{py}" r="46"/></clipPath>' + "".join(clips))
    bands = "".join(f'<rect x="{px - 46 + j * 30}" y="{py - 46 + (j * 23) % 80}" width="70" height="7" rx="3.5" fill="#bff6ff" opacity=".18"/>'
                    for j in range(8))
    body.append(f'<circle cx="{px}" cy="{py}" r="62" fill="url(#atm)"/>'
                f'<ellipse cx="{px}" cy="{py}" rx="92" ry="20" fill="none" stroke="{P}" stroke-opacity=".35" stroke-width="1.2" transform="rotate(-18 {px} {py})"/>'
                f'<circle cx="{px}" cy="{py}" r="46" fill="url(#pl)"/>'
                f'<g clip-path="url(#pc)"><g class="band">{bands}</g></g>'
                f'<path d="M{px - 92} {py} A92 20 0 0 0 {px + 92} {py}" fill="none" stroke="{P}" stroke-width="2.2" '
                f'stroke-opacity=".75" transform="rotate(-18 {px} {py})"/>'
                f'<g class="orb"><circle cx="{px + 78}" cy="{py - 30}" r="5" fill="{G}"/>'
                f'<circle cx="{px + 78}" cy="{py - 30}" r="10" fill="{G}" opacity=".15"/></g>')
    return card(w, h, "".join(body), "".join(css), "Mission log: about Sanzid Ahmed", seed=11, defs=defs)


# ───────────────────────────── skill constellation ─────────────────────────────
def skills():
    w, h = 900, 300
    rnd = random.Random(5)
    cols = {"FRONTEND": G, "SCRIPTING": C, "TOOLS": "#7ee7ff", "NEXT ORBIT": P}
    layouts = {  # cluster centre + star offsets (hand-placed constellation shapes)
        "FRONTEND": ((150, 165), [(-80, -40), (-5, -75), (70, -25), (25, 55)]),
        "SCRIPTING": ((360, 120), [(0, 0)]),
        "TOOLS": ((560, 170), [(-70, -45), (5, -80), (75, -30), (10, 50)]),
        "NEXT ORBIT": ((790, 150), [(-20, -55), (25, 45)]),
    }
    css = [("@keyframes glow{0%,100%{opacity:1}50%{opacity:.55}}"
            ".s1{animation:glow 3.3s infinite}.s2{animation:glow 2.6s .4s infinite}.s3{animation:glow 2.1s .9s infinite}"
            "@keyframes shoot{0%,78%{transform:translate(0,0);opacity:0}80%{opacity:1}92%{transform:translate(260px,90px);opacity:0}100%{opacity:0}}"
            ".shoot{animation:shoot 7s ease-in infinite}"
            "@keyframes dash{to{stroke-dashoffset:-24}}.next{animation:dash 2s linear infinite}")]
    body = [f'<g class="shoot"><line x1="40" y1="40" x2="90" y2="57" stroke="url(#grad)" stroke-width="1.6" stroke-linecap="round"/></g>']
    defs = '<filter id="sg" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="3"/></filter>'
    for cluster, items in SKILLS.items():
        (cx, cy), offs = layouts[cluster]
        col = cols[cluster]
        pts = [(cx + ox, cy + oy) for ox, oy in offs[:len(items)]]
        learning = cluster == "NEXT ORBIT"
        dash = ' stroke-dasharray="4 4" class="next"' if learning else ""
        for a, b in zip(pts, pts[1:]):
            body.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{col}" stroke-opacity=".35" '
                        f'stroke-width="1.2"{dash}/>')
        body.append(f'<text x="{cx}" y="{36 if cy < 140 else 40}" font-size="12" font-weight="700" fill="{col}" '
                    f'text-anchor="middle" letter-spacing="3">{esc(cluster)}</text>')
        for (x, y), (name, lvl) in zip(pts, items):
            r = {0: 3, 1: 3.5, 2: 4.5, 3: 5.5}[lvl]
            op = 0.45 if learning else 1
            body.append(f'<g class="s{max(1, lvl)}" opacity="{op}"><circle cx="{x}" cy="{y}" r="{r * 2.6}" fill="{col}" '
                        f'opacity=".35" filter="url(#sg)"/><circle cx="{x}" cy="{y}" r="{r}" fill="#fff"/>'
                        f'<path d="M{x - r * 2.4} {y}H{x + r * 2.4}M{x} {y - r * 2.4}V{y + r * 2.4}" stroke="#fff" '
                        f'stroke-opacity=".5" stroke-width=".8"/></g>')
            body.append(f'<text x="{x}" y="{y + r + 18}" font-size="13" fill="{TEXT if not learning else MUTED}" '
                        f'text-anchor="middle">{esc(name)}</text>')
    body.append(f'<text x="{w - 18}" y="{h - 14}" font-size="11" fill="{DIM}" text-anchor="end">'
                f'★ brighter star = more experience · dashed = learning now</text>')
    return card(w, h, "".join(body), "".join(css), "Skill constellation", seed=21, stars=110, defs=defs)


# ───────────────────────────── project planet cards ─────────────────────────────
def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        if len(cur) + len(wd) + 1 > width:
            lines.append(cur); cur = wd
        else:
            cur = (cur + " " + wd).strip()
    return lines + [cur]


def project(slug, title, lang, stars, desc, link, seed):
    w, h = 290, 200
    col = LANG_COLOR.get(lang, C)
    px, py = 48, 52
    css = ("@keyframes band{from{transform:translateX(0)}to{transform:translateX(-40px)}}.band{animation:band 5s linear infinite}"
           "@keyframes halo{0%,100%{opacity:.25}50%{opacity:.5}}.halo{animation:halo 3s infinite}")
    defs = (f'<radialGradient id="pl" cx=".35" cy=".32" r=".8"><stop offset="0" stop-color="#fff" stop-opacity=".9"/>'
            f'<stop offset=".25" stop-color="{col}"/><stop offset="1" stop-color="#05080c"/></radialGradient>'
            f'<clipPath id="pc"><circle cx="{px}" cy="{py}" r="24"/></clipPath>')
    bands = "".join(f'<rect x="{px - 24 + j * 22}" y="{py - 20 + (j * 13) % 40}" width="40" height="5" rx="2.5" '
                    f'fill="#000" opacity=".22"/>' for j in range(6))
    body = [f'<circle class="halo" cx="{px}" cy="{py}" r="36" fill="{col}" opacity=".3" filter="url(#hb)"/>'
            f'<circle cx="{px}" cy="{py}" r="24" fill="url(#pl)"/><g clip-path="url(#pc)"><g class="band">{bands}</g></g>'
            f'<ellipse cx="{px}" cy="{py}" rx="38" ry="8" fill="none" stroke="{col}" stroke-opacity=".7" stroke-width="1.5" '
            f'transform="rotate(-20 {px} {py})" stroke-dasharray="70 200" stroke-dashoffset="-10"/>'
            f'<text x="92" y="48" font-size="17" font-weight="700" fill="{TEXT}">{esc(title)}</text>'
            f'<circle cx="97" cy="67" r="5" fill="{col}"/><text x="108" y="71" font-size="12" fill="{MUTED}">{esc(lang)}'
            f'{"   ★ " + str(stars) if stars else ""}</text>']
    for i, line in enumerate(wrap(desc, 33)[:3]):
        body.append(f'<text x="20" y="{110 + i * 19}" font-size="12.5" fill="{MUTED}">{esc(line)}</text>')
    body.append(f'<line x1="20" y1="166" x2="{w - 20}" y2="166" stroke="{BORDER}"/>'
                f'<text x="20" y="186" font-size="12.5" fill="url(#grad)" font-weight="700">▸ {esc(link)}</text>')
    defs += '<filter id="hb" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>'
    return card(w, h, "".join(body), css, f"Project: {title}", seed=seed, stars=35, defs=defs)


# ───────────────────────────── commit galaxy (live data) ─────────────────────────────
def fetch_contributions():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "profile-readme-generator"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    cells = {}
    for td in re.findall(r"<td[^>]*data-date[^>]*>", html):
        d = re.search(r'data-date="([\d-]+)"', td).group(1)
        lvl = int(re.search(r'data-level="(\d)"', td).group(1))
        cid = re.search(r'id="([^"]+)"', td).group(1)
        cells[cid] = [d, lvl, 0]
    for cid, label in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"\s*(\d+) contribution", label)
        if cid in cells and m:
            cells[cid][2] = int(m.group(1))
    days = sorted(cells.values())
    return days


def commit_galaxy(days):
    w, h = 900, 330
    cx, cy = 300, 168
    total = sum(c for _, _, c in days)
    active = sum(1 for _, _, c in days if c)
    best = max(days, key=lambda x: x[2]) if days else ("-", 0, 0)
    streak = longest = 0
    for _, _, c in days:
        streak = streak + 1 if c else 0
        longest = max(longest, streak)
    cur = 0
    for _, _, c in reversed(days):
        if c:
            cur += 1
        else:
            break
    rnd = random.Random(3)
    n = len(days)
    pal = ["#4a5566", G, C, "#7ee7ff", "#ffffff"]
    stars = []
    for i, (d, lvl, c) in enumerate(days):
        t = i / max(1, n - 1)                       # 0 = oldest (outer) .. 1 = today (core)
        arm = i % 2
        rad = 18 + (1 - t) ** 0.85 * 250 + rnd.gauss(0, 6)
        ang = arm * math.pi + (1 - t) * 3.3 * math.pi + rnd.gauss(0, 0.12)
        x, y = rad * math.cos(ang), rad * math.sin(ang)
        if lvl == 0:
            stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.3" fill="{pal[0]}"/>')
        else:
            r = 1.6 + lvl * 0.9
            cls = f' class="tw{i % 3}"' if lvl >= 3 else ""
            stars.append(f'<g{cls}><circle cx="{x:.1f}" cy="{y:.1f}" r="{r * 2.8:.1f}" fill="{pal[lvl]}" opacity=".28" '
                         f'filter="url(#sb)"/><circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{pal[lvl]}"/></g>')
    css = ("@keyframes spin{to{transform:rotate(360deg)}}.spin{transform-origin:0 0;animation:spin 140s linear infinite}"
           "@keyframes core{0%,100%{opacity:.85}50%{opacity:.55}}.core{animation:core 4s infinite}")
    defs = ('<filter id="sb" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="2.2"/></filter>'
            f'<radialGradient id="cg"><stop offset="0" stop-color="#fff"/><stop offset=".25" stop-color="{C}" stop-opacity=".6"/>'
            f'<stop offset="1" stop-color="{P}" stop-opacity="0"/></radialGradient>')
    first = days[0][0] if days else ""
    body = [f'<g transform="translate({cx} {cy}) scale(1 .5) rotate(-12)"><g class="spin">{"".join(stars)}</g></g>'
            f'<circle class="core" cx="{cx}" cy="{cy}" r="34" fill="url(#cg)"/>']
    x0 = 610
    rows = [(f"{total}", "contributions in the last year"), (f"{active}", "days with activity"),
            (f"{longest}", "day longest streak"), (f"{best[2]}", f"on my brightest day ({best[0]})")]
    body.append(f'<text x="{x0}" y="58" font-size="12" fill="{MUTED}" letter-spacing="2">LAST 12 MONTHS</text>')
    for i, (num, label) in enumerate(rows):
        y = 100 + i * 50
        body.append(f'<text x="{x0}" y="{y}" font-size="26" font-weight="700" fill="url(#grad)">{esc(num)}</text>'
                    f'<text x="{x0}" y="{y + 18}" font-size="12" fill="{MUTED}">{esc(label)}</text>')
    legend = "".join(f'<circle cx="{x0 + 92 + k * 16}" cy="{h - 22}" r="{1.4 + k * 0.9 if k else 1.4}" fill="{pal[k]}"/>' for k in range(5))
    body.append(f'<text x="{x0}" y="{h - 18}" font-size="11" fill="{DIM}">quiet</text>{legend}'
                f'<text x="{x0 + 92 + 5 * 16}" y="{h - 18}" font-size="11" fill="{DIM}">busy</text>'
                f'<text x="20" y="{h - 14}" font-size="11" fill="{DIM}">each star = one day · core = today · '
                f'updated {dt.date.today().isoformat()}</text>')
    return card(w, h, "".join(body), css, f"Commit galaxy: {total} contributions since {first}", seed=31, stars=70, defs=defs)


# ───────────────────────────── journey timeline ─────────────────────────────
def journey():
    w, h = 900, 230
    n = len(JOURNEY)
    xs = [105 + i * (w - 210) / (n - 1) for i in range(n)]
    ys = [128 + 26 * math.sin(i / (n - 1) * math.pi * 1.6 - 0.3) for i in range(n)]
    reached = sum(1 for j in JOURNEY if j[3])
    d = f"M{xs[0]:.1f} {ys[0]:.1f}" + "".join(
        f" C{(xs[i - 1] + xs[i]) / 2:.1f} {ys[i - 1]:.1f} {(xs[i - 1] + xs[i]) / 2:.1f} {ys[i]:.1f} {xs[i]:.1f} {ys[i]:.1f}"
        for i in range(1, n))
    d_done = d.split(" C")[0] + "".join(" C" + seg for seg in d.split(" C")[1:reached])
    css = ("@keyframes flow{to{stroke-dashoffset:-60}}.flow{animation:flow 1.6s linear infinite}"
           "@keyframes ping{0%{transform:scale(.6);opacity:.9}100%{transform:scale(2.4);opacity:0}}"
           f".ping{{transform-box:fill-box;transform-origin:center;animation:ping 1.8s ease-out infinite}}")
    body = [f'<path d="{d}" fill="none" stroke="{DIM}" stroke-width="1.5" stroke-dasharray="3 6"/>'
            f'<path d="{d_done}" fill="none" stroke="url(#grad)" stroke-width="2.5"/>'
            f'<path class="flow" d="{d_done}" fill="none" stroke="#fff" stroke-opacity=".8" stroke-width="2.5" '
            f'stroke-dasharray="6 54" stroke-linecap="round"/>']
    for i, ((date, title, detail, done), x, y) in enumerate(zip(JOURNEY, xs, ys)):
        up = i % 2 == 0
        ty = y - 52 if up else y + 34
        col = [G, G, C, C, "#7ee7ff", P, P][min(i, 6)]
        if done:
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="{col}" opacity=".2"/>'
                        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{col}"/><circle cx="{x:.1f}" cy="{y:.1f}" r="2" fill="#fff"/>')
            if i == reached - 1:
                body.append(f'<circle class="ping" cx="{x:.1f}" cy="{y:.1f}" r="7" fill="none" stroke="{col}" stroke-width="2"/>')
        else:
            body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="none" stroke="{P}" stroke-dasharray="3 3"/>')
        tc, mc = (TEXT, MUTED) if done else (MUTED, DIM)
        body.append(f'<text x="{x:.1f}" y="{ty:.1f}" font-size="11" fill="{col}" text-anchor="middle" letter-spacing="1.5">{esc(date)}</text>'
                    f'<text x="{x:.1f}" y="{ty + 17:.1f}" font-size="13" font-weight="700" fill="{tc}" text-anchor="middle">{esc(title)}</text>'
                    f'<text x="{x:.1f}" y="{ty + 32:.1f}" font-size="11" fill="{mc}" text-anchor="middle">{esc(detail)}</text>')
    return card(w, h, "".join(body), css, "Journey timeline", seed=41, stars=60)


# ───────────────────────────── transmission ─────────────────────────────
def transmission():
    w, h = 900, 160
    ax, ay = 110, 92
    css = ("@keyframes wave{0%{transform:scale(.3);opacity:0}15%{opacity:.9}100%{transform:scale(1.6);opacity:0}}"
           f".wv{{transform-origin:{ax + 18}px {ay - 30}px;animation:wave 2.4s ease-out infinite}}"
           ".w1{animation-delay:.8s}.w2{animation-delay:1.6s}"
           "@keyframes blink{0%,60%{opacity:1}61%,100%{opacity:.2}}.led{animation:blink 1.2s infinite}")
    arcs = "".join(f'<path class="wv w{k}" d="M{ax + 30} {ay - 58} A40 40 0 0 1 {ax + 58} {ay - 18}" fill="none" '
                   f'stroke="url(#grad)" stroke-width="2.5" stroke-linecap="round"/>' for k in range(3))
    body = [arcs,
            f'<path d="M{ax - 42} {ay - 6} A46 46 0 0 0 {ax + 30} {ay - 62} Z" fill="#1c2430" stroke="{C}" stroke-opacity=".6"/>'
            f'<line x1="{ax - 6} " y1="{ay - 34}" x2="{ax + 18}" y2="{ay - 30}" stroke="{C}" stroke-width="1.5"/>'
            f'<circle class="led" cx="{ax + 18}" cy="{ay - 30}" r="3.5" fill="{G}"/>'
            f'<path d="M{ax - 8} {ay - 20} L{ax - 20} {ay + 30} M{ax - 8} {ay - 20} L{ax + 6} {ay + 30}" stroke="{MUTED}" stroke-width="2"/>'
            f'<line x1="{ax - 34}" y1="{ay + 30}" x2="{ax + 20}" y2="{ay + 30}" stroke="{MUTED}" stroke-width="2"/>',
            f'<text x="250" y="62" font-size="13" fill="{G}" letter-spacing="3">● {esc(TRANSMISSION[0])}</text>'
            f'<text x="250" y="94" font-size="20" font-weight="700" fill="{TEXT}">{esc(TRANSMISSION[1])}</text>'
            f'<text x="250" y="124" font-size="14" fill="url(#grad)">{esc(TRANSMISSION[2])}</text>']
    return card(w, h, "".join(body), css, "Contact", seed=51, stars=50)


def main():
    galaxy_only = "--galaxy" in sys.argv
    write("commit-galaxy.svg", commit_galaxy(fetch_contributions()))
    if galaxy_only:
        return
    for i, t in enumerate(["MISSION LOG", "SKILL CONSTELLATION", "FEATURED PLANETS", "COMMIT GALAXY", "JOURNEY", "TRANSMISSION"], 1):
        write(f"divider-{i}.svg", divider(f"{i:02d}", t))
    write("mission.svg", mission())
    write("skills.svg", skills())
    for k, p in enumerate(PROJECTS):
        write(f"project-{p[0].lower()}.svg", project(*p, seed=60 + k))
    write("journey.svg", journey())
    write("transmission.svg", transmission())


if __name__ == "__main__":
    main()
