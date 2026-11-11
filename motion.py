"""Motion-graphics banner: a looping flat-design title sequence.

Colour bars wipe the screen, the name slides up letter by letter out of a mask, geometric shapes
pop in around it, block wipes swap the subtitle lines, tag chips bounce in, and an iris wipe closes
the loop. Everything is driven by CSS keyframes that share one timeline, so the piece stays in sync.

Same contract as creative.py: (name, lines, tags, theme, seed) -> svg string.
"""

from __future__ import annotations

import random

from common import MONO, THEMES, esc
from creative import reduced, svg_open

T = 12.0  # seconds per loop
PAPER = "#f6f1e7"

OUT = "cubic-bezier(.16,1,.3,1)"
IN = "cubic-bezier(.7,0,.84,0)"
IO = "cubic-bezier(.76,0,.24,1)"
BACK = "cubic-bezier(.34,1.56,.64,1)"

# shared beats of the timeline (seconds)
T_IN = 1.5     # content starts entering
T_OUT = 10.0   # content starts leaving


def _kf(name: str, steps: list[tuple]) -> str:
    """@keyframes from (time, css[, easing towards the next step]) tuples on the shared timeline."""
    steps = list(steps)
    if steps[0][0] > 0:
        steps.insert(0, (0, steps[0][1]))
    if steps[-1][0] < T:
        steps.append((T, steps[-1][1]))
    body = []
    for t, css, *ease in steps:
        timing = f" animation-timing-function: {ease[0]};" if ease else ""
        body.append(f"{t / T * 100:.2f}% {{ {css};{timing} }}")
    return f"@keyframes {name} {{ {' '.join(body)} }}"


def _lag(seconds: float) -> str:
    """Inline style that makes an element run the shared timeline `seconds` late."""
    return f'style="--d:{seconds:.2f}s"'


