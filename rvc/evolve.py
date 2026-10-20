"""Adaptive rewiring game: environment selects expander-like vs chaxu-like topology.

每个 round：
  1. 任务：requester r 需要一份知识。以概率 L（locality）目标在 r 的 2 跳邻域内
     （本地复现型知识），否则全域均匀（新异型知识）。知识沿图上 ≤ H 跳的路径传递。
  2. 结算：路径最冷边（familiarity < τ）让传递退化（成功率 δ）；路径越长上下文
     成本 c 折损越大：reward = (1 − c·hops)。成功回报沿路径边的效用 EMA 与熟悉度；
     失败（不可达）推高 requester 的 explore-urge。
  3. 重连博弈：冷边（util < drop 阈值）被预算富余的一端剪除； urge 高的 agent
     倾向连陌生远端（expander 的长边），urge 低则连朋友的朋友（差序的近圈）。
     熟悉度随使用升温、闲置衰减——不常走的远边会"冷下去"。

均衡由环境选择：高 L / 高 c → 聚类收缩（差序格局）；低 L / 低 c → 长边存活、
谱隙拉大（expander-like，向拉马努金参照靠拢）。
"""
from __future__ import annotations

import math
import random
from collections import deque

import numpy as np


class GameConfig:
    def __init__(self, L: float = 0.5, c: float = 0.15, *,
                 n: int = 50, d_min: int = 2, d_max: int = 8, hops: int = 3,
                 tau: float = 0.6, delta: float = 0.5,
                 p_drop: float = 0.10, drop_thresh: float = 0.05,
                 p_add: float = 0.30, seed: int = 1):
        self.L = L
        self.c = c
        self.n = n
        self.d_min = d_min
        self.d_max = d_max
        self.hops = hops
        self.tau = tau
        self.delta = delta
        self.p_drop = p_drop
        self.drop_thresh = drop_thresh
        self.p_add = p_add
        self.seed = seed


