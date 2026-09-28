"""Day-batched strategic environment backed by the official Kaggriculture engine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from kaggle_environments import make

from agriculture_kaggle.strategic import (
    StrategicAction,
    StrategicState,
    initial_strategic_state,
)

PASS_ACTION = {"farmer": ["PASS"], "hands": [], "market": []}


def compile_strategic_action(action: StrategicAction) -> dict[str, Any]:
    """Compile one economic action into a legal one-turn engine action.

    A strategic action is deliberately day-granular.  The environment applies
    the compiled action on the first turn of that day and passes subsequently;
    physical route expansion can replace this compiler without changing the
    learning API.
    """
    name = action.name.upper()
    payload = action.payload
    market: list[list[Any]] = []
    if name == "BUY_SEED" and len(payload) == 2:
        market = [["BUY_SEED", str(payload[0]).upper(), int(payload[1])]]
    elif name == "BUY_FERTILIZER":
        market = [["BUY_PRODUCT", "FERTILIZER", int(payload[0]) if payload else 1]]
    elif name == "BUY_PRODUCT" and len(payload) == 2:
        market = [["BUY_PRODUCT", str(payload[0]).upper(), int(payload[1])]]
    elif name == "BUY_ANIMAL" and len(payload) == 2:
        market = [["BUY_ANIMAL", str(payload[0]).upper(), int(payload[1])]]
    elif name == "BUY_LAND":
        market = [["BUY_LAND"]]
    elif name == "HIRE_WORKER":
        market = [["HIRE"] for _ in range(int(payload[0]) if payload else 1)]
    elif name == "SELL" and len(payload) == 2:
        market = [["SELL", str(payload[0]).upper(), int(payload[1])]]
    elif name == "PLANT_BATCH" and payload:
        return {"farmer": ["PLANT", str(payload[0]).upper()], "hands": [], "market": []}
    return {"farmer": ["PASS"], "hands": [], "market": market}


def _crop_ages(observation: dict[str, Any]) -> tuple[tuple[str, int, int, int], ...]:
    result: list[tuple[str, int, int, int]] = []
    tiles = observation.get("farms", [{}])[0].get("tiles", [])
    flat_tiles = [tile for row in tiles for tile in row] if tiles and isinstance(tiles[0], list) else tiles
    for index, tile in enumerate(flat_tiles):
        if not isinstance(tile, dict):
            continue
        if tile.get("kind") != "PLANT":
            continue
        crop = str(tile.get("crop", tile.get("name", "UNKNOWN"))).upper()
        x, y = int(tile.get("x", index)), int(tile.get("y", 0))
        planted = int(tile.get("planted", tile.get("planted_day", observation.get("day", 0))))
        result.append((crop, x, y, max(0, int(observation.get("day", 0)) - planted)))
    return tuple(sorted(result))


def strategic_state_from_observation(observation: dict[str, Any], previous: StrategicState | None = None) -> StrategicState:
    """Project official observation fields into the strategic learning state."""
    previous = previous or initial_strategic_state()
    private = observation.get("private", {})
    player = int(observation.get("player", 0))
    farms = observation.get("farms", [])
    farm = farms[player] if player < len(farms) else {}
    prices = observation.get("market", {}).get("prices", {})
    shops = tuple(str(shop).upper() for shop in observation.get("town", {}).get("unlocked_shops", []))
    opponent_signal = {}
    if len(farms) > 1:
        opponent_signal["CASH_BUCKET"] = int(float(farms[1 - player].get("money", 0)) // 100)
    shed = private.get("shed", previous.shed)
    reserves = previous.reserves
    return StrategicState(
        day=int(observation.get("day", 0)),
        cash=float(farm.get("money", previous.cash)),
        land_quadrants=previous.land_quadrants,
        workers=previous.workers,
        seeds=previous.seeds,
        crops=previous.crops,
        animals=previous.animals,
        shed=tuple(sorted((str(key), int(value)) for key, value in shed.items() if value)),
        fertilizer=previous.fertilizer,
        shops=shops,
        expected_value=previous.expected_value,
        worker_allocations=previous.worker_allocations,
        crop_ages=_crop_ages(observation),
        market_prices=tuple(sorted((str(key), int(value)) for key, value in prices.items())),
        shop_demand=tuple(sorted((shop, 1) for shop in shops)),
        opponent_signal=tuple(sorted(opponent_signal.items())),
        reserves=reserves,
    )


class StrategicEnvironment:
    """Run strategic actions against the official engine in 24-turn day batches."""

    def __init__(self, *, seed: int = 0, steps: int = 720, opponent: Callable | None = None) -> None:
        self.seed, self.steps = seed, steps
        self.opponent = opponent or (lambda observation: PASS_ACTION)
        self.env = None
        self.observation: dict[str, Any] = {}
        self.strategic_state = initial_strategic_state()
        self.engine_step = 0

    def reset(self) -> StrategicState:
        self.env = make("kaggriculture", configuration={"episodeSteps": self.steps, "seed": self.seed})
        states = self.env.reset(2)
        self.engine_step = 0
        self.observation = states[0]["observation"]
        self.strategic_state = strategic_state_from_observation(self.observation)
        return self.strategic_state

    def step(self, action: StrategicAction) -> tuple[StrategicState, float, bool, dict[str, Any]]:
        if self.env is None:
            self.reset()
        compiled = compile_strategic_action(action)
        reward = 0.0
        done = False
        turns = min(24, self.steps - self.engine_step)
        for turn in range(turns):
            opponent_action = self.opponent(self.observation) if callable(self.opponent) else PASS_ACTION
            states = self.env.step([compiled if turn == 0 else PASS_ACTION, opponent_action])
            self.engine_step += 1
            self.observation = states[0]["observation"]
            reward = float(states[0].get("reward") or 0.0)
            done = str(states[0].get("status", "")).upper() in {"DONE", "INVALID", "TIMEOUT"}
            if done:
                break
        self.strategic_state = strategic_state_from_observation(self.observation, self.strategic_state)
        return self.strategic_state, reward, done, {"engine_step": self.engine_step, "turns": turns}