def build_motion(name: str, lines: list[str], tags: list[str], theme: str, seed: int) -> str:
    """Flat motion-graphics title sequence that loops every 12 seconds."""
    W, H = 900, 300
    rng = random.Random(seed)
    ink, (c1, c2, c3) = THEMES.get(theme, THEMES["aurora"])
    cx = W / 2

    # ---- name: one <text> per letter on a monospace grid, revealed from a clip mask
    fs = min(76.0, 640 / (max(1, len(name)) * 0.6))
    cell = fs * 0.6
    base_y = 152
    x0 = cx - cell * len(name) / 2
    last_word = len(name) - len(name.split(" ")[-1]) if " " in name.strip() else len(name)
    letters = "".join(
        f'<text x="{x0 + cell * (i + 0.5):.1f}" y="{base_y}" text-anchor="middle" '
        f'class="a letter{" hl" if i >= last_word else ""}" {_lag(i * 0.05)}>{esc(ch)}</text>'
        for i, ch in enumerate(name) if ch != " "
    )
    mark_w = cell * (len(name) - last_word) + 10 if last_word < len(name) else cell * len(name) + 10
    mark_x = x0 + cell * last_word - 5 if last_word < len(name) else x0 - 5

    # ---- subtitle lines swapped by block wipes
    shown = [s for s in lines[:3] if s] or [""]
    n = len(shown)
    sub_fs = 18
    sub_w = max(len(s) for s in shown) * sub_fs * 0.6 + 20
    sub_y = base_y + 46
    first_wipe = 2.6
    spacing = (T_OUT - first_wipe) / n
    hidden = ' opacity="0"'
    subs = "".join(
        f'<text x="{cx}" y="{sub_y}" text-anchor="middle" class="a sub" {_lag(i * spacing)}'
        f'{hidden if i else ""}>{esc(s)}</text>'
        for i, s in enumerate(shown)
    )
    blocks = "".join(
        f'<rect x="{cx - sub_w / 2:.1f}" y="{sub_y - 20}" width="{sub_w:.1f}" height="29" fill="{[c1, c2, c3][k % 3]}" '
        f'class="a block" {_lag(k * spacing)}/>'
        for k in range(n + 1)
    )

    # ---- tag chips
    chips, chip_w = [], []
    for tag in tags:
        w = len(tag) * 12 * 0.6 + 24
        if sum(chip_w) + w + 8 * len(chip_w) > 640:
            break
        chip_w.append(w)
    x = cx - (sum(chip_w) + 8 * (len(chip_w) - 1)) / 2
    for i, (tag, w) in enumerate(zip(tags, chip_w)):
        col = [c1, c2, c3][i % 3]
        solid = i % 2 == 0
        chips.append(
            f'<g class="a c chip" {_lag(i * 0.07)}>'
            f'<rect x="{x:.1f}" y="226" width="{w:.1f}" height="26" rx="13" fill="{col if solid else PAPER}" '
            f'stroke="{col if solid else ink}" stroke-width="2"/>'
            f'<text x="{x + w / 2:.1f}" y="243.5" text-anchor="middle" class="tag" fill="{ink}">{esc(tag)}</text></g>'
        )
        x += w + 8

    # ---- decorative shapes
    dots = "".join(
        f'<circle cx="{776 + c * 18}" cy="{32 + r * 18}" r="2.6" class="a c dot" {_lag((r + c) * 0.06 + rng.uniform(0, 0.05))}/>'
        for r in range(4) for c in range(4)
    )
    confetti = "".join(
        # the rotation lives on a wrapper: an animated CSS transform would replace it on the rect itself
        f'<g transform="rotate({rot} {px + w / 2} {py + 3})"><rect x="{px}" y="{py}" width="{w}" height="6" rx="3" '
        f'fill="{col}" class="a c dot" {_lag(lag)}/></g>'
        for px, py, w, rot, col, lag in [(232, 34, 46, -18, c2, .3), (604, 262, 34, 24, c1, .45), (318, 268, 22, -32, c3, .55),
                                         (560, 30, 18, 40, c3, .2)]
    )
    bars = "".join(
        f'<rect x="{i * 150}" width="151" height="{H}" fill="{[c1, c2, c3, ink][i % 4]}" class="a bar" {_lag(i * 0.07)}/>'
        for i in range(6)
    )

    hold = T_OUT - T_IN
    keyframes = "\n    ".join([
        _kf("bar", [(0.15, f"transform: translateY({H}px)", OUT), (0.65, "transform: translateY(0)"),
                    (1.1, "transform: translateY(0)", IO), (1.65, f"transform: translateY(-{H}px)")]),
        _kf("iris", [(0, "transform: scale(1)"), (1.05, "transform: scale(1)"), (1.06, "transform: scale(0)"),
                     (10.95, "transform: scale(0)", IO), (11.65, "transform: scale(1)")]),
        _kf("letter", [(T_IN, f"transform: translateY({fs * 1.25:.0f}px)", OUT), (T_IN + 0.8, "transform: translateY(0)"),
                       (6.2, "transform: translateY(0)", OUT), (6.42, "transform: translateY(-12px)", "ease-in"),
                       (6.7, "transform: translateY(0)"),
                       (T_OUT + 0.1, "transform: translateY(0)", IN), (T_OUT + 0.6, f"transform: translateY(-{fs * 1.25:.0f}px)")]),
        _kf("mark", [(2.2, "transform: scaleX(0)", OUT), (2.9, "transform: scaleX(1)"),
                     (T_OUT, "transform: scaleX(1)", IN), (T_OUT + 0.45, "transform: scaleX(0)")]),
        _kf("block", [(first_wipe, f"transform: translateX(-{sub_w + 2:.0f}px)", OUT), (first_wipe + 0.38, "transform: translateX(0)", IN),
                      (first_wipe + 0.76, f"transform: translateX({sub_w + 2:.0f}px)")]),
        _kf("sub", [(first_wipe + 0.37, "opacity: 0"), (first_wipe + 0.38, "opacity: 1"),
                    (first_wipe + 0.37 + spacing, "opacity: 1"), (first_wipe + 0.38 + spacing, "opacity: 0")]),
        _kf("chip", [(3.2, "transform: scale(0)", BACK), (3.65, "transform: scale(1)"),
                     (8.0, "transform: scale(1)", OUT), (8.18, "transform: scale(1.14)", "ease-in-out"),
                     (8.45, "transform: scale(1)"),
                     (T_OUT - 0.1, "transform: scale(1)", IN), (T_OUT + 0.25, "transform: scale(0)")]),
        _kf("dot", [(1.9, "transform: scale(0)", BACK), (2.3, "transform: scale(1)"),
                    (T_OUT, "transform: scale(1)", IN), (T_OUT + 0.3, "transform: scale(0)")]),
        _kf("ring", [(1.6, "stroke-dashoffset: 75; transform: rotate(-90deg)", OUT),
                     (2.5, "stroke-dashoffset: 0; transform: rotate(0deg)"),
                     (T_OUT, "stroke-dashoffset: 0; transform: rotate(230deg)", IN),
                     (T_OUT + 0.5, "stroke-dashoffset: -100; transform: rotate(300deg)")]),
        _kf("tri", [(1.8, "transform: scale(0) rotate(-200deg)", OUT), (2.6, "transform: scale(1) rotate(0deg)"),
                    (T_OUT, "transform: scale(1) rotate(240deg)", IN), (T_OUT + 0.4, "transform: scale(0) rotate(360deg)")]),
        _kf("plus", [(2.0, "transform: scale(0) rotate(-180deg)", BACK), (2.6, "transform: scale(1) rotate(0deg)"),
                     (T_OUT, "transform: scale(1) rotate(270deg)", IN), (T_OUT + 0.35, "transform: scale(0) rotate(360deg)")]),
        _kf("ball", [(1.7, "transform: translateY(-90px)", "cubic-bezier(.5,0,1,.5)"), (2.05, "transform: translateY(0)", OUT),
                     (2.35, "transform: translateY(-26px)", "cubic-bezier(.5,0,1,.5)"), (2.6, "transform: translateY(0)", OUT),
                     (2.75, "transform: translateY(-8px)", "cubic-bezier(.5,0,1,.5)"), (2.88, "transform: translateY(0)"),
                     *[(T_IN + hold * k / 6, f"transform: translateY({-6 if k % 2 else 0}px)", "ease-in-out") for k in range(2, 6)],
                     (T_OUT, "transform: translateY(0)", IN), (T_OUT + 0.4, "transform: translateY(-90px)")]),
        _kf("draw", [(2.1, "stroke-dashoffset: 100", IO), (2.9, "stroke-dashoffset: 0"),
                     (T_OUT, "stroke-dashoffset: 0", IN), (T_OUT + 0.4, "stroke-dashoffset: -100")]),
        _kf("half", [(1.7, "transform: translateX(60px)", OUT), (2.4, "transform: translateX(0)"),
                     (T_OUT, "transform: translateX(0)", IN), (T_OUT + 0.4, "transform: translateX(60px)")]),
        _kf("prog", [(T_IN, "transform: scaleX(0)"), (T_OUT + 0.6, "transform: scaleX(1)"),
                     (T_OUT + 0.9, "transform: scaleX(1); opacity: 1"), (T_OUT + 0.95, "transform: scaleX(1); opacity: 0")]),
    ])

    return f"""{svg_open(W, H, name)}
  <defs>
    <clipPath id="frame"><rect width="{W}" height="{H}" rx="16"/></clipPath>
    <clipPath id="nameMask"><rect x="0" y="{base_y - fs * 0.98:.1f}" width="{W}" height="{fs * 1.26:.1f}"/></clipPath>
    <clipPath id="subMask"><rect x="{cx - sub_w / 2:.1f}" y="{sub_y - 20}" width="{sub_w:.1f}" height="29"/></clipPath>
  </defs>
  <style>
    .a      {{ animation: {T:g}s linear infinite; animation-delay: calc(var(--d, 0s) - {T:g}s); }}
    .c      {{ transform-box: fill-box; transform-origin: center; }}
    .bar    {{ animation-name: bar; transform: translateY({H}px); }}
    .iris   {{ animation-name: iris; transform: scale(0); transform-origin: {cx}px {H / 2}px; }}
    .letter {{ animation-name: letter; font: 800 {fs:.1f}px {MONO}; fill: {ink}; }}
    .hl     {{ fill: {c1}; }}
    .mark   {{ animation-name: mark; transform-box: fill-box; transform-origin: left center; }}
    .block  {{ animation-name: block; transform: translateX(-{sub_w + 2:.0f}px); }}
    .sub    {{ animation-name: sub; font: 600 {sub_fs}px {MONO}; fill: {ink}; }}
    .chip   {{ animation-name: chip; }}
    .tag    {{ font: 700 12px {MONO}; }}
    .dot    {{ animation-name: dot; }}
    .ring   {{ animation-name: ring; fill: none; stroke: {c1}; stroke-width: 10; stroke-linecap: round; stroke-dasharray: 75 100; }}
    .tri    {{ animation-name: tri; }}
    .plus   {{ animation-name: plus; fill: none; stroke: {ink}; stroke-width: 6; stroke-linecap: round; }}
    .ball   {{ animation-name: ball; }}
    .draw   {{ animation-name: draw; fill: none; stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 100 100; }}
    .half   {{ animation-name: half; }}
    .prog   {{ animation-name: prog; transform-origin: 0 0; }}
    {keyframes}
    {reduced()}
  </style>
  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{PAPER}"/>

    <circle cx="88" cy="78" r="30" pathLength="100" class="a c ring"/>
    <circle cx="700" cy="56" r="13" fill="{c3}" class="a ball"/>
    <path d="M822 190 L850 238 L794 238Z" fill="{c2}" class="a c tri"/>
    <path d="M60 212 V244 M44 228 H76" class="a c plus"/>
    <path d="M34 152 q10 -16 20 0 t20 0 t20 0 t20 0" pathLength="100" stroke="{c2}" class="a draw"/>
    <circle cx="{W}" cy="128" r="38" fill="{c1}" class="a half"/>
    <g fill="{ink}">{dots}</g>
    {confetti}

    <rect x="{mark_x:.1f}" y="{base_y - fs * 0.2:.1f}" width="{mark_w:.1f}" height="{fs * 0.3:.1f}" fill="{c2}" opacity=".45" class="a mark"/>
    <g clip-path="url(#nameMask)">{letters}</g>
    <g clip-path="url(#subMask)">{subs}{blocks}</g>
    {"".join(chips)}

    <rect y="{H - 5}" width="{W}" height="5" fill="{c1}" class="a prog"/>

    <circle cx="{cx}" cy="{H / 2}" r="480" fill="{c1}" class="a iris" {_lag(-0.16)}/>
    <circle cx="{cx}" cy="{H / 2}" r="480" fill="{ink}" class="a iris"/>
    {bars}
  </g>
</svg>
"""


STYLES = {"motion": build_motion}
