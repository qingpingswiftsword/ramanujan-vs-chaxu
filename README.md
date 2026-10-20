# ramanujan-vs-chaxu

**拉马努金图 × 差序格局 — 协作拓扑的环境选择** — a deterministic, zero-API-cost simulation asking which collaboration topology the environment selects: the spectral perfection of a Ramanujan expander, or the clustered trust of 费孝通's differential mode of association. Sibling project of [differential-association-mas](https://github.com/qingpingswiftsword/differential-association-mas).

## The question

- **Ramanujan graphs** are the "most perfect collaboration networks" by spectrum: every nontrivial eigenvalue ≤ 2√(d−1) (the Alon–Boppana limit). Information diffuses fastest, diameter is minimal — and they contain **zero triangles**. The perfect spreading machine has no cliques at all.
- **差序格局** is the opposite: everything is circles — closeness-ranked rings, dense in-group triangles, cold periphery. Cheap, trusted, spectrally collapsed.

A population of 50 agents runs a task game on a rewirable network. Two environment knobs — **task locality L** and **context cost c** — plus three individual instincts (trust warming, exploration urge, introductions vs strangers). The equilibrium is a clean diagonal phase diagram.

## Certified reference frames

All constructions numerically verified (`rvc/graphs.py`):

| graph | n | d | diameter | triangles | \|λ\|₂ | bound 2√(d−1) | Ramanujan |
|---|---|---|---|---|---|---|---|
| Petersen (Kneser 5,2) | 10 | 3 | 2 | 0 | 2.0 | 2.83 | ✓ |
| Hoffman–Singleton | 50 | 7 | 2 | 0 | 3.0 | 4.90 | ✓ |
| Levi PG(2,2) Fano | 14 | 3 | 3 | 0 | 1.41 | 2.83 | ✓ |
| Levi PG(2,3) | 26 | 4 | 3 | 0 | 1.73 | 3.46 | ✓ |
| Levi PG(2,5) | 62 | 6 | 3 | 0 | 2.24 | 4.47 | ✓ |

## What the phase diagram says (700 rounds × 3 seeds per cell)

- **Novel tasks + cheap context (low L, low c) → expander equilibrium.** Spectral gap ratio ≈ 0.33–0.38, Ramanujan index ≈ 0.91–0.97 (**the evolved network satisfies the Ramanujan bound**), near-random clustering.
- **Local tasks + expensive context (high L, high c) → 差序 equilibrium.** Gap ratio collapses to ≈ 0.0–0.15, excess clustering ≈ 3× the random baseline.
- A wide diagonal **transition belt** between — the two organizational logics in direct competition.

**Environment flips produce topological swings without hysteresis**: 500 rounds of chaxu environment → 500 of expander → 500 back moves the same population gap 0.13 → 0.36 → −0.003 and clustering 0.30 → 0.15 → 0.32. 差序格局 is not cultural inertia; it is the optimal response to a local-expensive environment. So is the expander.

## Quick start

```bash
python3 run_demo.py                   # 所有结果 → results/*.json（约 40 秒，全 seeded）
python3 -m http.server 8000           # 打开 http://localhost:8000/viz/index.html
```

Python ≥ 3.10, numpy. No API keys, fully deterministic.

## Honest boundaries

- All agents are rule-based heuristics, no LLM, no learning
- "Ramanujan" is claimed **only for the certified reference graphs**; evolved equilibria are described via the Ramanujan index (λ₂ₐᵦₛ / 2√(d̄−1)), not certified Ramanujan
- Tasks are a one-hop knowledge-location simplification; the phase boundary is noise-banded (the transition belt is genuinely wide)

## Layout

```
rvc/graphs.py      certified constructions (Petersen, Hoffman–Singleton, Levi) + spectral verification
rvc/evolve.py      rewiring game: locality L, context cost c, trust warming, urge, introductions
rvc/layout.py      deterministic spring layout for drawing
run_demo.py        exports reference / sweep / storyline / equilibrium JSONs
viz/index.html     certified gallery, phase diagram, swing timeline, two-equilibrium duel
```

## References

- Lubotzky, Phillips & Sarnak, *Ramanujan graphs* (1988); Hoffman & Singleton (1960); Alon–Boppana bound
- 费孝通《乡土中国·差序格局》(1948)
- Agensh: Scaling Organizational Intelligence to 1,024 Agents ([arXiv:2609.26781](https://arxiv.org/abs/2609.26781))
- [differential-association-mas](https://github.com/qingpingswiftsword/differential-association-mas) — the ring-level protocol this project's chaxu pole abstracts

## License

MIT
