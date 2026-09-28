# Strategic Optimization Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a deterministic strategic-state transition model and beam-search planner that can generate and evaluate multi-day farming plans against the V56 benchmark.

**Architecture:** Add a focused `strategic.py` module containing immutable state, actions, transitions, and beam search. Keep the existing physical route compiler separate; add a bridge that turns the selected crop plan into a verified route. Extend training utilities with candidate evaluation, while leaving the default Simple Joe submission unchanged.

**Tech Stack:** Python 3.11, dataclasses, standard library, official `kaggle-environments`, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-09-22-strategic-optimization-design.md`

## Global Constraints

- Use the official Kaggriculture engine as the final authority.
- Keep the default root `main.py` unchanged until a candidate beats the baseline on held-out seeds.
- Keep Kaggle runtime code independent of `uv`, notebooks, caches, and training dependencies.
- Use deterministic transitions and tie-breaking for reproducible search.
- Do not implement raw-action RL in this milestone.

## Review Focus

- Invalid strategic purchases must be rejected without mutating state — test action preconditions and cash preservation.
- Crop and animal timing must not create value before first yield — test delayed production.
- Beam search must be deterministic and preserve the best candidate — test tie-breaking and width limits.
- Route compilation must produce exactly one action per turn — test 720-turn output and official-engine completion.
- V56 comparisons must not silently alter the default submission — test existing Simple Joe behavior after integration.

### Task 1: Strategic state and action model

**Files:**
- Create: `src/agriculture_kaggle/strategic.py`
- Create: `tests/test_strategic.py`

**Interfaces:**
- Produces `StrategicState`, `StrategicAction`, `initial_strategic_state()`, and `apply_action()` for later planner tasks.

- [ ] Write failing tests for initial state, affordable seed purchase, rejected unaffordable purchase, immutable state, and action equality.
- [ ] Run `./.venv/bin/pytest -q tests/test_strategic.py`; expect import failure because the module does not exist.
- [ ] Implement immutable dataclasses and minimal action validation for `HOLD`, `BUY_SEED`, `BUY_LAND`, `BUY_FERTILIZER`, `HIRE_WORKER`, `BUY_ANIMAL`, `BUILD_COOP`, `BUILD_PASTURE`, `SELL`, and `LIQUIDATE`.
- [ ] Run the focused tests and confirm they pass.
- [ ] Run the existing suite and confirm no regression.

### Task 2: Daily production transition model

**Files:**
- Modify: `src/agriculture_kaggle/strategic.py`
- Modify: `tests/test_strategic.py`

**Interfaces:**
- Consumes `StrategicState` and `StrategicAction`.
- Produces `advance_day(state, actions)` and `estimate_plan_value(state)`.

- [ ] Write failing tests for crop time-to-yield, animal feed cost, worker capacity, shed capacity, and terminal liquidation value.
- [ ] Run the focused tests and verify they fail for missing transition functions.
- [ ] Implement conservative deterministic daily transitions using the README crop/animal economics and explicit production obligations.
- [ ] Run focused and full tests.

### Task 3: Deterministic beam search

**Files:**
- Modify: `src/agriculture_kaggle/strategic.py`
- Modify: `tests/test_strategic.py`

**Interfaces:**
- Produces `BeamPlan`, `StrategicBeamPlanner(width=...)`, and `plan_season(initial_state, days=...)`.

- [ ] Write failing tests for beam width, deterministic ordering, multi-day plan length, and retaining a profitable crop plan over `HOLD`.
- [ ] Run focused tests and verify the expected failures.
- [ ] Implement bounded candidate expansion, deterministic score ordering, and beam pruning.
- [ ] Run focused and full tests.

### Task 4: Bridge strategic plans to physical routes

**Files:**
- Modify: `src/agriculture_kaggle/production.py`
- Modify: `src/agriculture_kaggle/training.py`
- Modify: `tests/test_production.py`
- Modify: `tests/test_training.py`

**Interfaces:**
- Produces `route_from_strategic_plan(plan, steps=720)` and `make_strategic_agent(...)`.

- [ ] Write failing tests that compile a one-crop strategic plan into a 720-turn route and run it through the official engine.
- [ ] Run the focused tests and verify failure before implementation.
- [ ] Implement the minimal bridge using existing physical route primitives, preserving legal movement, watering, harvest, drop, and sell behavior.
- [ ] Run the official-engine smoke test and the full suite.

### Task 5: Benchmark integration and documentation

**Files:**
- Modify: `src/agriculture_kaggle/training.py`
- Modify: `scripts/benchmark.py`
- Modify: `README.md`
- Modify: `tests/test_training.py`

**Interfaces:**
- Produces `evaluate_strategy_candidates(...)` with training/holdout summaries and optional custom V56 opponent loading.

- [ ] Write failing tests for candidate score aggregation, held-out seed separation, both seats, and unchanged Simple Joe behavior.
- [ ] Run focused tests and verify failure.
- [ ] Implement candidate evaluation and document exact commands for strategic planning and V56 comparison.
- [ ] Run full pytest, Ruff, a 720-turn strategic smoke episode, and a benchmark against pass.

### Task 6: Final verification

**Files:**
- No new production files.

- [ ] Run `./.venv/bin/pytest -q`.
- [ ] Run `./.venv/bin/ruff check src scripts tests main.py`.
- [ ] Run the packaging script and confirm the default submission artifact remains valid.
- [ ] Record the strategic planner score against pass and V56 without changing the default submission agent.
