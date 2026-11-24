#!/usr/bin/env python3
"""
Render the profile README cards as animated SVGs into cards/.

Look: black and gold, matching the LinkedIn project covers (near-black ground,
gold #D4B06A, Inter Display titles, a letterspaced mono label on every card).

Each card is a standalone SVG shown through <img>, so it can only use what
GitHub allows there: inline CSS animations, SMIL, and fonts embedded as data
URIs (no JS, no external requests). Fonts in fonts/ are subsets of Inter
(SIL OFL) and DejaVu Sans Mono (free licence).

Numbers come from data/contributions.json, written by fetch_contributions.py.
"""
import base64
import datetime
import json
import math
import os
import random
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
AVATAR = os.path.join(ROOT, "assets", "avatar.png")

# ---- who ---------------------------------------------------------------------
NAME_1, NAME_2 = "Atharva", "Dudhe"
ROLES = ["FULL STACK DEVELOPER", "BACKEND-FOCUSED ENGINEER", "BUILDING DEVELOPER TOOLS", "SHIPPING IN PUBLIC"]
HELLOS = ["hi there", "let's build", "ship daily", "say hello"]
# shortcut: glyph x-offsets of the name at 92px Inter Display 700, -2.6 spacing, measured in Chrome;
# re-measure (getStartPositionOfChar) if NAME_*, the font or the size changes.
NAME_X = {NAME_1: [0, 59.4, 90.8, 142, 190.3, 223.3, 270.1], NAME_2: [0, 61.9, 113.2, 165.5, 216.8]}
NAME_W = {NAME_1: 318.3, NAME_2: 265.9}
TAGLINE = ["Backend-focused full stack developer.", "I build developer tools and ship them in public."]
STACK = "Java · Spring Boot · TypeScript · Node.js · React"
SITE = "atharva-dudhe.vercel.app"

# ---- tokens ------------------------------------------------------------------
BG = "#0b0b0c"
BG_2 = "#141311"
EDGE = "#24211c"
GOLD = "#d4b06a"
GOLD_HI = "#ecd08f"
CREAM = "#ede6d6"
SOFT = "#c9c6bf"
MUTED = "#8f8a7e"
DIM = "#5c584f"
BAR = "#3a362e"
HEAT = ["#191815", "#3b3222", "#6b5530", "#a88446", "#e6c378"]
W = 880

DISPLAY = "'Inter Display', Inter, system-ui, sans-serif"
SANS = "Inter, system-ui, -apple-system, sans-serif"
MONO = "'DejaVu Sans Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
FONT_FILES = [
    ("Inter Display", 700, "display-700.woff"),
    ("Inter", 400, "inter-400.woff"),
    ("Inter", 500, "inter-500.woff"),
    ("DejaVu Sans Mono", 400, "mono-400.woff"),
]
EASE = "cubic-bezier(.16,1,.3,1)"
CSS = f"""
@keyframes rise{{from{{opacity:0;transform:translateY(12px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.3)}}to{{opacity:1;transform:none}}}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.25}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes glow{{0%,100%{{opacity:.35}}50%{{opacity:.9}}}}
@keyframes nudge{{0%,100%{{transform:none}}50%{{transform:translate(3px,-3px)}}}}
.r{{opacity:0;animation:rise .9s {EASE} both;transform-box:fill-box}}
.f{{opacity:0;animation:fade .8s ease-out both}}
.g{{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .9s {EASE} both}}
.p{{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .6s {EASE} both}}
.live{{animation:pulse 1.6s ease-in-out infinite}}
.glow{{animation:glow 3.2s ease-in-out infinite}}
.d{{animation:draw 1.4s {EASE} both}}
.nu{{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}}
@keyframes float{{0%,100%{{transform:none}}50%{{transform:translateY(-7px)}}}}
@keyframes twinkle{{0%,100%{{opacity:0;transform:scale(.3) rotate(0)}}50%{{opacity:1;transform:scale(1) rotate(45deg)}}}}
@keyframes wave{{0%,55%,100%{{transform:none}}10%,30%{{transform:rotate(16deg)}}20%,40%{{transform:rotate(-8deg)}}}}
@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
@keyframes sheen{{from{{transform:translateX(-160px)}}to{{transform:translateX(420px)}}}}
.fl{{transform-box:fill-box;animation:float 4.5s ease-in-out 1s infinite}}
.tw{{opacity:0;transform-box:fill-box;transform-origin:center;animation:twinkle 2.8s ease-in-out infinite}}
.wv{{transform-box:fill-box;transform-origin:70% 85%;animation:wave 2.6s ease-in-out 1.8s infinite}}
.cur{{animation:blink 1s step-end infinite}}
.sh{{animation:sheen 3.6s ease-in-out infinite}}
@keyframes hop{{0%,6%,100%{{transform:none}}3%{{transform:translateY(-12px)}}}}
@keyframes sway{{0%,100%{{transform:rotate(-3deg)}}50%{{transform:rotate(3deg)}}}}
@keyframes roll{{0%{{opacity:0;transform:translateY(8px)}}4%,21%{{opacity:1;transform:none}}25%,100%{{opacity:0;transform:translateY(-8px)}}}}
.hop{{transform-box:fill-box;animation:hop 6s ease-in-out infinite}}
.sway{{animation:sway 6s ease-in-out infinite}}
.bob{{transform-box:fill-box;animation:float 3.2s ease-in-out infinite}}
.roll{{opacity:0;transform-box:fill-box;animation:roll 10s ease-in-out infinite}}
"""


