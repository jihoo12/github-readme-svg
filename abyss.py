"""Deep-sea banner: bioluminescent jellyfish pulsing through the dark, with an anglerfish passing by.

Same contract as creative.py: (name, lines, tags, theme, seed) -> svg string, using only CSS
animations and SMIL so the banner plays on GitHub.
"""

from __future__ import annotations

import math
import random

from common import MONO, SANS, THEMES, esc, text_width
from creative import reduced, svg_open

# (water near the surface, water in the deep, silhouette colour)
WATER = {
    "aurora": ("#0d2360", "#02030b", "#070d24"),
    "sunset": ("#3d1450", "#07030d", "#150822"),
    "ocean": ("#064468", "#010710", "#031a2b"),
}

WAVE_FRAMES = 5


def _bell(w: float, h: float, scallops: int = 7) -> str:
    """Dome with a scalloped rim; the rim centre sits on the local origin."""
    d = [f"M{-w:.1f} 0 C{-w * 1.06:.1f} {-h * 1.38:.1f} {w * 1.06:.1f} {-h * 1.38:.1f} {w:.1f} 0"]
    step = 2 * w / scallops
    for i in range(scallops):
        x1 = w - step * (i + 1)
        d.append(f"Q{x1 + step / 2:.1f} {h * 0.2:.1f} {x1:.1f} 0")
    return " ".join(d) + "Z"


def _strand(x0: float, length: float, amp: float, phase: float, t: float, pts: int, spread: float) -> str:
    """One frame of a tentacle: a travelling sine wave that grows towards the free end."""
    p = []
    for k in range(pts + 1):
        u = k / pts
        x = x0 + spread * u + amp * u ** 0.8 * math.sin(phase + k * 0.85 - t)
        p.append((x, length * u))
    # whole-unit vertical coordinates keep the many animation frames compact
    d = [f"M{p[0][0]:.1f} {p[0][1]:.0f}"]
    for a, b in zip(p[1:-1], p[2:]):
        d.append(f"Q{a[0]:.1f} {a[1]:.0f} {(a[0] + b[0]) / 2:.1f} {(a[1] + b[1]) / 2:.0f}")
    d.append(f"T{p[-1][0]:.1f} {p[-1][1]:.0f}")
    return " ".join(d)


def _tentacle(x0: float, length: float, amp: float, phase: float, dur: float, cls: str, pts: int = 6,
              spread: float = 0.0) -> str:
    frames = [_strand(x0, length, amp, phase, 2 * math.pi * f / WAVE_FRAMES, pts, spread)
              for f in range(WAVE_FRAMES)]
    return (f'<path class="{cls}" d="{frames[0]}"><animate attributeName="d" dur="{dur:.1f}s" '
            f'repeatCount="indefinite" values="{";".join([*frames, frames[0]])}"/></path>')


