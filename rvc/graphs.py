"""Certified Ramanujan graph constructions + spectral verification.

拉马努金图 = 非平凡特征值绝对值不超过 Ramanujan 界 2√(d−1) 的正则图
（Alon–Boppana 下界的极达到者，Lubotzky–Phillips–Sarnak 1988 起的系统构造）。
本模块给出三个族的小尺寸实例，全部数值验证：

- Petersen (n=10, d=3)        — 最小的三次拉马努金图
- Hoffman–Singleton (n=50, d=7) — Moore 图，直径 2：任何两个 agent 至多 2 跳
- PG(2,q) Levi 图 (n=2(q²+q+1), d=q+1) — 二部拉马努金，点线关联图
"""
from __future__ import annotations

import itertools
import math
from collections import deque

import numpy as np


def petersen() -> list[set[int]]:
    subs = list(itertools.combinations(range(5), 2))
    g: list[set[int]] = [set() for _ in subs]
    for a, b in itertools.combinations(range(len(subs)), 2):
        if set(subs[a]).isdisjoint(subs[b]):
            g[a].add(b)
            g[b].add(a)
    return g


def hoffman_singleton() -> list[set[int]]:
    """P_{i,j} 五边形 ∪ Q_{i,j} 五角星，P_{i,j}~Q_{k,(j+ik) mod 5}。"""
    vid_p = lambda i, j: i * 5 + j
    vid_q = lambda i, j: 25 + i * 5 + j
    g: list[set[int]] = [set() for _ in range(50)]

    def add(u: int, v: int) -> None:
        if u != v:
            g[u].add(v)
            g[v].add(u)

    for i in range(5):
        for j in range(5):
            add(vid_p(i, j), vid_p(i, (j + 1) % 5))
            add(vid_q(i, j), vid_q(i, (j + 2) % 5))
            for k in range(5):
                add(vid_p(i, j), vid_q(k, (j + i * k) % 5))
    return g


def levi_graph(q: int) -> list[set[int]]:
    """PG(2,q) 的点-线关联图：二部 (q+1)-正则，特征值 ±(q+1), ±√q。"""

    def norm(t: tuple[int, ...]) -> tuple[int, ...]:
        for x in t:
            if x % q:
                inv = pow(x, -1, q)
                return tuple((y * inv) % q for y in t)
        return t

    triples = {(x, y, z) for x in range(q) for y in range(q) for z in range(q)}
    triples.discard((0, 0, 0))
    pts = sorted({norm(t) for t in triples})
    lines = sorted({norm(t) for t in triples})
    n = len(pts)
    assert n == q * q + q + 1 and len(lines) == n, (q, n, len(lines))
    g: list[set[int]] = [set() for _ in range(2 * n)]
    for pi, p in enumerate(pts):
        for li, l in enumerate(lines):
            if sum(p[k] * l[k] for k in range(3)) % q == 0:
                g[pi].add(n + li)
                g[n + li].add(pi)
    return g


def adjacency(g: list[set[int]]) -> np.ndarray:
    n = len(g)
    A = np.zeros((n, n))
    for u in range(n):
        for v in g[u]:
            A[u][v] = 1.0
    return A


def bfs_dists(g: list[set[int]], src: int) -> list[int]:
    dist = [-1] * len(g)
    dist[src] = 0
    queue = deque([src])
    while queue:
        u = queue.popleft()
        for v in g[u]:
            if dist[v] < 0:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


def graph_diameter(g: list[set[int]]) -> int:
    return max(max(bfs_dists(g, s)) for s in range(len(g)))


def triangles(g: list[set[int]]) -> int:
    return sum(len(g[u] & g[v]) for u in range(len(g)) for v in g[u] if v > u) // 3


def ramanujan_report(name: str, g: list[set[int]]) -> dict:
    n = len(g)
    d = len(g[0])
    assert all(len(g[u]) == d for u in range(n)), f"{name}: not regular"
    ev = np.linalg.eigvalsh(adjacency(g))
    bound = 2.0 * math.sqrt(d - 1)
    bipartite = bool(abs(ev[0] + d) < 1e-9)
    nontrivial = [x for x in ev if x < d - 1e-9]
    if bipartite:
        nontrivial = [x for x in nontrivial if x > -d + 1e-9]
    lam2 = float(ev[-2])
    lam_abs2 = max(abs(min(nontrivial)), abs(max(nontrivial)))
    return {
        "name": name,
        "n": n,
        "degree": d,
        "bipartite": bipartite,
        "diameter": graph_diameter(g),
        "triangles": triangles(g),
        "lambda2": round(lam2, 4),
        "lambda2_abs": round(lam_abs2, 4),
        "ramanujan_bound": round(bound, 4),
        "spectral_gap": round(d - lam2, 4),
        "is_ramanujan": bool(lam_abs2 <= bound + 1e-6),
    }


def reference_reports() -> list[dict]:
    fam = [
        ("Petersen (Kneser 5,2)", petersen()),
        ("Hoffman-Singleton", hoffman_singleton()),
        ("Levi PG(2,2) Fano", levi_graph(2)),
        ("Levi PG(2,3)", levi_graph(3)),
        ("Levi PG(2,5)", levi_graph(5)),
    ]
    return [ramanujan_report(name, g) for name, g in fam]
