#!/usr/bin/env python3
"""Generate the Nsight/NVTX-style "trace" row SVGs for the profile README.

Stdlib only, deterministic. Writes into assets/trace/:
  {hackathon,til-ai,calorpie,carpark}-{light,dark}.svg
"""
from pathlib import Path

W = 860
ROW_H = 40
LABEL_X = 0
TRACK_X = 180          # where the timeline starts (after the label column)
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
    "light": {"muted": "#59636e",
              "purple": ("#CECBF6", "#3C3489"), "teal": ("#9FE1CB", "#085041"),
              "coral": ("#F5C4B3", "#712B13"), "gray": ("#D3D1C7", "#444441")},
    "dark": {"muted": "#9198a1",
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


def row_svg(theme, label, text, colour, x0, delay):
    t = THEMES[theme]
    fill, ink = t[colour]
    text_w = len(text) * CHAR_W
    bar_w = round(PAD_L + text_w + GAP + ARROW_W + PAD_R)
    assert x0 + bar_w <= W - 4, (label, x0 + bar_w)
    bar_y = (ROW_H - BAR_H) // 2
    base_y = bar_y + BAR_H / 2 + 4.2  # optical baseline centre for 12.5px
    tx = x0 + PAD_L
    ax = x0 + bar_w - PAD_R - ARROW_W + 2
    fade_delay = delay + GROW_MS
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{ROW_H}" viewBox="0 0 {W} {ROW_H}" role="img" aria-label="{esc(label)}: {esc(text)}">
  <style>
    .lbl {{ font: 12px {FONT}; fill: {t["muted"]}; }}
    .bar {{ fill: {fill}; transform-box: fill-box; transform-origin: 0 50%; }}
    .txt {{ font: 400 {FS}px {FONT}; fill: {ink}; white-space: pre; }}
    .arr {{ font: 600 {FS}px {FONT}; fill: {ink}; }}
    @media (prefers-reduced-motion: no-preference) {{
      .bar {{ animation: grow {GROW_MS}ms cubic-bezier(.2,.7,.2,1) {delay}ms both; }}
      .txt, .arr {{ animation: fade {FADE_MS}ms ease-out {fade_delay}ms both; }}
    }}
    @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes fade {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  </style>
  <text class="lbl" x="{LABEL_X}" y="{base_y:.1f}">{esc(label)}</text>
  <rect class="bar" x="{x0}" y="{bar_y}" width="{bar_w}" height="{BAR_H}" rx="{BAR_RX}"/>
  <text class="txt" x="{tx}" y="{base_y:.1f}" xml:space="preserve">{esc(text)}</text>
  <text class="arr" x="{ax}" y="{base_y:.1f}">→</text>
</svg>
'''


def main():
    out = Path(__file__).resolve().parent.parent / "assets" / "trace"
    out.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        for slug, label, text, colour, x0, delay in ROWS:
            (out / f"{slug}-{theme}.svg").write_text(
                row_svg(theme, label, text, colour, x0, delay), encoding="utf-8")
    print(f"wrote {len(list(out.glob('*.svg')))} SVGs to {out}")


if __name__ == "__main__":
    main()
