# Strategic Optimization Framework Design

## Goal

Build a local optimization framework that can discover Kaggriculture agents which outperform the V56 notebook baseline, while keeping the Kaggle runtime self-contained and deterministic.

## Scope

The first implementation adds a daily strategic planning layer. It does not replace the current Simple Joe submission, implement deep RL, or reproduce every V56 route immediately. The planner is evaluated using the official Kaggriculture engine and can use V56 as a fixed benchmark policy.

## Architecture

```text
official Kaggriculture engine
        ↓
observation encoder
        ↓
StrategicState
        ↓
candidate StrategicAction expansion
        ↓
deterministic daily transition model
        ↓
beam search
        ↓
physical route compiler
        ↓
720-turn action tape
```

The planner chooses strategic actions such as buying seeds, planting a crop, buying land, hiring workers, buying animals, reserving fertilizer, harvesting, and selling. The route compiler remains responsible for legal movement, planting, watering, feeding, harvesting, worker queues, shed delivery, and liquidation.

## Strategic state

The state must be compact enough for search and rich enough to distinguish profitable plans:

- Day and cash
- Unlocked land/quadrants
- Crop counts and expected harvest timing
- Animal counts and expected production timing
- Worker count and hire cost
- Shed load and key inventory quantities
- Fertilizer quantity
- Unlocked shop profile
- Market price buckets
- Optional public opponent summary

The state is an immutable dataclass. Raw observations remain available for the route compiler and safety layer but are not used as the beam-search key.

## Strategic actions

The initial action vocabulary is deliberately small:

- `HOLD`
- `BUY_SEED(crop, quantity)`
- `PLANT_BATCH(crop, plots)`
- `BUY_LAND(quadrant)`
- `BUY_FERTILIZER(quantity)`
- `BUILD_PASTURE`
- `BUILD_COOP`
- `BUY_ANIMAL(animal, quantity)`
- `HIRE_WORKER(quantity)`
- `HARVEST`
- `SELL(item, quantity)`
- `LIQUIDATE`

Every action has an affordability/precondition check and produces a new strategic state through the transition model. Invalid actions are discarded before beam expansion.

## Transition model

The transition model is an intentionally conservative daily approximation of the official engine. It accounts for:

- Seed, land, building, animal, worker, feed, and fertilizer costs
- Crop time-to-yield and expected harvest value
- Animal time-to-yield and feed overhead
- Worker parallelism and daily action capacity
- Shed capacity
- Shop demand categories
- Market price buckets
- Terminal liquidation value

The official simulator remains the final authority. Candidate plans are compiled and verified by real episodes before being considered improvements.

## Beam search

`BeamPlanner` expands the best partial plans for each day. The beam width is configurable. Candidate ordering uses a deterministic score combining expected cash, inventory value, completion feasibility, and a small risk penalty for unused capacity or unfulfilled obligations.

V56 is an external candidate/opponent, not copied into the planner. A new policy is accepted only when it improves held-out simulator performance; training-seed performance alone is insufficient.

## RL boundary

RL is deferred until the strategic state, action vocabulary, transition model, and beam search are measurable. The first RL policy chooses among planner candidates or adjusts planner parameters. It does not emit raw movement actions.

## Evaluation

Every candidate is evaluated on:

- Multiple training seeds
- Held-out seeds
- Both player seats
- `pass`, `random`, and V56 opponents
- Completion status
- Final reward
- Score margin
- Production quantities
- Invalid/no-op action counts where observable

Baseline and candidate scores are stored as JSON so experiments are reproducible and comparable.

## Compatibility constraints

- The default root `main.py` remains unchanged until a candidate beats the current baseline on held-out seeds.
- Kaggle runtime code remains independent of `uv`, notebooks, caches, and training dependencies.
- The existing production route remains usable as a verified fallback.
- New code uses the existing Python 3.11 project and official engine.

## Success criteria

The first milestone is complete when the repository can:

1. Encode an official observation into `StrategicState`.
2. Expand and transition strategic actions deterministically.
3. Generate a ranked beam of multi-day plans.
4. Compile the selected plan into a 720-turn action tape.
5. Evaluate the tape in the official engine.
6. Compare it against V56 on training and held-out seeds.
7. Preserve all existing tests and submission behavior.