def font_css():
    out = []
    for fam, weight, fn in FONT_FILES:
        with open(os.path.join(FONTS, fn), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};"
                   f"src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "".join(out)


FONT_CSS = None


def svg(h, body, desc, w=W):
    global FONT_CSS
    if FONT_CSS is None:
        FONT_CSS = font_css()
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(desc)}"><title>{escape(desc)}</title>'
            f'<style>{FONT_CSS}{CSS}</style>'
            f'<defs><radialGradient id="bg" cx="78%" cy="18%" r="95%">'
            f'<stop offset="0" stop-color="{BG_2}"/><stop offset="1" stop-color="{BG}"/></radialGradient>'
            f'<linearGradient id="rule" x1="0" x2="1"><stop offset="0" stop-color="{GOLD}"/>'
            f'<stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></linearGradient></defs>'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-9}" rx="16" fill="url(#bg)" stroke="{EDGE}"/>'
            f'{body}</svg>')


def text(x, y, s, size, fill, family=SANS, weight=400, spacing=0, anchor="start", cls="", delay=0, extra=""):
    st = f' style="animation-delay:{delay:.2f}s"' if cls else ""
    c = f' class="{cls}"' if cls else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}{c}{st}{extra}>{escape(s)}</text>')


def label(x, y, s, delay=0, dot=True):
    out = ""
    if dot:
        out += f'<circle cx="{x+4}" cy="{y-4}" r="3.5" fill="{GOLD}" class="live"/>'
        x += 16
    return out + text(x, y, s, 11, MUTED, MONO, spacing=2.6, cls="f", delay=delay)


# ---- hero ----------------------------------------------------------------------
def shine(gid, base, hi, begin):
    """A highlight band that sweeps across the name every few seconds."""
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="360" y2="0">'
            f'<stop offset="0" stop-color="{base}"/><stop offset=".42" stop-color="{base}"/>'
            f'<stop offset=".5" stop-color="{hi}"/><stop offset=".58" stop-color="{base}"/>'
            f'<stop offset="1" stop-color="{base}"/>'
            f'<animateTransform attributeName="gradientTransform" type="translate" values="-420 0;520 0;520 0" '
            f'keyTimes="0;.45;1" dur="5.5s" begin="{begin}s" repeatCount="indefinite"/></linearGradient>')


def name_line(word, x, y, gid, first):
    """Each letter rises in on its own, then the word does a small wave every few seconds."""
    out = []
    for i, (ch, dx) in enumerate(zip(word, NAME_X[word])):
        k = first + i
        out.append(f'<g class="r" style="animation-delay:{.15 + k*.045:.2f}s">'
                   f'<text x="{x + dx:.1f}" y="{y}" font-family="{DISPLAY}" font-size="92" font-weight="700" '
                   f'fill="url(#{gid})" class="hop" style="animation-delay:{2.4 + k*.07:.2f}s">{escape(ch)}</text></g>')
    return "".join(out)


def cycle(x, y, words, size, fill, family, spacing=0, period=10):
    step = period / len(words)
    return "".join(f'<g class="roll" style="animation-duration:{period}s;animation-delay:{.8 + i*step:.1f}s">'
                   f'{text(x, y, w, size, fill, family, spacing=spacing)}</g>' for i, w in enumerate(words))


