# Basic Kaggriculture Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal deterministic Kaggriculture agent that can be tested locally and submitted as a root-level `main.py`.

**Architecture:** Keep the agent logic in the installable `agriculture_kaggle` package and expose a thin root `main.py` adapter for Kaggle submission. The first behavior is intentionally conservative: on the first turn buy one wheat seed, then return valid PASS actions without making unsafe assumptions about the observation state.

**Tech Stack:** Python 3.11+, uv, `kaggle-environments`, pytest, Ruff.

**Spec:** Approved in-chat design on 2026-08-24.

## Global Constraints

- The Kaggle submission entry point must expose a callable named `agent` from root `main.py`.
- The returned action must contain `farmer`, `hands`, and `market` keys.
- The first-turn action must buy exactly one wheat seed; later turns must be safe PASS actions.
- Local tests must not require network access or Kaggle credentials.
- The project must use Python 3.11+ because current Kaggle packages require it.

### Task 1: Define the starter-agent contract with tests

**Files:**
- Create: `tests/test_agent.py`

**Interfaces:**
- Consumes: `agriculture_kaggle.agent.agent(observation)` once implemented.
- Produces: executable tests covering first-turn purchase, later PASS behavior, and required action keys.

- [ ] **Step 1: Write the failing tests**

```python
from agriculture_kaggle.agent import agent


def test_first_turn_buys_one_wheat_seed():
    action = agent({"step": 0})

    assert action == {
        "farmer": ["PASS"],
        "hands": [],
        "market": [["BUY_SEED", "WHEAT", 1]],
    }


def test_later_turn_passes_without_market_orders():
    action = agent({"step": 1})

    assert action == {"farmer": ["PASS"], "hands": [], "market": []}


def test_missing_step_is_safe():
    action = agent({})

    assert action == {"farmer": ["PASS"], "hands": [], "market": []}
```

- [ ] **Step 2: Run the tests and verify they fail because the module is missing**

Run: `uv run pytest tests/test_agent.py -q`

Expected: collection failure because `agriculture_kaggle.agent` does not exist yet.

### Task 2: Implement the reusable starter agent and Kaggle adapter

**Files:**
- Create: `src/agriculture_kaggle/agent.py`
- Create: `main.py`

**Interfaces:**
- Produces: `agent(observation: dict) -> dict` from both `agriculture_kaggle.agent` and root `main.py`.

- [ ] **Step 1: Implement the minimal agent**

```python
from typing import Any


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    if observation.get("step", 0) == 0:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", 1]],
        }
    return {"farmer": ["PASS"], "hands": [], "market": []}
```

- [ ] **Step 2: Add the root submission adapter**

```python
from agriculture_kaggle.agent import agent

__all__ = ["agent"]
```

- [ ] **Step 3: Run the focused tests and verify they pass**

Run: `uv run pytest tests/test_agent.py -q`

Expected: 3 passed.

### Task 3: Configure dependencies and local smoke execution

**Files:**
- Modify: `.python-version`
- Modify: `pyproject.toml`
- Create: `scripts/run_local.py`

**Interfaces:**
- Consumes: root `main.agent` and `kaggle_environments.make`.
- Produces: a local 10-turn Kaggriculture smoke run that prints final player statuses.

- [ ] **Step 1: Pin Python 3.11 and add the runtime/test dependencies**

Run:

```bash
uv python pin 3.11
uv add kaggle-environments
uv add --dev pytest pytest-cov
```

- [ ] **Step 2: Create the local smoke runner**

```python
from kaggle_environments import make

from main import agent


def main() -> None:
    environment = make("kaggriculture", configuration={"episodeSteps": 10})
    environment.run([agent, "pass"])
    for player, state in enumerate(environment.steps[-1]):
        print(f"player={player} status={state.status} reward={state.reward}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run the smoke test**

Run: `uv run python scripts/run_local.py`

Expected: two player status/reward lines and no import or action-format errors.

### Task 4: Verify the complete project

**Files:**
- No new files.

- [ ] **Step 1: Run all tests**

Run: `uv run pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Run Ruff**

Run: `uv run ruff check .`

Expected: no lint errors.

- [ ] **Step 3: Verify the submission import**

Run: `uv run python -c 'from main import agent; print(agent({"step": 0}))'`

Expected: the first-turn action dictionary is printed.

- [ ] **Step 4: Review Git status**

Run: `git status --short`

Expected: only the intended agent, test, runner, metadata, and plan files are changed.
