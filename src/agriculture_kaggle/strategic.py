"""Compact, deterministic strategic planning primitives.

This module deliberately models decisions at day granularity. The official
Kaggriculture engine remains the authority for validating compiled routes.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

CROP_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
CROP_VALUE = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
LAND_COST = {2: 1000, 3: 2000, 4: 4000}
CROP_FIRST_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}
CROP_REPEAT_YIELD = {"WHEAT": 2, "CARROT": 2, "TOMATO": 4, "STRAWBERRY": 4, "MELON": 4}


def _counts(values: tuple[tuple[str, int], ...]) -> dict[str, int]:
    return dict(values)


def _freeze(values: dict[str, int]) -> tuple[tuple[str, int], ...]:
    return tuple(sorted((key, value) for key, value in values.items() if value))


@dataclass(frozen=True)
class StrategicState:
    day: int = 0
    cash: float = 3000.0
    land_quadrants: int = 1
    workers: int = 1
    seeds: tuple[tuple[str, int], ...] = ()
    crops: tuple[tuple[str, int], ...] = ()
    animals: tuple[tuple[str, int], ...] = ()
    shed: tuple[tuple[str, int], ...] = ()
    fertilizer: int = 0
    shops: tuple[str, ...] = ()
    expected_value: float = 0.0
    worker_allocations: tuple[tuple[str, int], ...] = ()
    # (crop, x, y, age-in-days), captured from the official observation.
    crop_ages: tuple[tuple[str, int, int, int], ...] = ()
    market_prices: tuple[tuple[str, int], ...] = ()
    shop_demand: tuple[tuple[str, int], ...] = ()
    opponent_signal: tuple[tuple[str, int], ...] = ()
    reserves: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True)
class StrategicAction:
    name: str
    payload: tuple[str | int, ...] = ()


def initial_strategic_state(cash: float = 3000.0) -> StrategicState:
    return StrategicState(cash=cash)


def production_schedule(crop: str, planted_day: int, *, horizon: int = 30) -> tuple[int, ...]:
    """Return projected harvest days for a crop within ``horizon`` days."""
    crop = crop.upper()
    first = CROP_FIRST_YIELD.get(crop)
    repeat = CROP_REPEAT_YIELD.get(crop)
    if first is None or repeat is None:
        return ()
    days = []
    day = planted_day + first
    while day <= planted_day + horizon:
        days.append(day)
        day += repeat
    return tuple(days)


def apply_action(state: StrategicState, action: StrategicAction) -> StrategicState | None:
    """Apply one economic action, returning None when its precondition fails."""
    name = action.name.upper()
    payload = action.payload
    if name in {"HOLD", "HARVEST", "LIQUIDATE"}:
        return state
    seeds, crops, animals, shed = map(_counts, (state.seeds, state.crops, state.animals, state.shed))
    cash = state.cash
    if name == "BUY_SEED" and len(payload) == 2:
        crop, quantity = str(payload[0]).upper(), int(payload[1])
        cost = CROP_COST.get(crop, 0) * quantity
        if quantity < 1 or not cost or cash < cost:
            return None
        seeds[crop] = seeds.get(crop, 0) + quantity
        cash -= cost
    elif name == "PLANT_BATCH" and len(payload) == 2:
        crop, quantity = str(payload[0]).upper(), int(payload[1])
        if quantity < 1 or seeds.get(crop, 0) < quantity or sum(crops.values()) + quantity > state.land_quadrants * 25:
            return None
        seeds[crop] -= quantity
        crops[crop] = crops.get(crop, 0) + quantity
    elif name == "BUY_LAND":
        target = int(payload[0]) if payload else state.land_quadrants + 1
        cost = LAND_COST.get(target)
        if target != state.land_quadrants + 1 or cost is None or cash < cost:
            return None
        cash -= cost
        state = replace(state, land_quadrants=target)
    elif name == "BUY_ANIMAL" and len(payload) == 2:
        animal, quantity = str(payload[0]).upper(), int(payload[1])
        cost = ANIMAL_COST.get(animal, 0) * quantity
        if quantity < 1 or not cost or cash < cost:
            return None
        animals[animal] = animals.get(animal, 0) + quantity
        cash -= cost
    elif name == "ASSIGN_WORKER" and len(payload) == 2:
        role, quantity = str(payload[0]).upper(), int(payload[1])
        allocations = _counts(state.worker_allocations)
        used = sum(allocations.values())
        if quantity < 1 or used + quantity > state.workers:
            return None
        allocations[role] = allocations.get(role, 0) + quantity
        return replace(state, worker_allocations=_freeze(allocations))
    elif name == "HIRE_WORKER":
        quantity = int(payload[0]) if payload else 1
        cost = sum(range(1, quantity + 1))
        if quantity < 1 or cash < cost:
            return None
        cash -= cost
        state = replace(state, workers=state.workers + quantity)
    elif name == "BUY_FERTILIZER":
        quantity = int(payload[0]) if payload else 1
        cost = 100 * quantity
        if quantity < 1 or cash < cost:
            return None
        cash -= cost
        state = replace(state, fertilizer=state.fertilizer + quantity)
    elif name == "BUY_PRODUCT" and len(payload) == 2:
        product, quantity = str(payload[0]).upper(), int(payload[1])
        unit_cost = {"WHEAT": 25, "FERTILIZER": 100}.get(product, 0)
        if quantity < 1 or not unit_cost or cash < unit_cost * quantity:
            return None
        cash -= unit_cost * quantity
        shed[product] = shed.get(product, 0) + quantity
    elif name == "RESERVE" and len(payload) == 2:
        product, quantity = str(payload[0]).upper(), int(payload[1])
        if quantity < 0:
            return None
        reserves = _counts(state.reserves)
        reserves[product] = quantity
        return replace(state, reserves=_freeze(reserves))
    elif name in {"BUILD_COOP", "BUILD_PASTURE"}:
        if cash < 100:
            return None
        cash -= 100
    elif name == "SELL" and len(payload) == 2:
        item, quantity = str(payload[0]).upper(), int(payload[1])
        if quantity < 1 or shed.get(item, 0) < quantity:
            return None
        shed[item] -= quantity
        cash += CROP_VALUE.get(item, 50) * quantity
    else:
        return None
    return replace(
        state,
        cash=cash,
        seeds=_freeze(seeds),
        crops=_freeze(crops),
        animals=_freeze(animals),
        shed=_freeze(shed),
    )


def advance_day(state: StrategicState, actions: tuple[StrategicAction, ...] = ()) -> StrategicState | None:
    current = state
    for action in actions:
        current = apply_action(current, action)
        if current is None:
            return None
    crops = _counts(current.crops)
    animals = _counts(current.animals)
    produced = 0.0
    for crop, quantity in crops.items():
        if current.day >= {"WHEAT": 2, "CARROT": 2, "TOMATO": 8, "STRAWBERRY": 10, "MELON": 10}.get(crop, 99):
            produced += CROP_VALUE[crop] * quantity / 4
    produced += sum(ANIMAL_COST.get(animal, 0) * quantity / 20 for animal, quantity in animals.items())
    return replace(current, day=current.day + 1, expected_value=current.expected_value + produced)


def estimate_plan_value(state: StrategicState) -> float:
    return state.cash + state.expected_value + sum(CROP_VALUE.get(crop, 0) * quantity for crop, quantity in state.shed)


@dataclass(frozen=True)
class BeamPlan:
    actions_by_day: tuple[tuple[StrategicAction, ...], ...]
    final_state: StrategicState

    @property
    def score(self) -> float:
        return estimate_plan_value(self.final_state)


def _candidate_actions(state: StrategicState) -> tuple[tuple[StrategicAction, ...], ...]:
    candidates: list[tuple[StrategicAction, ...]] = [(StrategicAction("HOLD"),)]
    if sum(dict(state.crops).values()) < min(2, state.land_quadrants * 25) and not state.seeds:
        existing = {crop for crop, _ in state.crops}
        for crop in ("MELON", "STRAWBERRY", "CARROT", "WHEAT"):
            if crop in existing:
                continue
            candidates.append((StrategicAction("BUY_SEED", (crop, 1)), StrategicAction("PLANT_BATCH", (crop, 1))))
    if state.animals == () and state.cash >= ANIMAL_COST["COW"] + 100:
        candidates.append((StrategicAction("BUILD_PASTURE"), StrategicAction("BUY_ANIMAL", ("COW", 1))))
    if state.land_quadrants < 4:
        candidates.append((StrategicAction("BUY_LAND", (state.land_quadrants + 1,)),))
    return tuple(candidates)


class StrategicBeamPlanner:
    """Bounded deterministic search over daily strategic decisions."""

    def __init__(self, width: int = 32) -> None:
        if width < 1:
            raise ValueError("width must be positive")
        self.width = width

    def plan(self, initial_state: StrategicState, *, days: int) -> list[BeamPlan]:
        if days < 0:
            raise ValueError("days must be non-negative")
        beam = [BeamPlan((), initial_state)]
        for _ in range(days):
            expanded: list[BeamPlan] = []
            for candidate in beam:
                for actions in _candidate_actions(candidate.final_state):
                    updated = advance_day(candidate.final_state, actions)
                    if updated is not None:
                        expanded.append(BeamPlan(candidate.actions_by_day + (actions,), updated))
            expanded.sort(key=lambda item: (-item.score, repr(item.actions_by_day)))
            beam = expanded[: self.width]
        return beam


def plan_season(initial_state: StrategicState, *, days: int = 30, width: int = 32) -> BeamPlan:
    plans = StrategicBeamPlanner(width=width).plan(initial_state, days=days)
    if not plans:
        return BeamPlan((), initial_state)
    return plans[0]