def _jelly(rng: random.Random, uid: int, x: float, y: float, scale: float, color: str, opacity: float) -> str:
    w, h = 34.0, 30.0
    pulse = rng.uniform(3.2, 4.6)
    begin = rng.uniform(0, pulse)
    wave = rng.uniform(3.4, 5.0)
    tilt = rng.uniform(-16, 16)
    n_t = 9 if scale > 0.8 else 6

    strands = []
    for i in range(n_t):
        u = i / (n_t - 1) * 2 - 1
        strands.append(_tentacle(u * w * 0.86, rng.uniform(70, 118), rng.uniform(5, 10), rng.uniform(0, 6.28),
                                 wave * rng.uniform(0.85, 1.2), "tn", pts=5, spread=u * 9))
    arms = "".join(
        _tentacle(u * w * 0.3, rng.uniform(44, 62), rng.uniform(7, 11), rng.uniform(0, 6.28), wave * 1.3, "arm",
                  pts=4, spread=u * 4)
        for u in (-1, 0, 1)
    )
    organs = "".join(
        f'<ellipse cx="{cx:.1f}" cy="{-h * 0.62:.1f}" rx="{w * 0.11:.1f}" ry="{h * 0.13:.1f}" class="organ"/>'
        for cx in (-w * 0.42, -w * 0.14, w * 0.14, w * 0.42)
    )
    # slow closed loop so every jellyfish wanders a little around its home position
    rx, ry = rng.uniform(10, 26), rng.uniform(8, 18)
    loop = f"M0 0 C{rx:.0f} {-ry:.0f} {rx * 2:.0f} {ry:.0f} 0 {ry * 1.4:.0f} C{-rx * 2:.0f} {ry:.0f} {-rx:.0f} {-ry:.0f} 0 0"
    drift = rng.uniform(22, 34)
    smil = f'dur="{pulse:.2f}s" begin="-{begin:.2f}s" repeatCount="indefinite" calcMode="spline"'
    return f"""
    <g transform="translate({x:.0f} {y:.0f}) rotate({tilt:.0f}) scale({scale:.2f})" opacity="{opacity}" color="{color}">
      <g><animateMotion dur="{drift:.0f}s" begin="-{rng.uniform(0, drift):.0f}s" repeatCount="indefinite" path="{loop}"/>
        <g><animateTransform attributeName="transform" type="translate" {smil}
            values="0 0;0 -3;0 -10;0 0" keyTimes="0;.32;.6;1" keySplines=".4 0 .6 1;.2 .6 .4 1;.4 0 .6 1"/>
          <circle cy="{-h * 0.5:.0f}" r="{w * 2.1:.0f}" fill="url(#halo{uid})" class="halo" style="animation-duration:{pulse:.2f}s;animation-delay:-{begin:.2f}s"/>
          <g><animateTransform attributeName="transform" type="scale" {smil}
              values="1 1;.78 1.12;1 1" keyTimes="0;.32;1" keySplines=".5 0 .5 1;.2 .5 .4 1"/>
            {"".join(strands)}
            {arms}
            <path d="{_bell(w, h)}" fill="url(#bell{uid})" class="bell"/>
            <path d="{_bell(w * 0.72, h * 0.78)}" class="inner"/>
            {organs}
            <path d="M{-w * 0.62:.1f} {-h * 0.62:.1f} C{-w * 0.5:.1f} {-h * 0.95:.1f} {-w * 0.2:.1f} {-h * 1.0:.1f} 0 {-h * 1.0:.1f}" class="shine"/>
          </g>
        </g>
      </g>
    </g>"""


def _jelly_defs(uid: int, color: str) -> str:
    return f"""
    <radialGradient id="bell{uid}" cx="50%" cy="20%" r="85%">
      <stop offset="0" stop-color="#fff" stop-opacity=".9"/><stop offset=".35" stop-color="{color}" stop-opacity=".75"/>
      <stop offset="1" stop-color="{color}" stop-opacity=".18"/>
    </radialGradient>
    <radialGradient id="halo{uid}">
      <stop offset="0" stop-color="{color}" stop-opacity=".5"/><stop offset=".5" stop-color="{color}" stop-opacity=".14"/>
      <stop offset="1" stop-color="{color}" stop-opacity="0"/>
    </radialGradient>"""


def _ridge(rng: random.Random, W: float, H: float, base: float, rough: float) -> str:
    d, x = [f"M0 {H}", f"L0 {base:.0f}"], 0.0
    while x < W:
        step = rng.uniform(40, 90)
        y = base + rng.uniform(-rough, rough)
        d.append(f"Q{x + step / 2:.0f} {y - rng.uniform(4, rough * 1.6):.0f} {x + step:.0f} {y:.0f}")
        x += step
    return " ".join(d) + f" L{W} {H}Z"


ANGLER = """
      <path d="M-46 -2 C-40 -24 -12 -30 12 -18 C22 -13 30 -8 38 -14 L52 -24 C47 -8 47 6 53 20 L38 10
               C30 5 22 12 12 16 C-6 24 -24 22 -34 14 L-27 9 L-33 8 L-27 4 L-34 2 L-28 -1 L-36 -3 L-31 -6 L-40 -8 L-36 -10Z"/>
      <path d="M-6 -26 L2 -38 L8 -30 L16 -36 L18 -16Z"/>
      <path d="M-2 14 C6 26 14 26 18 14Z"/>
      <path d="M-2 2 C6 -2 14 2 16 8 C8 10 2 8 -2 2Z" class="fin"/>
      <path d="M-30 -22 C-36 -44 -60 -46 -66 -28" class="rod"/>
      <circle cx="-25" cy="-12" r="3.2" class="eye"/><circle cx="-25.6" cy="-12" r="1.4" fill="#000"/>
      <circle cx="-66" cy="-25" r="22" fill="url(#lure)" class="lure"/>
      <circle cx="-66" cy="-25" r="3" class="bulb"/>"""


