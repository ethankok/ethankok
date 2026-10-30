"""Generate the animated hero SVGs (light + dark).

A cursor glides in on a minimum-jerk path, overshoots and corrects, clicks,
then the headline types out with lognormal inter-key delays: the same motion
model the hackathon agent used to pass as a person.
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"

W, H = 860, 104
HEADLINE = "Hi, I'm Ethan. I love building with ML."
ACCENT_FROM = HEADLINE.index("love")

FONT_SIZE = 30
ADV = FONT_SIZE * 0.6  # monospace advance
X0, BASE = 40, 66
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "light": dict(text="#1f2328", muted="#59636e", accent="#534AB7", edge="#ffffff"),
    "dark": dict(text="#e6edf3", muted="#9198a1", accent="#AFA9EC", edge="#0d1117"),
}

START = (-24.0, 110.0)
TARGET = (X0 - 2.0, BASE - 26.0)  # where the click lands: just left of the first glyph
OVERSHOOT = (9.0, 4.0)
MOVE_S, CORRECT_S, CLICK_S, TYPE_START_S = 0.80, 0.22, 1.08, 1.40


def min_jerk(tau):
    return 10 * tau**3 - 15 * tau**4 + 6 * tau**5


def cursor_path():
    """(time, x, y) samples: main ballistic move with an arc, then a small correction."""
    pts = []
    ox, oy = TARGET[0] + OVERSHOOT[0], TARGET[1] + OVERSHOOT[1]
    for i in range(17):
        tau = i / 16
        s = min_jerk(tau)
        x = START[0] + (ox - START[0]) * s
        y = START[1] + (oy - START[1]) * s - 22 * math.sin(math.pi * s)
        pts.append((MOVE_S * tau, x, y))
    for i in range(1, 6):
        tau = i / 5
        s = min_jerk(tau)
        pts.append((MOVE_S + CORRECT_S * tau, ox + (TARGET[0] - ox) * s, oy + (TARGET[1] - oy) * s))
    return pts


def key_times():
    """Absolute time each character appears."""
    rng = random.Random(7)
    t, times = TYPE_START_S, []
    for i, ch in enumerate(HEADLINE):
        times.append(t)
        gap = rng.lognormvariate(math.log(0.105), 0.35)
        if ch == " ":
            gap *= 1.5
        elif ch in ",.":
            gap *= 2.6
        t += gap
    return times


def pct(t, total):
    return f"{100 * t / total:.2f}%"


def build(theme):
    c = THEMES[theme]
    path = cursor_path()
    times = key_times()
    type_end = times[-1] + 0.12
    n = len(HEADLINE)

    cur_total = TYPE_START_S
    cur_frames = "".join(
        f"{pct(t, cur_total)}{{transform:translate({x:.1f}px,{y:.1f}px);opacity:1}}" for t, x, y in path
    )
    cur_frames += f"{pct(CLICK_S + 0.2, cur_total)}{{opacity:1}}100%{{transform:translate({TARGET[0]}px,{TARGET[1]}px);opacity:0}}"

    caret_frames = "".join(
        f"{pct(t, type_end)}{{transform:translateX({-(n - i) * ADV + ADV:.1f}px)}}" for i, t in enumerate(times)
    )
    caret_frames = f"0%{{transform:translateX({-n * ADV:.1f}px)}}" + caret_frames + "100%{transform:none}"

    glyphs = []
    for i, ch in enumerate(HEADLINE):
        if ch == " ":
            continue
        esc = {"&": "&amp;", "<": "&lt;", "'": "&#39;"}.get(ch, ch)
        cls = "g a" if i >= ACCENT_FROM else "g"
        glyphs.append(
            f'<text class="{cls}" x="{X0 + i * ADV:.1f}" y="{BASE}" style="animation-delay:{times[i]:.3f}s">{esc}</text>'
        )

    caret_x = X0 + n * ADV + 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">{HEADLINE}</title>
<style>
.g{{font:500 {FONT_SIZE}px {MONO};fill:{c['text']}}}
.a{{fill:{c['accent']}}}
.caret{{fill:{c['accent']}}}
.cur{{opacity:0}}
.ring{{opacity:0;fill:none;stroke:{c['accent']};stroke-width:2;transform-box:fill-box;transform-origin:center}}
@media (prefers-reduced-motion:no-preference){{
.g{{animation:show .01s linear both}}
.cur{{animation:cur {cur_total}s linear both}}
.ring{{animation:ring .45s ease-out {CLICK_S}s both}}
.caret{{animation:caret {type_end:.3f}s linear both,blink 1.06s step-end {type_end:.3f}s 6}}
.caret-wrap{{animation:show .01s linear {TYPE_START_S}s both}}
}}
@keyframes show{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes ring{{0%{{opacity:.7;transform:scale(.2)}}100%{{opacity:0;transform:scale(1)}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes cur{{{cur_frames}}}
@keyframes caret{{{caret_frames.replace('}', ';animation-timing-function:steps(1,end)}')}}}
</style>
<circle class="ring" cx="{TARGET[0]}" cy="{TARGET[1]}" r="14"/>
{chr(10).join(glyphs)}
<g class="caret-wrap"><rect class="caret" x="{caret_x:.1f}" y="{BASE - 26}" width="3" height="32" rx="1"/></g>
<g class="cur"><path d="M0 0 L0 19 L4.6 14.6 L8 22 L11 20.7 L7.7 13.6 L14 13.6 Z" fill="{c['text']}" stroke="{c['edge']}" stroke-width="1.4" stroke-linejoin="round"/></g>
</svg>
"""


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        (OUT / f"hero-{theme}.svg").write_text(build(theme))
        print(f"wrote assets/hero-{theme}.svg")
