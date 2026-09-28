"""Small, interpretable planning layer used by the optimizer experiments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class DailyState:
    day: int
    cash: float
    crop_count: int
    animal_count: int
    shed_load: int
    shops: tuple[str, ...]


@dataclass(frozen=True)
class PlanningAction:
    name: str
    payload: tuple[str, int] = ()


def encode_observation(observation: dict[str, Any]) -> DailyState:
    private = observation.get("private", {})
    farms = observation.get("farms", [])
    player = int(observation.get("player", 0))
    farm = farms[player] if player < len(farms) else {}
    tiles = farm.get("tiles", [])
    crop_count = sum(
        tile.get("kind") == "PLANT"
        for row in tiles
        for tile in row
        if isinstance(tile, dict)
    )
    shed = private.get("shed", {})
    town = observation.get("town", observation.get("public", {}).get("town", {}))
    return DailyState(
        day=int(observation.get("day", observation.get("step", 0) // 24)),
        cash=float(farm.get("money", private.get("cash", 0))),
        crop_count=int(crop_count),
        animal_count=sum(
            tile.get("animal") is not None
            for row in tiles
            for tile in row
            if isinstance(tile, dict)
        ),
        shed_load=sum(int(value) for value in shed.values()),
        shops=tuple(town.get("unlocked_shops", [])),
    )


class BeamPlanner:
    """Deterministic bounded search over daily economic actions."""

    SEED_COSTS: ClassVar = {"WHEAT": 10, "CARROT": 20, "TOMATO": 40, "STRAWBERRY": 80, "MELON": 120}
    EXPECTED_VALUE: ClassVar = {"WHEAT": 25, "CARROT": 35, "TOMATO": 60, "STRAWBERRY": 120, "MELON": 250}
    DAYS_TO_VALUE: ClassVar = {"WHEAT": 4, "CARROT": 5, "TOMATO": 6, "STRAWBERRY": 8, "MELON": 12}

    def __init__(self, width: int = 8) -> None:
        self.width = width

    def plan(self, state: DailyState, *, days: int) -> list[PlanningAction]:
        actions = [
            PlanningAction("BUY_SEED", (crop, 1))
            for crop, cost in self.SEED_COSTS.items()
            if cost <= state.cash - 400 and state.crop_count < 1
        ]
        actions.sort(
            key=lambda action: (
                (self.EXPECTED_VALUE[action.payload[0]] - self.SEED_COSTS[action.payload[0]])
                / self.DAYS_TO_VALUE[action.payload[0]]
            ),
            reverse=True,
        )
        actions.append(PlanningAction("HOLD"))
        return actions[: max(1, min(self.width, days))]


def generate_route(
    initial_state: DailyState,
    *,
    days: int = 30,
    planner: BeamPlanner | None = None,
) -> list[dict[str, Any]]:
    """Compile daily planner choices into a complete executable action tape."""
    planner = planner or BeamPlanner()
    route: list[dict[str, Any]] = []
    state = initial_state
    for day in range(days):
        choices = planner.plan(state, days=days - day)
        planned = choices[0] if choices else PlanningAction("HOLD")
        market = []
        if planned.name == "BUY_SEED":
            crop, quantity = planned.payload
            market = [[planned.name, crop, quantity]]
        for _ in range(24):
            route.append({"farmer": ["PASS"], "hands": [], "market": market})
            market = []
        if planned.name == "BUY_SEED":
            crop, quantity = planned.payload
            state = DailyState(
                day=day + 1,
                cash=state.cash - planner.SEED_COSTS[crop] * quantity,
                crop_count=state.crop_count + 1,
                animal_count=state.animal_count,
                shed_load=state.shed_load,
                shops=state.shops,
            )
        else:
            state = DailyState(
                day=day + 1,
                cash=state.cash,
                crop_count=state.crop_count,
                animal_count=state.animal_count,
                shed_load=state.shed_load,
                shops=state.shops,
            )
    return route