def build_abyss(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Bioluminescent jellyfish drifting through the deep sea around a softly refracted title."""
    W, H = 900, 300
    rng = random.Random(seed)
    top, deep, dark = WATER.get(theme, WATER["aurora"])
    c1, c2, c3 = THEMES.get(theme, THEMES["aurora"])[1]

    # (x, y, scale, opacity): small faint ones in the back, large ones framing the title in front
    back = [(250, 216, 0.5, 0.5), (668, 206, 0.56, 0.55), (58, 70, 0.4, 0.42), (842, 232, 0.44, 0.45),
            (470, 52, 0.34, 0.38)]
    front = [(112, 132, 1.0, 0.95), (768, 104, 1.14, 0.95)]
    colors = [c1, c2, c3]
    defs, back_svg, front_svg = [], [], []
    for uid, (x, y, s, o) in enumerate(back + front):
        col = colors[uid % 3]
        defs.append(_jelly_defs(uid, col))
        jelly = _jelly(rng, uid, x + rng.uniform(-14, 14), y + rng.uniform(-8, 8), s, col, o)
        (back_svg if uid < len(back) else front_svg).append(jelly)

    shafts = []
    for i in range(6):
        x = rng.uniform(-40, W - 80)
        w0, w1, lean = rng.uniform(16, 50), rng.uniform(80, 170), rng.uniform(60, 150)
        shafts.append(
            f'<path d="M{x:.0f} -4 L{x + w0:.0f} -4 L{x + lean + w1:.0f} {H * 0.86:.0f} L{x + lean:.0f} {H * 0.86:.0f}Z" '
            f'class="shaft" style="animation-duration:{rng.uniform(6, 11):.1f}s;animation-delay:-{rng.uniform(0, 9):.1f}s"/>'
        )

    snow = []
    for _ in range(48):
        dur = rng.uniform(18, 46)
        snow.append(
            f'<circle cx="{rng.uniform(0, W):.0f}" cy="-4" r="{rng.uniform(0.5, 1.5):.1f}" class="snow" '
            f'style="animation-duration:{dur:.0f}s;animation-delay:-{rng.uniform(0, dur):.0f}s;'
            f'--sx:{rng.uniform(-50, 50):.0f}px;opacity:{rng.uniform(0.15, 0.55):.1f}"/>'
        )

    plankton = []
    for _ in range(34):
        plankton.append(
            f'<circle cx="{rng.uniform(0, W):.0f}" cy="{rng.uniform(20, H - 20):.0f}" r="{rng.uniform(0.9, 2.1):.1f}" '
            f'fill="{rng.choice(colors)}" class="glint" style="animation-duration:{rng.uniform(2.5, 6):.1f}s;'
            f'animation-delay:-{rng.uniform(0, 6):.1f}s"/>'
        )

    bubbles = []
    for _ in range(5):
        bx, dur = rng.uniform(60, W - 60), rng.uniform(9, 15)
        delay = rng.uniform(0, dur)
        for j in range(rng.randint(2, 4)):
            r = rng.uniform(1.6, 4.4)
            bubbles.append(
                f'<g class="rise" style="animation-duration:{dur:.1f}s;animation-delay:-{delay + j * 0.5:.1f}s">'
                f'<g class="sway" style="animation-duration:{rng.uniform(1.6, 2.8):.1f}s">'
                f'<circle cx="{bx + rng.uniform(-9, 9):.0f}" cy="{H + 10}" r="{r:.1f}" class="bubble"/></g></g>'
            )

    # depth gauge along the right edge
    gx, g0, g1 = W - 22, 34, H - 44
    ticks = "".join(
        f'<path d="M{gx} {g0 + (g1 - g0) * i / 20:.1f} h{-9 if i % 5 == 0 else -5}"/>' for i in range(21)
    )
    labels = "".join(
        f'<text x="{gx - 13}" y="{g0 + (g1 - g0) * i / 4 + 3:.0f}" text-anchor="end" class="depth">{3600 + i * 100}m</text>'
        for i in range(5)
    )

    name_fs = min(54, 560 / max(1, len(name)) / 0.58)
    cx, ty = W / 2, 142
    shown = lines[:4] or [""]
    n = len(shown)
    slot = 100 / n
    subs = "".join(
        f'<text x="{cx}" y="{ty + 34}" text-anchor="middle" class="sub{" cyc" if n > 1 else ""}" '
        f'style="animation-delay:{i * 4}s{";opacity:0" if i else ""}">{esc(line)}</text>'
        for i, line in enumerate(shown)
    )
    fitted, used = [], 0.0
    for tag in tags:
        tw = text_width(tag, 11) + 22
        if used + tw > 520:
            break
        fitted.append(tag)
        used += tw
    tag_row = esc("  ·  ".join(fitted))

    return f"""{svg_open(W, H, name)}
  <defs>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{top}"/><stop offset=".55" stop-color="{deep}"/><stop offset="1" stop-color="{deep}"/>
    </linearGradient>
    <linearGradient id="shaft" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#cfe9ff" stop-opacity=".13"/><stop offset="1" stop-color="#cfe9ff" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="ink" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c1}"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="{c3}"/>
      <animate attributeName="x1" values="-1;1" dur="7s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="0;2" dur="7s" repeatCount="indefinite"/>
    </linearGradient>
    <radialGradient id="lure">
      <stop offset="0" stop-color="#fff7c2" stop-opacity=".9"/><stop offset=".3" stop-color="#ffe066" stop-opacity=".35"/>
      <stop offset="1" stop-color="#ffe066" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="vignette" cx="50%" cy="45%" r="75%">
      <stop offset=".55" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".6"/>
    </radialGradient>
    <filter id="refract" x="-6%" y="-40%" width="112%" height="180%">
      <feTurbulence type="fractalNoise" baseFrequency=".012 .06" numOctaves="1" seed="{seed % 97}" result="n">
        <animate attributeName="baseFrequency" values=".012 .06;.02 .09;.012 .06" dur="9s" repeatCount="indefinite"/>
      </feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="n" scale="6" xChannelSelector="R" yChannelSelector="G" result="d"/>
      <feGaussianBlur in="d" stdDeviation="5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="d"/></feMerge>
    </filter>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>{"".join(defs)}
  </defs>
  <style>
    .shaft  {{ fill: url(#shaft); mix-blend-mode: screen; animation: shaft ease-in-out infinite alternate; }}
    @keyframes shaft {{ from {{ opacity: .25; }} to {{ opacity: 1; }} }}
    .snow   {{ fill: #dbeaff; animation: snow linear infinite; }}
    @keyframes snow {{ to {{ transform: translate(var(--sx), {H + 10}px); }} }}
    .glint  {{ animation: glint ease-in-out infinite; }}
    @keyframes glint {{ 0%, 100% {{ opacity: 0; }} 50% {{ opacity: .9; }} }}
    .tn     {{ fill: none; stroke: currentColor; stroke-width: 1.1; stroke-linecap: round; opacity: .6; }}
    .arm    {{ fill: none; stroke: #fff; stroke-width: 3.2; stroke-linecap: round; opacity: .32; }}
    .bell   {{ stroke: #fff; stroke-opacity: .55; stroke-width: .9; }}
    .inner  {{ fill: none; stroke: #fff; stroke-opacity: .28; stroke-width: .8; }}
    .organ  {{ fill: #fff; fill-opacity: .16; stroke: #fff; stroke-opacity: .6; stroke-width: 1; }}
    .shine  {{ fill: none; stroke: #fff; stroke-opacity: .7; stroke-width: 1.6; stroke-linecap: round; }}
    .halo   {{ animation: halo ease-in-out infinite; }}
    @keyframes halo {{ 0%, 100% {{ opacity: .55; }} 35% {{ opacity: 1; }} }}
    .fish   {{ fill: {dark}; animation: swim 48s linear infinite; }}
    @keyframes swim {{ from {{ transform: translate(420px, 10px); }} 70%, 100% {{ transform: translate(-{W - 140}px, -12px); }} }}
    .wiggle {{ transform-origin: 10px 0; animation: wiggle 2.4s ease-in-out infinite alternate; }}
    @keyframes wiggle {{ from {{ transform: rotate(-3deg); }} to {{ transform: rotate(3deg); }} }}
    .fin    {{ fill: #000; opacity: .35; }}
    .rod    {{ fill: none; stroke: {dark}; stroke-width: 1.6; stroke-linecap: round; }}
    .eye    {{ fill: #e9f4ff; opacity: .85; }}
    .bulb   {{ fill: #fffbe0; }}
    .lure   {{ animation: lure 2.2s ease-in-out infinite alternate; transform-box: fill-box; transform-origin: center; }}
    @keyframes lure {{ from {{ opacity: .45; transform: scale(.7); }} to {{ opacity: 1; transform: scale(1.1); }} }}
    .rise   {{ animation: rise linear infinite; }}
    @keyframes rise {{ to {{ transform: translateY(-{H + 30}px); }} }}
    .sway   {{ animation: sway ease-in-out infinite alternate; }}
    @keyframes sway {{ from {{ transform: translateX(-4px); }} to {{ transform: translateX(4px); }} }}
    .bubble {{ fill: #fff; fill-opacity: .06; stroke: #cfe9ff; stroke-opacity: .55; stroke-width: .8; }}
    .name   {{ font: 800 {name_fs:.1f}px {SANS}; fill: url(#ink); letter-spacing: 1.5px; }}
    .sub    {{ font: 500 14px {MONO}; fill: #b8cbe6; letter-spacing: 2.5px; }}
    .cyc    {{ animation: cyc {n * 4}s linear infinite; }}
    @keyframes cyc {{ 0% {{ opacity: 0; }} {slot * 0.12:.2f}%, {slot * 0.88:.2f}% {{ opacity: 1; }} {slot:.2f}%, 100% {{ opacity: 0; }} }}
    .tags   {{ font: 500 11px {MONO}; fill: #7f95b8; letter-spacing: 1.5px; opacity: .8; }}
    .gauge  {{ stroke: #9fb6d9; stroke-width: 1; opacity: .35; }}
    .depth  {{ font: 500 8px {MONO}; fill: #9fb6d9; opacity: .45; }}
    .mark   {{ fill: {c2}; animation: mark 13s ease-in-out infinite alternate; }}
    @keyframes mark {{ from {{ transform: translateY(-{(g1 - g0) * 0.3:.0f}px); }} to {{ transform: translateY({(g1 - g0) * 0.35:.0f}px); }} }}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="url(#water)"/>
    {"".join(shafts)}
    {"".join(snow)}
    {"".join(back_svg)}
    <g transform="translate(640 226)"><g class="fish"><g class="wiggle">{ANGLER}
    </g></g></g>
    <path d="{_ridge(rng, W, H, H - 20, 9)}" fill="{dark}"/>
    <path d="{_ridge(rng, W, H, H - 9, 5)}" fill="#000" opacity=".55"/>
    {"".join(plankton)}

    <text x="{cx}" y="{ty}" text-anchor="middle" class="name" filter="url(#refract)">{esc(name)}</text>
    {subs}
    <text x="{cx}" y="{H - 36}" text-anchor="middle" class="tags">{tag_row}</text>
    {"".join(front_svg)}
    {"".join(bubbles)}

    <g class="gauge">{ticks}<path d="M{gx} {g0} V{g1}"/></g>
    {labels}
    <g transform="translate(0 {(g0 + g1) / 2:.0f})"><path d="M{gx + 3} 0 l7 -4 v8Z" class="mark"/></g>
    <rect width="{W}" height="{H}" fill="url(#vignette)"/>
  </g>
</svg>
"""


STYLES = {"abyss": build_abyss}
