"""Spring layout for graph drawing (deterministic, seeded)."""
from __future__ import annotations

import math
import random


def spring_layout(g: list[set[int]], seed: int = 0, iters: int = 500) -> list[dict]:
    rng = random.Random(seed * 7 + 13)
    n = len(g)
    pos = [[rng.random(), rng.random()] for _ in range(n)]
    k = 1.0 / math.sqrt(n)
    for _ in range(iters):
        disp = [[0.0, 0.0] for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                dx = pos[u][0] - pos[v][0]
                dy = pos[u][1] - pos[v][1]
                d2 = dx * dx + dy * dy
                d = math.sqrt(d2) or 1e-9
                f = (k * k) / d - (d * d) / k if v in g[u] else (k * k) / d
                fx, fy = f * dx / d, f * dy / d
                disp[u][0] += fx; disp[u][1] += fy
                disp[v][0] -= fx; disp[v][1] -= fy
        for u in range(n):
            dx, dy = disp[u]
            dl = math.hypot(dx, dy) or 1e-9
            step = min(dl, 0.02)
            pos[u][0] += dx / dl * step
            pos[u][1] += dy / dl * step
        xs = [p[0] for p in pos]; ys = [p[1] for p in pos]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        sx = (x1 - x0) or 1e-9; sy = (y1 - y0) or 1e-9
        pos = [[(p[0] - x0) / sx, (p[1] - y0) / sy] for p in pos]
    return [{"x": round(p[0], 4), "y": round(p[1], 4)} for p in pos]