def avatar_motif(cx, cy, s=280):
    """The cut-out 3D head floating free: sways, bobs, catches a glint on the glasses."""
    with open(AVATAR, "rb") as f:
        img = base64.b64encode(f.read()).decode()
    x0, y0 = cx - s/2, cy - s/2
    out = [f'<radialGradient id="halo"><stop offset="0" stop-color="{GOLD}" stop-opacity=".3"/>'
           f'<stop offset="1" stop-color="{GOLD}" stop-opacity="0"/></radialGradient>'
           f'<circle cx="{cx}" cy="{cy + 10}" r="{s*.62:.0f}" fill="url(#halo)" class="glow"/>',
           # a tilted orbit with two dots riding it
           f'<g class="f" style="animation-delay:.7s"><g transform="rotate(-18 {cx} {cy}) translate({cx} {cy}) scale(1 .34)">'
           f'<circle r="{s*.56:.0f}" fill="none" stroke="{GOLD}" stroke-opacity=".4" stroke-dasharray="2 7" '
           f'vector-effect="non-scaling-stroke"/><g>'
           f'<circle cx="{s*.56:.0f}" r="4.5" fill="{GOLD_HI}"/><circle cx="{-s*.56:.0f}" r="3" fill="{GOLD}"/>'
           f'<animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="9s" '
           f'repeatCount="indefinite"/></g></g></g>']
    # glasses glint, in image fractions; rides along with the head
    lenses = ((.476, .59, .085, .075), (.71, .566, .085, .08))
    clip = "".join(f'<ellipse cx="{x0 + fx*s:.1f}" cy="{y0 + fy*s:.1f}" rx="{rx*s:.1f}" ry="{ry*s:.1f}"/>'
                   for fx, fy, rx, ry in lenses)
    out.append(f'<clipPath id="lens">{clip}</clipPath>'
               f'<linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
               f'<stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
               f'</linearGradient>')
    out.append(f'<g class="p" style="animation-delay:.3s"><g class="fl"><g class="sway" '
               f'style="transform-origin:{cx}px {y0 + s*.85:.0f}px">'
               f'<image href="data:image/png;base64,{img}" x="{x0}" y="{y0}" width="{s}" height="{s}"/>'
               f'<g clip-path="url(#lens)"><rect x="{x0 + s*.3:.0f}" y="{y0 + s*.4:.0f}" width="26" height="{s*.4:.0f}" '
               f'fill="url(#gl)" transform="skewX(-20)" opacity="0">'
               f'<animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.05;.2;.25;1" dur="5s" begin="2s" repeatCount="indefinite"/>'
               f'<animateTransform attributeName="transform" type="translate" additive="sum" values="0 0;{s*.55:.0f} 0;{s*.55:.0f} 0" '
               f'keyTimes="0;.25;1" dur="5s" begin="2s" repeatCount="indefinite"/></rect></g></g></g></g>')
    # twinkling sparkles
    for k, (x, y, r) in enumerate(((cx - s*.5, cy - s*.28, 9), (cx + s*.5, cy + s*.22, 7),
                                   (cx + s*.34, cy - s*.46, 6), (cx - s*.42, cy + s*.4, 5))):
        out.append(f'<path d="M{x},{y - r} Q{x},{y} {x + r},{y} Q{x},{y} {x},{y + r} Q{x},{y} {x - r},{y} '
                   f'Q{x},{y} {x},{y - r}Z" fill="{GOLD_HI}" class="tw" style="animation-delay:{1.2 + k*.6:.1f}s"/>')
    # speech bubble with rotating hellos
    bx, by = cx - s*.5 - 80, cy - s*.42
    out.append(f'<g class="p" style="animation-delay:1.4s"><g class="bob">'
               f'<rect x="{bx}" y="{by}" width="124" height="34" rx="17" fill="{BG_2}" stroke="{GOLD}" stroke-opacity=".6"/>'
               f'<path d="M{bx + 96},{by + 33} l12,12 l-3,-12z" fill="{BG_2}" stroke="{GOLD}" stroke-opacity=".6"/>'
               f'<rect x="{bx + 92}" y="{by + 30}" width="18" height="3" fill="{BG_2}"/>'
               f'{cycle(bx + 14, by + 22, HELLOS, 12.5, CREAM, MONO, period=10)}'
               f'<text x="{bx + 96}" y="{by + 23}" font-size="15" class="wv">👋</text></g></g>')
    return "".join(out)


