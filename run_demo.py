#!/usr/bin/env python3
"""ramanujan-vs-chaxu: 环境演化 + 重连博弈 → 拉马努金(扩张子)均衡 vs 差序格局均衡。

产出（全部 seeded 确定性，零 API）：
  results/reference.json   认证拉马努金参照系（谱报告 + 布局）
  results/sweep.json       L × c 相图（每个格子的均衡指标 + 体制标签）
  results/storyline.json   环境切换时间线（差序 → 扩张 → 差序）
  results/equilibrium.json 两端均衡快照（expander 端 / chaxu 端的图 + 布局）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rvc.evolve import GameConfig, RewireGame
from rvc.graphs import hoffman_singleton, levi_graph, petersen, ramanujan_report
from rvc.layout import spring_layout

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"

ENVS = {
    "chaxu":   {"L": 0.85, "c": 0.30},
    "expander": {"L": 0.05, "c": 0.05},
}


def export_reference() -> dict:
    graphs = [
        ("Petersen (Kneser 5,2)", petersen(), 11),
        ("Hoffman-Singleton", hoffman_singleton(), 22),
        ("Levi PG(2,5)", levi_graph(5), 33),
    ]
    entries = []
    for name, g, seed in graphs:
        rep = ramanujan_report(name, g)
        rep["layout"] = spring_layout(g, seed=seed)
        rep["edges"] = sorted((min(u, v), max(u, v))
                              for u in range(len(g)) for v in g[u] if v > u)
        entries.append(rep)
    return {"note": "全部数值验证 is_ramanujan；Hoffman-Singleton 与 PG(2,5) 零三角形",
            "graphs": entries}


def run_game(L: float, c: float, rounds: int, seed: int = 1,
             snap_every: int = 0) -> tuple[dict, RewireGame, list]:
    game = RewireGame(GameConfig(L=L, c=c, seed=seed))
    snaps = []
    warm = rounds // 2
    for t in range(rounds):
        game.round()
        if snap_every and t >= warm and (t - warm) % snap_every == 0:
            snaps.append(game.metrics())
    avg = {k: round(sum(s[k] for s in snaps) / len(snaps), 4)
           for k in snaps[0]} if snaps else game.metrics()
    return avg, game, snaps


def export_sweep() -> dict:
    Ls = [0.0, 0.2, 0.4, 0.6, 0.8, 0.95]
    cs = [0.05, 0.15, 0.25, 0.35, 0.45]
    cells = []
    for L in Ls:
        for c in cs:
            runs = [run_game(L, c, rounds=700, seed=s)[0] for s in (1, 2, 3)]
            avg = {k: round(sum(r[k] for r in runs) / len(runs), 4)
                   for k in runs[0]}
            cells.append({"L": L, "c": c, "regime": RewireGame.classify(avg),
                          **avg})
    return {"note": "700 rounds/格 × 3 seeds 取均值，分类在均值上判定",
            "cells": cells}


def export_storyline() -> dict:
    game = RewireGame(GameConfig(L=ENVS["chaxu"]["L"], c=ENVS["chaxu"]["c"], seed=3))
    timeline = []
    phases = [("chaxu", 500), ("expander", 500), ("chaxu", 500)]
    t0 = 0
    for label, span in phases:
        game.cfg.L = ENVS[label]["L"]
        game.cfg.c = ENVS[label]["c"]
        for _ in range(span):
            game.round()
            t0 += 1
            if t0 % 20 == 0:
                m = game.metrics()
                timeline.append({"t": t0, "phase": label,
                                 "gap_ratio": m["gap_ratio"],
                                 "clustering": m["clustering"],
                                 "ramanujan_index": m["ramanujan_index"]})
    return {"schedule": [{"env": k, **v} for k, v in ENVS.items()],
            "note": "500 轮差序环境 → 500 轮新异环境 → 500 轮差序；每 20 轮快照",
            "timeline": timeline}


def export_equilibrium() -> dict:
    out = {}
    for label, env in ENVS.items():
        avg, game, _ = run_game(env["L"], env["c"], rounds=900)
        edges = sorted((min(u, v), max(u, v))
                       for u in range(game.cfg.n) for v in game.adj[u] if v > u)
        out[label] = {"env": env, "metrics": avg,
                      "regime": RewireGame.classify(avg),
                      "layout": spring_layout([game.adj[i] for i in range(game.cfg.n)],
                                              seed=44 if label == "chaxu" else 55),
                      "edges": edges}
    return {"note": "两端各 900 轮独立收敛后的均衡快照（n=50）", **out}


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    jobs = [("reference.json", export_reference),
            ("sweep.json", export_sweep),
            ("storyline.json", export_storyline),
            ("equilibrium.json", export_equilibrium)]
    for fname, fn in jobs:
        doc = fn()
        (RESULTS / fname).write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        print(f"wrote results/{fname}")
    print("sweep regimes:",
          {r: sum(1 for cell in json.loads((RESULTS / 'sweep.json').read_text())["cells"]
                  if cell["regime"] == r)
           for r in ("expander", "chaxu", "transition")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
