#!/usr/bin/env python3
"""Fetch HDB carpark availability, track share of carparks >=90% full, render SVG cards.

Stdlib only. On any API failure the previous data/SVGs are kept and the script exits 0.
Endpoint: https://api.data.gov.sg/v1/transport/carpark-availability (no key needed).
"""
import json
import sys
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "carpark.json"
ASSETS = ROOT / "assets"
URL = "https://api.data.gov.sg/v1/transport/carpark-availability"
KEEP = 24
THRESHOLD = 0.90
SGT = timezone(timedelta(hours=8))

THEMES = {
    "light": {"text": "#1f2328", "muted": "#59636e", "line": "#1D9E75"},
    "dark": {"text": "#e6edf3", "muted": "#9198a1", "line": "#5DCAA5"},
}


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "ethankok-profile-readme"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def compute(payload):
    item = payload["items"][0]
    total = full = 0
    for cp in item["carpark_data"]:
        for info in cp["carpark_info"]:
            if info.get("lot_type") != "C":
                continue
            lots = int(info["total_lots"])
            if lots <= 0:
                continue
            avail = int(info["lots_available"])
            total += 1
            if 1 - avail / lots >= THRESHOLD:
                full += 1
    if total == 0:
        raise ValueError("no lot_type C carparks in response")
    return item["timestamp"], round(100 * full / total, 1)


def load_history():
    try:
        h = json.loads(DATA.read_text())
        return [e for e in h if "t" in e and "pct" in e]
    except Exception:
        return []


def fmt(p):
    return f"{p:.1f}%".replace(".0%", "%") if p != int(p) else f"{int(p)}%"


def sparkline(points, x0, x1, y0, y1):
    """Return (path_d or None, dot (x,y), n)."""
    n = len(points)
    lo, hi = min(points), max(points)
    span = max(hi - lo, 2.0)
    mid = (hi + lo) / 2
    lo, hi = mid - span / 2, mid + span / 2

    def y(v):
        return y1 - (v - lo) / (hi - lo) * (y1 - y0)

    if n == 1:
        return None, ((x0 + x1) / 2, y(points[0])), 1
    xs = [x0 + i * (x1 - x0) / (n - 1) for i in range(n)]
    d = " ".join(("M" if i == 0 else "L") + f"{xs[i]:.1f},{y(points[i]):.1f}" for i in range(n))
    return d, (xs[-1], y(points[-1])), n


def render(theme, history):
    c = THEMES[theme]
    pts = [e["pct"] for e in history[-KEEP:]]
    cur = pts[-1]
    d, (dx, dy), n = sparkline(pts, 236, 400, 42, 92)
    line = ""
    if d:
        line = (f'<path class="spark" d="{d}" pathLength="1" fill="none" stroke="{c["line"]}" '
                f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="420" height="100" viewBox="0 0 420 100" role="img" aria-label="{fmt(cur)} of HDB carparks at least 90% full right now">
  <style>
    .lbl {{ font: 500 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: {c["muted"]}; }}
    .big {{ font: 700 46px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: {c["text"]}; }}
    .spark {{ stroke-dasharray: 1; stroke-dashoffset: 0; }}
    .dot {{ opacity: 1; }}
    @media (prefers-reduced-motion: no-preference) {{
      .spark {{ animation: draw 1.6s ease-out 0.2s both; }}
      .dot {{ animation: pop 0.4s ease-out 1.7s both; }}
    }}
    @keyframes draw {{ from {{ stroke-dashoffset: 1; }} to {{ stroke-dashoffset: 0; }} }}
    @keyframes pop {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
  </style>
  <text class="lbl" x="16" y="24">HDB carparks &#8805;90% full right now</text>
  <text class="big" x="16" y="78">{fmt(cur)}</text>
  {line}
  <circle class="dot" cx="{dx:.1f}" cy="{dy:.1f}" r="3.5" fill="{c["line"]}"/>
</svg>
'''


def main():
    try:
        ts, pct = compute(fetch())
    except Exception as e:
        print(f"carpark: fetch failed ({e!r}); keeping previous data", file=sys.stderr)
        return 0
    hist = load_history()
    entry = {"t": ts, "pct": pct}
    if hist and hist[-1]["t"] == ts:
        hist[-1] = entry
    else:
        hist.append(entry)
    hist = hist[-KEEP:]
    DATA.parent.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(hist, indent=1) + "\n")
    ASSETS.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        (ASSETS / f"carpark-{theme}.svg").write_text(render(theme, hist))
    print(f"carpark: {pct}% ({len(hist)} points) at {ts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