class RewireGame:
    def __init__(self, cfg: GameConfig):
        self.cfg = cfg
        self.rng = random.Random(cfg.seed * 101 + 7)
        self.adj: list[set[int]] = [set() for _ in range(cfg.n)]
        for i in range(cfg.n):  # 初始：一个环（中性、连通、度=2）
            self.adj[i].add((i + 1) % cfg.n)
            self.adj[(i + 1) % cfg.n].add(i)
        self.util: dict[tuple[int, int], float] = {}
        self.fam: dict[tuple[int, int], float] = {}
        for u in range(cfg.n):
            for v in self.adj[u]:
                if u < v:
                    self.util[(u, v)] = 0.05
                    self.fam[(u, v)] = 0.5
        self.urge = [0.0] * cfg.n

    # ---------- 基础 ----------
    def _key(self, u: int, v: int) -> tuple[int, int]:
        return (u, v) if u < v else (v, u)

    def _add_edge(self, u: int, v: int) -> None:
        if u == v or v in self.adj[u]:
            return
        self.adj[u].add(v)
        self.adj[v].add(u)
        self.util[self._key(u, v)] = 0.02
        self.fam[self._key(u, v)] = 0.1

    def _remove_edge(self, u: int, v: int) -> None:
        self.adj[u].discard(v)
        self.adj[v].discard(u)
        self.util.pop(self._key(u, v), None)
        self.fam.pop(self._key(u, v), None)

    def _bfs_path(self, src: int, cap: int) -> tuple[dict[int, int], dict[int, int]]:
        """返回 {node: dist≤cap} 与 {node: parent}。"""
        dist = {src: 0}
        parent = {src: -1}
        queue = deque([src])
        while queue:
            u = queue.popleft()
            if dist[u] >= cap:
                continue
            for v in self.adj[u]:
                if v not in dist:
                    dist[v] = dist[u] + 1
                    parent[v] = u
                    queue.append(v)
        return dist, parent

    def _path_edges(self, parent: dict[int, int], target: int) -> list[tuple[int, int]]:
        edges = []
        node = target
        while parent[node] != -1:
            edges.append(self._key(node, parent[node]))
            node = parent[node]
        return edges

    # ---------- 一轮 ----------
    def round(self) -> None:
        cfg = self.cfg
        rng = self.rng
        r = rng.randrange(cfg.n)

        local = rng.random() < cfg.L
        if local:
            dist2, _ = self._bfs_path(r, 2)
            near = [t for t in dist2 if t != r]
            target = rng.choice(near) if near else rng.randrange(cfg.n)
        else:
            target = rng.randrange(cfg.n)
        if target == r:
            return

        dist, parent = self._bfs_path(r, cfg.hops)
        if target in dist:  # 可达 → 结算
            path = self._path_edges(parent, target)
            cold = min(self.fam[e] for e in path)
            reward = max(0.0, 1.0 - cfg.c * len(path))
            if cold < cfg.tau:
                reward *= cfg.delta
            warm_rate = 0.20 if local else 0.10  # 本地复现型互动升温信任更快
            for e in path:
                self.util[e] += 0.15 * (1.0 - self.util[e]) * reward
                self.fam[e] += warm_rate * (1.0 - self.fam[e])
                self.urge[e[0]] *= 0.9
                self.urge[e[1]] *= 0.9
        else:
            self.urge[r] = min(1.0, self.urge[r] + 0.2)

        for e in self.util:  # 闲置衰减：不用的边变冷变弱
            self.util[e] *= 0.985
            self.fam[e] = max(0.05, self.fam[e] * 0.997)

        # ---------- 剪除冷边 ----------
        for e in sorted(self.util):
            if self.util[e] < cfg.drop_thresh and rng.random() < cfg.p_drop:
                u, v = e
                if len(self.adj[u]) > cfg.d_min or len(self.adj[v]) > cfg.d_min:
                    rich = u if len(self.adj[u]) > cfg.d_min else v
                    other = v if rich == u else u
                    if len(self.adj[rich]) > cfg.d_min:
                        self._remove_edge(u, v)
                        self.urge[other] = min(1.0, self.urge[other] + 0.25)

        # ---------- 建新边 ----------
        for a in range(cfg.n):
            if len(self.adj[a]) >= cfg.d_max or rng.random() > cfg.p_add:
                continue
            # 环境新异度直接进入重连倾向：任务流越全局，越该连陌生远端
            p_explore = 0.02 + 0.25 * self.urge[a] + 0.75 * (1.0 - cfg.L)
            cand = None
            if rng.random() < p_explore:
                cand = rng.randrange(cfg.n)  # 陌生远端
            else:  # 介绍制：朋友的朋友中挑共同朋友最多者（三角闭包定向）
                fo = {w for x in self.adj[a] for w in self.adj[x]
                      if w != a and w not in self.adj[a]}
                if fo:
                    sample = rng.sample(sorted(fo), min(3, len(fo)))
                    cand = max(sample,
                               key=lambda w: len(self.adj[a] & self.adj[w]))
                else:
                    cand = rng.randrange(cfg.n)
            if cand is not None and cand != a and cand not in self.adj[a]:
                self._add_edge(a, cand)
                self.urge[a] *= 0.6
            self.urge[a] *= 0.97

    # ---------- 度量 ----------
    def metrics(self) -> dict:
        cfg = self.cfg
        n = cfg.n
        degs = [len(self.adj[a]) for a in range(n)]
        d_avg = sum(degs) / n
        A = np.zeros((n, n))
        for u in range(n):
            for v in self.adj[u]:
                A[u][v] = 1.0
        ev = np.linalg.eigvalsh(A)
        lam2 = float(ev[-2])
        lam_abs2 = max(abs(float(ev[0])), lam2)
        bound = 2.0 * math.sqrt(max(d_avg - 1.0, 0.5))
        tri = 0
        for u in range(n):
            for v in self.adj[u]:
                if v > u:
                    tri += len(self.adj[u] & self.adj[v])
        tri //= 3
        possible = n * (n - 1) / 2
        clust = 3.0 * tri / possible  # 全局聚类（密度修正口径：网络三角密度）
        # 局部聚类均值更贴"圈子感"
        lc = []
        for u in range(n):
            k = len(self.adj[u])
            if k >= 2:
                links = sum(1 for a in self.adj[u]
                            for b in self.adj[a] if b in self.adj[u]) // 2
                lc.append(2 * links / (k * (k - 1)))
        mean_clust = sum(lc) / len(lc) if lc else 0.0
        ds = sorted(degs)
        gini = (sum((2 * i - n + 1) * ds[i] for i in range(n))) / (n * sum(ds)) if sum(ds) else 0.0
        gap_ratio = (d_avg - lam2) / d_avg
        ramanujan_index = lam_abs2 / bound
        sources = self.rng.sample(range(n), 6)
        ecc = [max(self._bfs_path(s, n)[0].values()) for s in sources]
        p_rand = d_avg / (n - 1)
        excess_clust = mean_clust / p_rand if p_rand else 0.0
        return {
            "d_avg": round(d_avg, 3),
            "lambda2": round(lam2, 3),
            "lambda2_abs": round(lam_abs2, 3),
            "ramanujan_bound": round(bound, 3),
            "ramanujan_index": round(ramanujan_index, 3),
            "gap_ratio": round(gap_ratio, 3),
            "clustering": round(mean_clust, 3),
            "excess_clustering": round(excess_clust, 2),
            "triangle_density": round(3 * tri / possible, 4),
            "degree_gini": round(gini, 3),
            "mean_eccentricity": round(sum(ecc) / len(ecc), 2),
            "edges": sum(degs) // 2,
        }

    @staticmethod
    def classify(m: dict) -> str:
        if (m["gap_ratio"] >= 0.30 and m["ramanujan_index"] <= 1.0
                and m["excess_clustering"] <= 1.6):
            return "expander"
        if m["gap_ratio"] <= 0.20 and m["excess_clustering"] >= 2.2:
            return "chaxu"
        return "transition"