def hero():
    h = 368
    b = [shine("sA", GOLD, "#fff3cf", 2.0), shine("sB", CREAM, GOLD_HI, 2.6)]
    b.append(f'<circle cx="44" cy="48" r="3.5" fill="{GOLD}" class="live"/>')
    b.append(cycle(56, 52, ROLES, 11, MUTED, MONO, spacing=2.6))
    b.append(name_line(NAME_1, 38, 152, "sA", 0))
    b.append(name_line(NAME_2, 38, 238, "sB", len(NAME_1)))
    cx = 38 + NAME_W[NAME_2] + 12
    b.append(f'<g class="f" style="animation-delay:1s"><rect x="{cx:.0f}" y="176" width="12" height="62" fill="{GOLD}" class="cur"/></g>')
    for i, line in enumerate(TAGLINE):
        b.append(text(41, 284 + i*22, line, 16, SOFT, SANS, cls="r", delay=.7 + i*.08))
    b.append(f'<rect x="40" y="320" width="800" height="1" fill="url(#rule)" class="f" style="animation-delay:.9s"/>')
    b.append(text(40, 346, STACK, 11.5, MUTED, MONO, spacing=.6, cls="f", delay=1))
    b.append(f'<g class="nu">{text(840, 346, SITE + " ↗", 11.5, GOLD, MONO, spacing=.6, anchor="end", cls="f", delay=1.1)}</g>')
    b.append(avatar_motif(696, 168, 316))
    return svg(h, "".join(b), f"{NAME_1} {NAME_2}. Full stack developer, backend-focused. "
                              f"Builds developer tools in public. {STACK}.")


# ---- heatmap -------------------------------------------------------------------
def heatmap(data):
    days = data["days"]
    h = 248
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # Sunday-first rows, like GitHub
    weeks = math.ceil((lead + len(days)) / 7)
    step = min(15, 800 / weeks)
    cell = step - 3
    x0, y0 = 40, 92
    b = [text(40, 62, "Every day, ", 30, CREAM, DISPLAY, 700, -.8, cls="r",
              extra="").replace("</text>", f'<tspan fill="{GOLD}">in gold.</tspan></text>'),
         text(840, 58, "REFRESHED DAILY", 11, MUTED, MONO, spacing=2.6, anchor="end", cls="f", delay=.3)]
    last_month = None
    last_x = -99
    lx = 840 - 5*14 - 30
    for i, d in enumerate(days):
        idx = lead + i
        wk, dow = divmod(idx, 7)
        x, y = x0 + wk*step, y0 + dow*step
        lvl = d["level"]
        b.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" rx="2.5" '
                 f'fill="{HEAT[lvl]}" class="p" style="animation-delay:{.25 + wk*.018:.2f}s"/>')
        date = datetime.date.fromisoformat(d["date"])
        if date.month != last_month:
            last_month = date.month
            if x - last_x > 34 and x < lx - 70:
                b.append(text(x, y0 + 7*step + 16, date.strftime("%b"), 10.5, MUTED, MONO, cls="f", delay=.6))
                last_x = x
    b.append(text(lx - 8, y0 + 7*step + 16, "less", 10.5, MUTED, MONO, anchor="end", cls="f", delay=.8))
    for k, c in enumerate(HEAT):
        b.append(f'<rect x="{lx + k*14}" y="{y0 + 7*step + 7}" width="11" height="11" rx="2.5" fill="{c}" '
                 f'class="f" style="animation-delay:.85s"/>')
    b.append(text(lx + 5*14 + 4, y0 + 7*step + 16, "more", 10.5, MUTED, MONO, cls="f", delay=.8))
    return svg(h, "".join(b), f"Contribution graph for the last year in gold: {data['total']:,} contributions.")


