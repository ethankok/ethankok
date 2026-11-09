#!/usr/bin/env python3
"""Generate the contribution-graph agent SVGs (light + dark).

The last year of contributions is the map. An agent repeatedly runs Dijkstra
to the nearest remaining contribution cell, shows the planned route, walks it
and clears the cell, then the graph resets and the loop restarts.

Stdlib only. With GH_TOKEN or GITHUB_TOKEN set it refreshes data/contrib.json
from the GraphQL API first; otherwise it renders from the cached file.
"""
import heapq
import json
import os
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contrib.json"
OUT = ROOT / "assets"
LOGIN = "ethankok"

W, CELL, PITCH, ROWS = 860, 11, 14, 7
PAD_Y = 6
STEP_S = 0.085          # seconds per cell walked
PAUSE_S = 0.12          # beat on each cleared cell
LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

THEMES = {
    "light": dict(ramp=["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"], agent="#534AB7", edge="#ffffff"),
    "dark": dict(ramp=["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"], agent="#AFA9EC", edge="#0d1117"),
}

QUERY = ("query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{"
         "weeks{contributionDays{date contributionLevel}}}}}}")


def fetch(token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [[[d["date"], LEVELS[d["contributionLevel"]]] for d in w["contributionDays"]] for w in weeks]


def load():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        weeks = fetch(token)
        DATA.write_text(json.dumps(weeks, separators=(",", ":")) + "\n")
        return weeks
    return json.loads(DATA.read_text())


def grid(weeks):
    """{(col, row): level}; row 0 is Sunday, like the profile graph."""
    cells = {}
    for col, week in enumerate(weeks):
        for day, level in week:
            cells[(col, (date.fromisoformat(day).weekday() + 1) % 7)] = level
    return cells


def dijkstra(src, targets, cols):
    """Shortest 4-connected route from src to the nearest target, as a list of cells."""
    dist, prev, heap = {src: 0}, {}, [(0, src)]
    while heap:
        d, cur = heapq.heappop(heap)
        if d > dist[cur]:
            continue
        if cur in targets:
            route = [cur]
            while route[-1] != src:
                route.append(prev[route[-1]])
            return route[::-1]
        c, r = cur
        for nxt in ((c + 1, r), (c, r + 1), (c, r - 1), (c - 1, r)):
            if -1 <= nxt[0] <= cols and 0 <= nxt[1] < ROWS and d + 1 < dist.get(nxt, 1e9):
                dist[nxt], prev[nxt] = d + 1, cur
                heapq.heappush(heap, (d + 1, nxt))
    raise ValueError("unreachable target")


def plan(cells, cols):
    """Returns (stops, eaten, legs, total): agent (t, cell) stops, {cell: t}, [(t0, t1, route)], loop length."""
    start, end = (-1, 3), (cols, 3)
    targets = {c for c, lvl in cells.items() if lvl}
    now, cur = 0.6, start
    stops, eaten, legs = [(0, start), (now, start)], {}, []
    while targets or cur != end:
        route = dijkstra(cur, targets or {end}, cols)
        t0 = now
        for a, b, nxt in zip(route, route[1:], route[2:] + [None]):
            now += STEP_S
            if nxt is None or (b[0] - a[0], b[1] - a[1]) != (nxt[0] - b[0], nxt[1] - b[1]):
                stops.append((now, b))          # only corners and arrivals need a keyframe
        legs.append((t0, now, route))
        cur = route[-1]
        if cur in targets:
            targets.discard(cur)
            eaten[cur] = now
            now += PAUSE_S
            stops.append((now, cur))
    return stops, eaten, legs, now + 1.6


def build(theme, cells, cols):
    c = THEMES[theme]
    stops, eaten, legs, total = plan(cells, cols)
    x0 = (W - (cols * PITCH - (PITCH - CELL))) / 2
    height = PAD_Y * 2 + ROWS * PITCH - (PITCH - CELL)

    def xy(cell):
        return x0 + cell[0] * PITCH, PAD_Y + cell[1] * PITCH

    def pct(t):
        return f"{100 * t / total:.3f}%"

    sx, sy = xy(stops[0][1])
    ag = "".join(f"{pct(t)}{{transform:translate({xy(p)[0] - sx:.1f}px,{xy(p)[1] - sy:.1f}px);opacity:1}}" for t, p in stops)
    ex, ey = xy(stops[-1][1])
    ag += (f"{pct(stops[-1][0] + 0.4)}{{transform:translate({ex - sx:.1f}px,{ey - sy:.1f}px);opacity:0}}"
           f"{pct(total - 0.5)}{{transform:none;opacity:0}}100%{{transform:none;opacity:1}}")
    frames = [f"@keyframes ag{{{ag}}}"]
    motion = [f".ag{{animation:ag {total:.2f}s linear infinite}}"]
    marks = []

    for (col, row), level in sorted(cells.items()):
        x, y = xy((col, row))
        marks.append(f'<rect x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{c["ramp"][0]}"/>')
    for i, (cell, t) in enumerate(sorted(eaten.items(), key=lambda kv: kv[1])):
        x, y = xy(cell)
        frames.append(f"@keyframes e{i}{{0%,{pct(t)}{{opacity:1}}{pct(t + 0.08)},{pct(total - 0.6)}{{opacity:0}}100%{{opacity:1}}}}")
        motion.append(f".e{i}{{animation:e{i} {total:.2f}s linear infinite}}")
        marks.append(f'<rect class="e{i}" x="{x:.1f}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{c["ramp"][cells[cell]]}"/>')
    for i, (t0, t1, route) in enumerate(legs):
        if len(route) < 4:
            continue
        pts = " ".join(f"{xy(p)[0] + CELL / 2:.1f},{xy(p)[1] + CELL / 2:.1f}" for p in route)
        frames.append(f"@keyframes p{i}{{0%{{opacity:0}}{pct(t0)}{{opacity:.75}}{pct(t1)},100%{{opacity:0}}}}")
        motion.append(f".p{i}{{animation:p{i} {total:.2f}s step-end infinite}}")
        marks.append(f'<polyline class="plan p{i}" points="{pts}"/>')

    nl = "\n"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{height}" viewBox="0 0 {W} {height}" role="img" aria-labelledby="t">
<title id="t">Contribution graph of the last year, with an agent planning shortest paths across it</title>
<style>
.plan{{opacity:0;fill:none;stroke:{c['agent']};stroke-width:1.5;stroke-dasharray:2 3;stroke-linecap:round;stroke-linejoin:round}}
.ag{{fill:{c['agent']};stroke:{c['edge']};stroke-width:1.5}}
@media (prefers-reduced-motion:no-preference){{
{nl.join(motion)}
}}
{nl.join(frames)}
</style>
{nl.join(marks)}
<rect class="ag" x="{sx:.1f}" y="{sy}" width="{CELL}" height="{CELL}" rx="3.5"/>
</svg>
"""


if __name__ == "__main__":
    weeks = load()
    cells = grid(weeks)
    OUT.mkdir(exist_ok=True)
    for theme in THEMES:
        (OUT / f"contrib-{theme}.svg").write_text(build(theme, cells, len(weeks)))
        print(f"wrote assets/contrib-{theme}.svg")
