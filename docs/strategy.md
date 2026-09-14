# Kaggriculture Notebook Strategy and Score Index

This is an initial inventory of the 23 notebooks in `Kaggriculture-notebooks/`.
Scores are copied from notebook text or displayed evaluation tables. They are
not assumed to be official Kaggle leaderboard scores: many are local replay,
frozen-panel, counterfactual, or head-to-head results. “Not reported” means
the notebook does not expose a clear aggregate score in its saved contents.

| Notebook | Unique strategy contribution | Reported score/evaluation |
|---|---|---|
| `103-128-fresh-public-v43-sparse-shop-hybrid.ipynb` | Sparse visible-shop routing with V43 route tapes and fresh-public validation | **103/128 wins**; strict unseen continuation **108/116** |
| `177-180-fresh-top-30-v21-1-conditional-memory.ipynb` | Conditional memory and continuation-lineage holdouts to handle leaderboard drift | **177/180** frozen current-Top-30 replay; reserved option window **53/53**; later outer result **46/51** |
| `25-27-strict-future-v27-midgame-meta-reset.ipynb` | Strict-future validation and midgame continuation reset after auditing V26 losses | **25/27** strict-future Top-30 replay cases |
| `60-64-recent-gold-climbers-v45-market-phase.ipynb` | V45 market-phase detector; promotes a two-turn sale horizon to three turns only on bounded public evidence | **60/64** recent climber panel; **104/116** prior live field; **108/116** known-opening/unseen-continuation panel |
| `adaptive-farming-strategy-for-kaggriculture.ipynb` | Adaptive multi-route controller with yarn-led, milk-supported, and balanced plans | Not reported as one clear aggregate score |
| `farming-score-v4-a-better-shop.ipynb` | Better-shop planner, warehouse protection, labor/survival guards, and terminal rescue | Cites **93.8% win rate** for an external public-state-router source; own aggregate not clearly reported |
| `kaggriculture-101.ipynb` | Educational progression from melon-only farming to diversified scoring and dynamic Farm OS/geese economics | Season 2 is described as roughly **4× Season 1**; strawberry example **+$2.8K/episode**; no single final aggregate reported |
| `kaggriculture-dynamic-route-agent.ipynb` | Dynamic route-agent implementation | Not reported |
| `kaggriculture-findings-from-zero-to-top-meta.ipynb` | Chronological experiment log, ablations, loss audits, and route-family discovery | Reports an anchor **6–0** result; C71 later reports **zero runtime errors** and **+14,196 mean margin** in one panel; metrics vary by experiment |
| `kaggriculture-master-engine-v3.ipynb` | Unified engine combining 13 public route tapes, multi-turn sale reservations, debt accounting, and warehouse/labor guards | Claims **95.1% win rate** and **+$17.5M net margin**; notebook claim, not independently verified here |
| `kaggriculture-multi-route-farming-agent.ipynb` | Multiple complete farming routes selected by observable game information | Not reported |
| `kaggriculture-rank-your-agent.ipynb` | Seat-swapped round robin with Bradley–Terry ranking and packaged submissions | Default K320 adaptive rank-1: **106–2–0 across 540 games** |
| `kaggriculture-reactive-router.ipynb` | Compressed route tapes plus shop/market branching, weed repair, sale lead, storage/budget guards, and liquidation | Includes 720-turn validation and starter-smoke assertions; no clear aggregate score reported |
| `kaggriculture-shop-router-reactive-v4.ipynb` | Shop-router continuation with warehouse, feed, fertilizer, labor, and terminal safety layers | Not reported |
| `kaggriculture-utils-v1.ipynb` | Shared utilities for route execution, warehouse protection, feed/fertilizer handling, and sale reservation | Not reported |
| `kaggriculture-v34-observed-market-timing.ipynb` | Observed-market timing with exact sale ordering and three-turn reservations gated by public similarity | Reports smoke validation and zero mismatches/errors; no aggregate win score clearly reported |
| `kaggriculture-v39-ready-before-the-rush.ipynb` | “Ready before the rush” route with reserve, replenishment, delivery, and warehouse controls | Not reported |
| `my-2026-08-04-high-score-pipeline.ipynb` | Pipeline for extracting/replaying high-score routes and recording margins | Contains per-game reward/margin fields; no single aggregate score clearly reported |
| `shop-router-0909.ipynb` | 13 route tapes selected by the first two shops, same-day worker queues, one-turn sale advancement, and final liquidation | No clear aggregate score reported |
| `v111-8c4s-economic-core-premium-lead.ipynb` | 8-cow/4-sheep economic core with conservative premium-market lead | Reuses the V16-RC5 evaluation family; exact standalone aggregate not clearly reported in the saved notebook |
| `v13-r3-top-meta-order-safe-premium-control.ipynb` | Order-safe premium control layered over complete routes; conservative market leads | **31/32** versus exact public V21.1; **91/96** replay-derived proxies; **96/96** strong-route regression controls |
| `v16-rc5-high-score-8c-4s-premium-market-lead.ipynb` | 8-cow/4-sheep route with premium SELL timing and route-preserving recovery | Evaluation asserts **60 wins**; the saved table’s exact denominator/context should be read with the notebook |
| `v20-adaptive-r1-multi-route-agent.ipynb` | Adaptive R1 multi-route agent with persistent route state | Not reported |

## How to interpret the table

The most comparable metrics are the ones that state their denominator,
evaluation population, seat handling, and whether the opponent is frozen or
reactive. A result such as `103/128` is not directly comparable with `106–2–0
across 540 games`, and neither is automatically an official public leaderboard
score.

The recurring high-performing design is consistent across the strongest rows:
complete route tapes provide economic discipline; visible shops or market flow
select among routes; narrow controllers repair weeds, hand alignment, storage,
budget, and sale timing; and terminal liquidation prevents stranded inventory.
The next analysis step should normalize each notebook’s evaluation metadata
into a common schema before using these numbers to select a production agent.