# ---- activity ------------------------------------------------------------------
def activity(data):
    h = 340
    months = data["monthly"][-12:]
    today = datetime.date.fromisoformat(data["days"][-1]["date"])
    peak = max(months, key=lambda m: m["total"])
    top = max(m["total"] for m in months) or 1
    b = [label(40, 50, "THE LAST 12 MONTHS ON GITHUB", dot=False),
         text(38, 102, f"{data['total']:,} ", 52, GOLD, DISPLAY, 700, -1.6, cls="r", delay=.1)
         .replace("</text>", f'<tspan fill="{CREAM}">contributions</tspan></text>')]
    x0, base, maxh = 40, 296, 150
    slot = 560 / len(months)
    bw = slot * .62
    for i, m in enumerate(months):
        hh = max(3, m["total"] / top * maxh)
        x = x0 + i*slot
        current = m["month"] == today.strftime("%Y-%m")
        fill = GOLD if m is peak else (DIM if current else BAR)
        b.append(f'<rect x="{x:.1f}" y="{base-hh:.1f}" width="{bw:.1f}" height="{hh:.1f}" rx="3" fill="{fill}" '
                 f'class="g" style="animation-delay:{.3 + i*.05:.2f}s"/>')
        mon = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        b.append(text(x + bw/2, base + 20, mon, 10.5, GOLD if m is peak else MUTED, MONO, anchor="middle",
                      cls="f", delay=.5))
        if m is peak:
            b.append(text(x + bw/2, base - hh - 9, str(m["total"]), 11, GOLD, MONO, anchor="middle",
                          cls="f", delay=1.1))
    # stats column
    sx = 640
    stats = [
        (f"{data['current_streak']}", " days", f"current streak, longest {data['longest_streak']}"),
        (f"{data['active_days']}", f" / {data['day_count']}", "days with a commit"),
        (f"{data['best_day']['count']}", "", "on the busiest day"),
    ]
    for i, (big, small, cap) in enumerate(stats):
        y = 150 + i*72
        b.append(text(sx, y, big, 34, GOLD if i == 0 else CREAM, DISPLAY, 700, -1, cls="r", delay=.4 + i*.12))
        if small:
            b[-1] = b[-1].replace("</text>", f'<tspan fill="{MUTED}" font-size="22">{small}</tspan></text>')
        b.append(text(sx, y + 22, cap, 13, SOFT, SANS, cls="f", delay=.6 + i*.12))
        if i < 2:
            b.append(f'<rect x="{sx}" y="{y+40}" width="200" height="1" fill="{EDGE}" class="f" '
                     f'style="animation-delay:.8s"/>')
    return svg(h, "".join(b), f"{data['total']:,} contributions in the last 12 months. "
                              f"Current streak {data['current_streak']} days.")


# ---- two tiles -----------------------------------------------------------------
TW, TH = 440, 300


def tile(tag, big, word, lines, foot, desc, motif):
    b = [label(28, 46, tag, dot=False)]
    b.append(motif)
    b.append(text(26, 148, big, 64, GOLD, DISPLAY, 700, -2, cls="r", delay=.15))
    b.append(text(28, 178, word, 18, CREAM, DISPLAY, 700, -.3, cls="r", delay=.25))
    for i, ln in enumerate(lines):
        b.append(text(28, 210 + i*19, ln, 12.5, SOFT, SANS, cls="f", delay=.4 + i*.06))
    b.append(f'<rect x="28" y="258" width="{TW-56}" height="1" fill="url(#rule)" class="f" style="animation-delay:.6s"/>')
    b.append(text(28, 280, foot, 11, GOLD, MONO, spacing=.5, cls="f", delay=.7))
    return svg(TH, "".join(b), desc, w=TW)


def dots_motif(seed, cols=6, rows=4):
    rnd = random.Random(seed)
    out = []
    for r in range(rows):
        for c in range(cols):
            lvl = rnd.choice([0, 1, 1, 2, 3, 4])
            out.append(f'<rect x="{TW-28-cols*11+c*11}" y="{32+r*11}" width="8" height="8" rx="1.5" '
                       f'fill="{HEAT[lvl]}" class="p" style="animation-delay:{.2+(c+r)*.04:.2f}s"/>')
    return "".join(out)


def ring_motif():
    cx, cy = TW - 58, 58
    return "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{GOLD}" '
                   f'stroke-opacity="{op}" class="glow" style="animation-delay:{d}s"/>'
                   for r, op, d in ((8, .9, 0), (18, .5, .4), (28, .25, .8))) + \
        f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{GOLD_HI}"/>'


def tiles(data):
    repos = data.get("repos") or {"own": 8}
    return {
        "build": tile("01 / BUILD", str(repos["own"]), "projects of my own",
                      ["Full stack apps, CLIs and", "experiments, all in the open."],
                      "see the repos →", f"BUILD: {repos['own']} public repos of my own", dots_motif(7)),
        "ship": tile("02 / SHIP", "npx", "synapse-map",
                     ["Maps a codebase by what it", "depends on, then shows it in 3D."],
                     "open Synapse →", "SHIP: Synapse, published on npm as synapse-map", ring_motif()),
    }


