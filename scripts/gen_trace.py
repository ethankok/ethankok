#!/usr/bin/env python3
"""Generate the Nsight/NVTX-style "trace" row SVGs for the profile README.

Each row is a span bar plus a looping child-track scene that shows the
project in action. Stdlib only, deterministic. Writes into assets/trace/:
  {hackathon,til-ai,calorpie,carpark}-{light,dark}.svg
"""
import math
import random
from pathlib import Path

W = 860
ROW_H = 82
BAR_ZONE = 40          # the bar keeps its old 40px band; the scene sits below
SCENE_Y = 45
LABEL_X = 0
BAR_H = 22
BAR_RX = 4
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FS = 12.5
CHAR_W = 8.0           # generous per-char advance estimate (7.4 nominal + headroom for fallback mono fonts)
PAD_L = 12
PAD_R = 10
ARROW_W = 16           # room for the "→" glyph
GAP = 8                # between text and arrow
GROW_MS = 600
FADE_MS = 300

THEMES = {
    "light": {"muted": "#59636e", "page": "#ffffff", "alert": "#D8433B",
              "purple": ("#CECBF6", "#3C3489"), "teal": ("#9FE1CB", "#085041"),
              "coral": ("#F5C4B3", "#712B13"), "gray": ("#D3D1C7", "#444441")},
    "dark": {"muted": "#9198a1", "page": "#0d1117", "alert": "#F0847C",
             "purple": ("#3C3489", "#CECBF6"), "teal": ("#085041", "#9FE1CB"),
             "coral": ("#712B13", "#F5C4B3"), "gray": ("#444441", "#D3D1C7")},
}