# ---- terminal ------------------------------------------------------------------
SESSION = [
    ("whoami", f"{NAME_1.lower()} {NAME_2.lower()}  ·  backend-focused full stack developer"),
    ("cat stack.txt", STACK),
    ("npx synapse-map .", "mapping dependencies ... rendering your codebase in 3D  ✓"),
]


def terminal():
    """A shell session that types itself out, then waits with a blinking cursor."""
    h, size, cw = 270, 13.5, 13.5 * .602  # mono advance is ~0.6 em
    b = [f'<rect x="1" y="1" width="{W-2}" height="38" rx="15" fill="{BG_2}"/>'
         f'<rect x="1" y="24" width="{W-2}" height="15" fill="{BG_2}"/>'
         f'<rect x="1" y="39" width="{W-2}" height="1" fill="{EDGE}"/>']
    for i, c in enumerate(("#e06c5f", "#e3b452", "#6cbf6a")):
        b.append(f'<circle cx="{26 + i*18}" cy="20" r="5.5" fill="{c}" fill-opacity=".85"/>')
    b.append(text(W/2, 25, "atharv1205 — zsh", 11, MUTED, MONO, spacing=1, anchor="middle"))
    t, y = .6, 76
    for k, (cmd, out) in enumerate(SESSION):
        full = "$ " + cmd
        steps = len(full)
        dur = steps * .055
        vals = ";".join(f"{(i+1)*cw:.1f}" for i in range(steps))
        b.append(f'<clipPath id="ty{k}"><rect x="40" y="{y-16}" height="22" width="0">'
                 f'<animate attributeName="width" values="{vals}" calcMode="discrete" dur="{dur:.2f}s" '
                 f'begin="{t:.2f}s" fill="freeze"/></rect></clipPath>')
        b.append(f'<g clip-path="url(#ty{k})">{text(40, y, "$ ", size, GOLD, MONO)}'
                 .replace("</text>", f'<tspan fill="{CREAM}">{escape(cmd)}</tspan></text>') + '</g>')
        t += dur + .25
        b.append(text(40, y + 22, "→ " + out, size, SOFT, MONO, cls="f", delay=t))
        t += .55
        y += 52
    b.append(text(40, y, "$", size, GOLD, MONO, cls="f", delay=t))
    b.append(f'<g class="f" style="animation-delay:{t:.2f}s"><rect x="{40 + 2*cw:.1f}" y="{y-13}" width="{cw:.1f}" '
             f'height="17" fill="{GOLD}" class="cur"/></g>')
    return svg(h, "".join(b), "Terminal: whoami, Atharva Dudhe, backend-focused full stack developer. "
                              f"Stack: {STACK}. Ships Synapse, run with npx synapse-map.")


# ---- link buttons -----------------------------------------------------------------
LINKS = [("portfolio", "Portfolio"), ("linkedin", "LinkedIn"), ("youtube", "YouTube"), ("email", "Email")]


def button(word, i):
    bw, bh = 214, 64
    b = [f'<clipPath id="bc"><rect x="1" y="1" width="{bw-2}" height="{bh-11}" rx="15"/></clipPath>'
         f'<linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="{GOLD}" stop-opacity="0"/>'
         f'<stop offset=".5" stop-color="{GOLD}" stop-opacity=".22"/><stop offset="1" stop-color="{GOLD}" stop-opacity="0"/>'
         f'</linearGradient>'
         f'<g clip-path="url(#bc)"><rect x="0" y="0" width="120" height="{bh}" fill="url(#sg)" class="sh" '
         f'style="animation-delay:{i*.5:.1f}s"/></g>']
    b.append(text(bw/2 - 8, 34, word.upper(), 12, CREAM, MONO, spacing=2.4, anchor="middle", cls="f", delay=.2 + i*.1))
    b.append(f'<g class="nu">{text(bw/2 + len(word)*5.2 + 6, 34, "↗", 13, GOLD, MONO, anchor="middle")}</g>')
    return svg(bh, "".join(b), word, w=bw)


def main():
    with open(DATA) as f:
        data = json.load(f)
    os.makedirs(OUT, exist_ok=True)
    cards = {"hero": hero(), "terminal": terminal(), "heatmap": heatmap(data), "activity": activity(data),
             **tiles(data), **{f"link-{k}": button(w, i) for i, (k, w) in enumerate(LINKS)}}
    for name, s in cards.items():
        with open(os.path.join(OUT, f"{name}.svg"), "w") as f:
            f.write(s)
    print("wrote", ", ".join(f"{k}.svg" for k in cards))


if __name__ == "__main__":
    main()