# slug, label, bar text (two spaces between fn and metric), colour, start x, delay ms
ROWS = [
    ("hackathon", "NTU × STEng Hackathon", "pass_as_human()  office work that looks human in the logs", "purple", 180, 0),
    ("til-ai", "DSTA TIL-AI", "five_ml_services()  speech, vision, QA, RL, adversarial noise", "teal", 245, 150),
    ("calorpie", "Calorpie bot", "snap_to_kcal()  photo, text or voice → calories", "coral", 315, 300),
    ("carpark", "Carpark demand", "predict_parking_deserts()  1,982 HDB carparks", "gray", 385, 450),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def kf(name, total, stops):
    """@keyframes from (seconds, css) stops."""
    body = "".join(f"{100 * t / total:.2f}%{{{css}}}" for t, css in stops)
    return f"@keyframes {name}{{{body}}}"


def min_jerk(tau):
    return 10 * tau**3 - 15 * tau**4 + 6 * tau**5


# Each scene returns (base_css, motion_css, keyframes, markup).
# base_css is the still frame shown under prefers-reduced-motion.

def scene_cursor(x0, fill, ink, t):
    """Hackathon: a cursor arcs between spreadsheet cells on minimum-jerk paths and fills them."""
    cw, ch, cols, rows = 40, 13, 6, 2
    targets = [(0, 0), (2, 0), (1, 1), (4, 0), (3, 1), (5, 1)]
    widths = [22, 28, 18, 26, 20, 24]
    rest = (x0 + cols * cw + 14, SCENE_Y + 16)

    def tip(c, r):
        return (x0 + c * cw + 31, SCENE_Y + r * ch + 6)

    grid = [f'<rect x="{x0 + .5}" y="{SCENE_Y + .5}" width="{cols * cw}" height="{rows * ch}" rx="2" fill="none" stroke="{fill}"/>']
    grid.append(f'<path d="M{x0} {SCENE_Y + ch + .5}h{cols * cw}' + "".join(
        f'M{x0 + c * cw + .5} {SCENE_Y}v{rows * ch}' for c in range(1, cols)) + f'" stroke="{fill}" fill="none"/>')

    now, cur = 0.4, rest
    stops = [(0, cur), (now, cur)]
    typed = []
    for c, r in targets:
        dst = tip(c, r)
        for i in range(1, 9):
            s = min_jerk(i / 8)
            stops.append((now + 0.55 * i / 8,
                          (cur[0] + (dst[0] - cur[0]) * s,
                           cur[1] + (dst[1] - cur[1]) * s - 5 * math.sin(math.pi * s))))
        now += 0.55
        typed.append(now + 0.12)
        now += 0.6
        cur = dst
    fade = now + 0.9
    now = fade + 0.4
    for i in range(1, 9):
        s = min_jerk(i / 8)
        stops.append((now + 0.6 * i / 8, (cur[0] + (rest[0] - cur[0]) * s, cur[1] + (rest[1] - cur[1]) * s)))
    total = now + 0.6 + 0.3
    stops.append((total, rest))

    frames = [kf("cur", total, [(tt, f"transform:translate({x:.1f}px,{y:.1f}px)") for tt, (x, y) in stops])]
    base = f".cur{{transform:translate({rest[0]}px,{rest[1]}px)}}.in{{fill:{ink};transform-box:fill-box;transform-origin:0 50%}}"
    motion = f".cur{{animation:cur {total:.2f}s linear infinite}}"
    cells = []
    for i, ((c, r), w, ta) in enumerate(zip(targets, widths, typed)):
        on, off = "transform:scaleX(1);opacity:1", "transform:scaleX(1);opacity:0"
        frames.append(kf(f"in{i}", total, [(0, "transform:scaleX(0);opacity:1"), (ta, "transform:scaleX(0);opacity:1"),
                                           (ta + 0.35, on), (fade, on), (fade + 0.3, off), (total, off)]))
        motion += f".in{i}{{animation:in{i} {total:.2f}s linear infinite}}"
        cells.append(f'<rect class="in in{i}" x="{x0 + c * cw + 6}" y="{SCENE_Y + r * ch + 4}" width="{w}" height="5" rx="2"/>')
    arrow = (f'<g class="cur"><path transform="scale(.62)" d="M0 0 L0 19 L4.6 14.6 L8 22 L11 20.7 L7.7 13.6 L14 13.6 Z" '
             f'fill="{ink}" stroke="{t["page"]}" stroke-width="1.6" stroke-linejoin="round"/></g>')
    return base, motion, frames, "\n  ".join(grid + cells + [arrow])


def scene_bomber(x0, fill, ink, t):
    """TIL-AI: the game agent walks a Bomberman grid, bombs a crate and steps clear."""
    s, cols, rows, step = 10, 17, 3, 0.2
    crates = [(6, 0), (11, 2)]
    # waypoints the agent walks between; ("bomb", i) drops bomb i, ("wait", seconds) pauses
    script = [(5, 0), ("bomb", 0), (4, 0), (4, 2), ("wait", 0.9), (10, 2), ("bomb", 1),
              (8, 2), (8, 0), ("wait", 0.9), (16, 0)]
    fuse = 1.45

    def xy(c, r):
        return x0 + c * s, SCENE_Y + r * s

    now, pos = 0.5, (0, 0)
    stops = [(0, pos), (now, pos)]
    bombs = []
    for item in script:
        if item[0] == "bomb":
            bombs.append((pos, now))
        elif item[0] == "wait":
            now += item[1]
            stops.append((now, pos))
        else:
            now += step * (abs(item[0] - pos[0]) + abs(item[1] - pos[1]))
            pos = item
            stops.append((now, pos))
    gone = now + 0.5
    total = gone + 0.9

    frames = [kf("ag", total, [(tt, f"transform:translate({c * s}px,{r * s}px);opacity:1") for tt, (c, r) in stops]
                 + [(gone, f"transform:translate({pos[0] * s}px,{pos[1] * s}px);opacity:0"),
                    (total - 0.3, "transform:translate(0px,0px);opacity:0"), (total, "transform:translate(0px,0px);opacity:1")]),
              "@keyframes pulse{from{transform:scale(.75)}to{transform:scale(1.15)}}"]
    base = ".bomb,.flame{opacity:0}.pl{transform-box:fill-box;transform-origin:center}"
    motion = f".ag{{animation:ag {total:.2f}s linear infinite}}.pl{{animation:pulse .28s ease-in-out infinite alternate}}"

    bx, by = xy(0, 0)
    out = [f'<rect x="{bx - 1.5}" y="{by - 1.5}" width="{cols * s + 3}" height="{rows * s + 3}" rx="3" fill="none" stroke="{fill}"/>']
    for c in range(1, cols, 2):
        px, py = xy(c, 1)
        out.append(f'<rect x="{px + 1}" y="{py + 1}" width="8" height="8" rx="1.5" fill="{fill}"/>')
    for i, ((bc, br), drop) in enumerate(bombs):
        boom = drop + fuse
        cx, cy = xy(bc, br)
        frames.append(kf(f"b{i}", total, [(0, "opacity:0"), (drop, "opacity:1"), (boom, "opacity:0"), (total, "opacity:0")]))
        frames.append(kf(f"f{i}", total, [(0, "opacity:0"), (boom - 0.01, "opacity:0"), (boom + 0.06, "opacity:1"),
                                          (boom + 0.4, "opacity:0"), (total, "opacity:0")]))
        frames.append(kf(f"c{i}", total, [(0, "opacity:1"), (boom, "opacity:0"), (total - 0.3, "opacity:0"), (total, "opacity:1")]))
        motion += (f".b{i}{{animation:b{i} {total:.2f}s step-end infinite}}.f{i}{{animation:f{i} {total:.2f}s linear infinite}}"
                   f".c{i}{{animation:c{i} {total:.2f}s step-end infinite}}")
        kx, ky = xy(*crates[i])
        out.append(f'<rect class="c{i}" x="{kx + 1.5}" y="{ky + 1.5}" width="7" height="7" rx="1.5" fill="{fill}" stroke="{ink}" stroke-width="1.2"/>')
        out.append(f'<rect class="flame f{i}" x="{cx - 2 * s + 1}" y="{cy + 1.5}" width="{5 * s - 2}" height="7" rx="3.5" fill="{t["alert"]}"/>')
        out.append(f'<g class="bomb b{i}"><circle class="pl" cx="{cx + 5}" cy="{cy + 5}" r="3.2" fill="{ink}"/></g>')
    out.append(f'<rect class="ag" x="{bx + 1}" y="{by + 1}" width="8" height="8" rx="2.5" fill="{ink}"/>')
    return base, motion, frames, "\n  ".join(out)


def scene_inputs(x0, fill, ink, t):
    """Calorpie: a photo, a text bubble and a voice note each resolve to the same calorie ring."""
    y = SCENE_Y
    icon_x = [x0 + 2, x0 + 46, x0 + 90]
    ring_cx, ring_cy, rr = x0 + 172, y + 14, 10
    circ = 2 * math.pi * rr
    per, total = 2.1, 6.3
    st = f'fill="none" stroke="{ink}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
    icons = [
        f'<rect x="{icon_x[0]}" y="{y + 4}" width="26" height="20" rx="3" {st}/>'
        f'<circle cx="{icon_x[0] + 19}" cy="{y + 10}" r="2" fill="{ink}"/>'
        f'<path d="M{icon_x[0] + 3} {y + 21}l6-7 5 5 3-3 6 5" {st}/>',
        f'<path d="M{icon_x[1] + 3} {y + 5}h20a3 3 0 0 1 3 3v9a3 3 0 0 1-3 3h-13l-5 4v-4h-2a3 3 0 0 1-3-3v-9a3 3 0 0 1 3-3z" {st}/>'
        f'<path d="M{icon_x[1] + 6} {y + 10.5}h14M{icon_x[1] + 6} {y + 14.5}h9" {st}/>',
        "".join(f'<path d="M{icon_x[2] + 2 + i * 4} {y + 14 - h}v{2 * h}" {st}/>' for i, h in enumerate([3, 7, 4, 9, 5, 8, 2])),
    ]
    frames = [kf("sweep", per, [(0, f"stroke-dashoffset:{circ:.2f};opacity:1"), (0.85, f"stroke-dashoffset:{circ:.2f};opacity:1"),
                                (1.4, "stroke-dashoffset:0;opacity:1"), (1.85, "stroke-dashoffset:0;opacity:1"),
                                (2.05, "stroke-dashoffset:0;opacity:0"), (per, f"stroke-dashoffset:{circ:.2f};opacity:0")])]
    base = ".dot{opacity:0}"
    motion = f".ic{{opacity:.3}}.arc{{animation:sweep {per}s ease-in-out infinite}}"
    out = [f'<circle cx="{ring_cx}" cy="{ring_cy}" r="{rr}" fill="none" stroke="{fill}" stroke-width="4"/>',
           f'<circle class="arc" cx="{ring_cx}" cy="{ring_cy}" r="{rr}" fill="none" stroke="{ink}" stroke-width="4" stroke-linecap="round" '
           f'stroke-dasharray="{circ:.2f}" transform="rotate(-90 {ring_cx} {ring_cy})"/>']
    for i, ix in enumerate(icon_x):
        t0 = i * per
        dx = ring_cx - rr - 4 - (ix + 30)
        frames.append(kf(f"ic{i}", total, [(0, "opacity:.3"), (t0, "opacity:.3"), (t0 + 0.2, "opacity:1"),
                                           (t0 + per - 0.2, "opacity:1"), (min(t0 + per, total), "opacity:.3"), (total, "opacity:.3")]
                         if i else [(0, "opacity:1"), (per - 0.2, "opacity:1"), (per, "opacity:.3"), (total - 0.2, "opacity:.3"), (total, "opacity:1")]))
        frames.append(kf(f"d{i}", total, [(0, "opacity:0;transform:translateX(0px)"), (t0 + 0.3, "opacity:0;transform:translateX(0px)"),
                                          (t0 + 0.36, "opacity:1;transform:translateX(0px)"), (t0 + 0.85, f"opacity:1;transform:translateX({dx}px)"),
                                          (t0 + 0.9, f"opacity:0;transform:translateX({dx}px)"), (total, "opacity:0;transform:translateX(0px)")]))
        motion += f".ic{i}{{animation:ic{i} {total}s linear infinite}}.d{i}{{animation:d{i} {total}s ease-in-out infinite}}"
        out.append(f'<g class="ic ic{i}">{icons[i]}</g>')
        out.append(f'<circle class="dot d{i}" cx="{ix + 30}" cy="{ring_cy}" r="2.2" fill="{ink}"/>')
    return base, motion, frames, "\n  ".join(out)


def scene_lots(x0, fill, ink, t):
    """Carpark: lots fill one by one and the carpark turns red once it is 90% full."""
    cols, rows, lw, lh, gap = 24, 3, 7, 8, 2
    n = cols * rows
    order = list(range(n))
    random.Random(21).shuffle(order)
    threshold = math.ceil(0.9 * n)       # 65 of 72
    filled = threshold + 3
    t_in = [0.5 + i * 0.075 for i in range(filled)]
    t_red = t_in[threshold - 1]
    reset = t_in[-1] + 1.8
    total = reset + 0.7
    frames, motion, out = [], "", []
    rank = {lot: i for i, lot in enumerate(order)}
    for lot in range(n):
        c, r = lot % cols, lot // cols
        i = rank[lot]
        cls = ""
        if i < filled:
            stops = [(0, f"fill:{fill}")]
            if t_in[i] < t_red:
                stops += [(t_in[i], f"fill:{ink}")]
            stops += [(max(t_in[i], t_red), f"fill:{t['alert']}"), (reset, f"fill:{fill}"), (total, f"fill:{fill}")]
            frames.append(kf(f"l{i}", total, stops))
            motion += f".l{i}{{animation:l{i} {total:.2f}s step-end infinite}}"
            cls = f' class="l{i}"'
        colour = ink if i < threshold - 8 else fill
        out.append(f'<rect{cls} x="{x0 + c * (lw + gap)}" y="{SCENE_Y + 1 + r * (lh + gap)}" width="{lw}" height="{lh}" rx="1.5" fill="{colour}"/>')
    return "", motion, frames, "\n  ".join(out)


SCENES = {"hackathon": scene_cursor, "til-ai": scene_bomber, "calorpie": scene_inputs, "carpark": scene_lots}


def row_svg(theme, slug, label, text, colour, x0, delay):
    t = THEMES[theme]
    fill, ink = t[colour]
    text_w = len(text) * CHAR_W
    bar_w = round(PAD_L + text_w + GAP + ARROW_W + PAD_R)
    assert x0 + bar_w <= W - 4, (label, x0 + bar_w)
    bar_y = (BAR_ZONE - BAR_H) // 2
    base_y = bar_y + BAR_H / 2 + 4.2  # optical baseline centre for 12.5px
    tx = x0 + PAD_L
    ax = x0 + bar_w - PAD_R - ARROW_W + 2
    fade_delay = delay + GROW_MS
    base, motion, frames, scene = SCENES[slug](x0, fill, ink, t)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{ROW_H}" viewBox="0 0 {W} {ROW_H}" role="img" aria-label="{esc(label)}: {esc(text)}">
  <style>
    .lbl {{ font: 12px {FONT}; fill: {t["muted"]}; }}
    .bar {{ fill: {fill}; transform-box: fill-box; transform-origin: 0 50%; }}
    .txt {{ font: 400 {FS}px {FONT}; fill: {ink}; white-space: pre; }}
    .arr {{ font: 600 {FS}px {FONT}; fill: {ink}; }}
    {base}
    @media (prefers-reduced-motion: no-preference) {{
      .bar {{ animation: grow {GROW_MS}ms cubic-bezier(.2,.7,.2,1) {delay}ms both; }}
      .txt, .arr {{ animation: fade {FADE_MS}ms ease-out {fade_delay}ms both; }}
      {motion}
    }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
    {chr(10).join("    " + f for f in frames).strip()}
  </style>
  <text class="lbl" x="{LABEL_X}" y="{base_y:.1f}">{esc(label)}</text>
  <rect class="bar" x="{x0}" y="{bar_y}" width="{bar_w}" height="{BAR_H}" rx="{BAR_RX}"/>
  <text class="txt" x="{tx}" y="{base_y:.1f}" xml:space="preserve">{esc(text)}</text>
  <text class="arr" x="{ax}" y="{base_y:.1f}">→</text>
  {scene}
</svg>
'''


def main():
    out = Path(__file__).resolve().parent.parent / "assets" / "trace"
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        for slug, label, text, colour, x0, delay in ROWS:
            (out / f"{slug}-{theme}.svg").write_text(
                row_svg(theme, slug, label, text, colour, x0, delay), encoding="utf-8")
    print(f"wrote {len(list(out.glob('*.svg')))} SVGs to {out}")


if __name__ == "__main__":
    main()
