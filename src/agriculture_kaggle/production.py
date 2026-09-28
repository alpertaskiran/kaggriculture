"""Executable production routes for the strategy planner.

The economic planner chooses what to buy.  This module turns that choice into
the small, explicit action queues the Kaggriculture engine executes each turn.
It intentionally starts with one reliable crop lane; more plots and animals
can be added without changing the queue interface.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from agriculture_kaggle.strategic import BeamPlan

TURN_PER_DAY = 24
START = (4, 4)
PLOT = (3, 4)

_CROP_HARVEST_DAY = {
    "WHEAT": 4,
    "CARROT": 3,
    "TOMATO": 11,
    "STRAWBERRY": 16,
    "MELON": 10,
}
_EXPECTED_HARVEST = {
    "WHEAT": 3,
    "CARROT": 3,
    "TOMATO": 4,
    "STRAWBERRY": 4,
    "MELON": 6,
}
_ANIMAL_STRUCTURE = {"GOOSE": "COOP", "COW": "PASTURE", "SHEEP": "PASTURE"}
_ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def manhattan_moves(start: tuple[int, int], target: tuple[int, int]) -> list[str]:
    """Return a deterministic cardinal path from ``start`` to ``target``."""
    x, y = start
    target_x, target_y = target
    moves: list[str] = []
    while x < target_x:
        moves.append("EAST")
        x += 1
    while x > target_x:
        moves.append("WEST")
        x -= 1
    while y < target_y:
        moves.append("SOUTH")
        y += 1
    while y > target_y:
        moves.append("NORTH")
        y -= 1
    return moves


@dataclass(frozen=True)
class WorkerQueue:
    """Per-worker action tape with safe PASS padding.

    The engine's ``hands`` list is positional, so callers can ask for the
    actions in the same worker order used when hiring farm hands.
    """

    queues: Mapping[str, Sequence[str]]

    def action(self, worker: str, step: int) -> str:
        actions = self.queues.get(worker, ())
        return actions[step] if 0 <= step < len(actions) else "PASS"

    def actions(self, step: int, workers: Sequence[str]) -> list[str]:
        return [self.action(worker, step) for worker in workers]


def animal_care_cycle() -> list[str]:
    """Return the repeatable one-action-per-turn animal maintenance cycle."""
    return ["FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER"]


def animal_care_queue(days: int = 30, production_interval: int = 2) -> list[str]:
    """Compile a daily animal-care tape for a worker standing on the animal.

    Feeding and care happen every day. Harvesting is scheduled at the supplied
    interval, while fertilizer is collected daily because it does not accrue.
    Movement to the animal tile is intentionally composed by the caller's
    ``WorkerQueue`` so the same queue works for any farm layout.
    """
    if days < 0 or production_interval < 1:
        raise ValueError("days must be non-negative and interval must be positive")
    actions = ["PASS"] * (days * TURN_PER_DAY)
    for day in range(days):
        start = day * TURN_PER_DAY
        actions[start] = "FEED"
        actions[start + 1] = "CARE"
        if day % production_interval == production_interval - 1:
            actions[start + 2] = "HARVEST"
        actions[start + 3] = "COLLECT_FERTILIZER"
    return actions


def worker_crop_queue(
    *, crop: str, plot: tuple[int, int] = PLOT, days: int = 30, start: tuple[int, int] = (5, 4), fertilize: bool = False,
) -> list[list[str]]:
    """Compile a movement-aware hired-hand queue for one crop plot.

    Hands return to their shed-access position at each day boundary, just like
    the farmer.  The queue therefore includes the complete path on every day
    instead of assuming that a hand remains on the field overnight.
    """
    crop = crop.upper()
    if crop not in _CROP_HARVEST_DAY or days < 0:
        raise ValueError("unsupported crop or negative day count")
    queue = [["PASS"] for _ in range(days * TURN_PER_DAY)]
    path = manhattan_moves(start, plot)
    first_action = len(path)
    if first_action < len(queue):
        queue[first_action] = ["PLANT", crop]
        if fertilize and first_action + 1 < len(queue):
            queue[first_action + 1] = ["FERTILIZE"]
    for day in range(days):
        day_start = day * TURN_PER_DAY
        for offset, move in enumerate(path):
            if day_start + offset < len(queue):
                queue[day_start + offset] = [move]
        water_step = day_start + len(path) + (1 if day == 0 else 0)
        if water_step < len(queue) and day < _CROP_HARVEST_DAY[crop]:
            queue[water_step] = ["WATER"]
    harvest_step = _CROP_HARVEST_DAY[crop] * TURN_PER_DAY + len(path)
    if harvest_step < len(queue):
        queue[harvest_step] = ["HARVEST"]
        cursor = harvest_step + 1
        for move in manhattan_moves(plot, START):
            if cursor < len(queue):
                queue[cursor] = [move]
            cursor += 1
        if cursor < len(queue):
            queue[cursor] = ["DROP"]
    return queue


def _turn(
    farmer: str | list[str] = "PASS", *, market: list[list[Any]] | None = None
) -> dict[str, Any]:
    return {"farmer": [farmer] if isinstance(farmer, str) else farmer, "hands": [], "market": market or []}


def generate_production_route(
    *,
    steps: int = TURN_PER_DAY * 30,
    crop: str = "WHEAT",
    plot: tuple[int, int] = PLOT,
) -> list[dict[str, Any]]:
    """Build a self-contained single-plot route for a real farm episode.

    The route buys one seed, reaches an initially unlocked plot adjacent to
    the shed, plants and waters it, waters once per day, harvests at peak
    timing, returns the produce to the shed, and sells it near season end.
    Invalid tail turns are padded with PASS so callers can use any episode
    length without indexing special cases.
    """
    if steps < 1:
        return []
    crop = crop.upper()
    if crop not in _CROP_HARVEST_DAY:
        raise ValueError(f"Unsupported crop: {crop}")

    route = [_turn() for _ in range(steps)]
    route[0] = _turn(market=[["BUY_SEED", crop, 1]])
    cursor = 1
    moves = manhattan_moves(START, plot)
    for move in moves:
        if cursor >= steps:
            return route
        route[cursor] = _turn(move)
        cursor += 1

    # Planting day counts as the first missed watering day, so water directly
    # after planting and then once at the beginning of every later day.
    if cursor < steps:
        route[cursor] = _turn(["PLANT", crop])
        cursor += 1
    if cursor < steps:
        route[cursor] = _turn("WATER")

    harvest_step = _CROP_HARVEST_DAY[crop] * TURN_PER_DAY
    # The engine returns the farmer to the shed-access position at each day
    # boundary. Re-enter the plot, then water it once for that day.
    for day in range(1, _CROP_HARVEST_DAY[crop] + 1):
        day_start = day * TURN_PER_DAY
        if day_start < harvest_step and day_start < steps:
            for offset, move in enumerate(manhattan_moves(START, plot)):
                if day_start + offset < steps:
                    route[day_start + offset] = _turn(move)
            water_step = day_start + len(manhattan_moves(START, plot))
            if water_step < steps:
                route[water_step] = _turn("WATER")

    if harvest_step < steps:
        moves = manhattan_moves(START, plot)
        for offset, move in enumerate(moves):
            if harvest_step + offset < steps:
                route[harvest_step + offset] = _turn(move)
        harvest_action = harvest_step + len(moves)
        if harvest_action < steps:
            route[harvest_action] = _turn("HARVEST")
        cursor = harvest_action + 1
        for move in manhattan_moves(plot, START):
            if cursor < steps:
                route[cursor] = _turn(move)
            cursor += 1
        if cursor < steps:
            route[cursor] = _turn("DROP")

    if steps >= 2:
        route[-2] = _turn(market=[["SELL", crop, _EXPECTED_HARVEST[crop]]])
    return route


def route_from_strategic_plan(plan: BeamPlan, *, steps: int = TURN_PER_DAY * 30) -> list[dict[str, Any]]:
    """Compile the first crop commitment in a strategic plan into a route."""
    crops: list[str] = []
    for day_actions in plan.actions_by_day:
        for action in day_actions:
            if action.name == "BUY_SEED" and action.payload:
                crop = str(action.payload[0]).upper()
                if crop not in crops:
                    crops.append(crop)
        if len(crops) >= 2:
            break
    if len(crops) >= 2:
        return generate_multi_plot_route(crops=(crops[0], crops[1]), steps=steps)
    return generate_production_route(steps=steps, crop=crops[0] if crops else "WHEAT")


def generate_multi_plot_route(
    *,
    crops: tuple[str, ...] = ("WHEAT", "MELON"),
    steps: int = TURN_PER_DAY * 30,
) -> list[dict[str, Any]]:
    """Compile a two-plot route with independent watering and harvest timing."""
    if len(crops) != 2 or any(crop.upper() not in _CROP_HARVEST_DAY for crop in crops):
        raise ValueError("multi-plot route requires exactly two supported crops")
    crops = tuple(crop.upper() for crop in crops)
    plots = ((3, 4), (4, 3))
    route = [_turn() for _ in range(steps)]
    if not steps:
        return route
    route[0] = _turn(market=[["BUY_SEED", crop, 1] for crop in crops])

    def place(index: int, action: str | list[str]) -> int:
        if index < steps:
            route[index] = _turn(action)
        return index + 1

    index = 1
    position = START
    for crop, plot in zip(crops, plots):
        for move in manhattan_moves(position, plot):
            index = place(index, move)
        index = place(index, ["PLANT", crop])
        position = plot
    index = place(index, "WATER")
    for move in manhattan_moves(position, plots[0]):
        index = place(index, move)
    index = place(index, "WATER")

    for day in range(1, max(_CROP_HARVEST_DAY[crop] for crop in crops) + 1):
        index = day * TURN_PER_DAY
        position = START
        harvested = False
        for crop, plot in zip(crops, plots):
            for move in manhattan_moves(position, plot):
                index = place(index, move)
            harvest_day = _CROP_HARVEST_DAY[crop]
            if day == harvest_day:
                index = place(index, "HARVEST")
                harvested = True
            else:
                index = place(index, "WATER")
            position = plot
        if harvested:
            for move in manhattan_moves(position, START):
                index = place(index, move)
            index = place(index, "DROP")

    if steps >= 2:
        route[-2] = _turn(
            market=[
                ["SELL", crop, _EXPECTED_HARVEST[crop]]
                for crop in crops
            ]
        )
    return route


def make_multi_plot_agent() -> Any:
    """Return the verified two-plot wheat/melon route as a callable agent."""
    route = generate_multi_plot_route()

    def policy(observation: dict[str, Any]) -> dict[str, Any]:
        step = int(observation.get("step", 0))
        return route[step] if step < len(route) else _turn()

    return policy


def generate_full_physical_route(
    *,
    crops: tuple[str, ...] = ("WHEAT", "MELON"),
    animals: tuple[str, ...] = (),
    workers: int = 0,
    worker_crops: tuple[str, ...] = (),
    fertilize: bool = False,
    worker_days: int | None = None,
    opening_market_orders: tuple[tuple[Any, ...], ...] = (),
    steps: int = TURN_PER_DAY * 30,
) -> list[dict[str, Any]]:
    """Compile crops, workers, and animal maintenance into one physical tape.

    Crop work is assigned to the farmer through the existing deterministic
    multi-plot route.  Hired hands receive independent daily maintenance tapes;
    this keeps the engine's positional ``hands`` protocol explicit and makes
    the schedule inspectable by the optimizer.  Animal purchases/building are
    emitted in the opening market queue and their care actions are assigned to
    the first available hand (or the farmer when no hand is requested).
    """
    if not crops:
        raise ValueError("at least one crop is required")
    if worker_days is not None and (worker_days < 0 or worker_days > steps // TURN_PER_DAY):
        raise ValueError("worker_days must fit within the episode")
    if len(animals) > workers:
        raise ValueError("one hired worker is required per animal")
    active_worker_days = steps // TURN_PER_DAY if worker_days is None else worker_days
    if len(crops) == 1:
        route = generate_production_route(steps=steps, crop=crops[0])
    elif len(crops) == 2:
        route = generate_multi_plot_route(crops=tuple(crops[:2]), steps=steps)
    else:
        raise ValueError("physical compiler currently supports at most two crop plots")
    if not route:
        return route

    market = list(route[0]["market"])
    market.extend([list(order) for order in opening_market_orders])
    for crop in worker_crops:
        crop = crop.upper()
        if crop not in {"WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"}:
            raise ValueError(f"unsupported worker crop: {crop}")
        market.append(["BUY_SEED", crop, 1])
    if fertilize:
        market.append(["BUY_PRODUCT", "FERTILIZER", max(1, len(crops) + len(worker_crops))])
    for animal in animals:
        animal = animal.upper()
        if animal not in {"GOOSE", "COW", "SHEEP"}:
            raise ValueError(f"unsupported animal: {animal}")
        market.extend([["BUY_ANIMAL", animal, 1]])
    if animals:
        # One wheat unit is consumed per animal per day; buy a conservative
        # season reserve so the maintenance queue cannot starve the animal.
        market.append(["BUY_PRODUCT", "WHEAT", max(1, steps // TURN_PER_DAY)])
    market.extend([["HIRE"] for _ in range(workers)] if active_worker_days else [])
    route[0] = {**route[0], "market": market}
    # Hands are day-scoped in the official engine. Rehire them at each day
    # boundary before their next physical queue starts.
    for day in range(1, active_worker_days):
        boundary = day * TURN_PER_DAY
        route[boundary] = {
            **route[boundary],
            "market": [["HIRE"] for _ in range(workers)] + route[boundary]["market"],
        }

    hand_names = [f"hand-{index + 1}" for index in range(workers)]
    care = animal_care_queue(days=max(1, steps // TURN_PER_DAY)) if animals else []
    worker_queues = [
        worker_crop_queue(
            crop=crop,
            start=(5 + index, 4),
            days=max(1, active_worker_days),
            fertilize=fertilize,
        )
        for index, crop in enumerate(worker_crops[:workers])
    ]
    for step, turn in enumerate(route):
        hands = []
        for index, _ in enumerate(hand_names):
            if animals and index < len(animals):
                animal = animals[index].upper()
                structure_action = "BUILD_COOP" if _ANIMAL_STRUCTURE.get(animal) == "COOP" else "BUILD_PASTURE"
                if index == 0:
                    setup = {
                        1: ["PICKUP", animal, 1],
                        2: ["WEST"],
                        3: ["NORTH"],
                        4: [structure_action],
                        5: ["PLACE", animal],
                    }
                    day_actions = {
                        0: ["PASS"], 1: ["EAST"], 2: ["PICKUP", "WHEAT", 1],
                        3: ["WEST"], 4: ["NORTH"], 5: ["FEED"], 6: ["CARE"],
                        7: ["HARVEST"], 8: ["COLLECT_FERTILIZER"],
                    }
                else:
                    setup = {
                        1: ["PICKUP", animal, 1],
                        2: ["NORTH"],
                        3: ["NORTH"],
                        4: ["WEST"],
                        5: [structure_action],
                        6: ["PLACE", animal],
                    }
                    day_actions = {
                        0: ["PASS"], 1: ["PICKUP", "WHEAT", 1], 2: ["NORTH"],
                        3: ["NORTH"], 4: ["WEST"], 5: ["FEED"], 6: ["CARE"],
                        7: ["HARVEST"], 8: ["COLLECT_FERTILIZER"],
                    }
                if step < TURN_PER_DAY:
                    hands.append(setup.get(step, [care[step - 6]] if step >= 6 and step - 6 < len(care) else ["PASS"]))
                else:
                    _, hour = divmod(step, TURN_PER_DAY)
                    hands.append(day_actions.get(hour, ["PASS"]))
                continue
            if index > 0 and index - 1 < len(worker_queues):
                queue = worker_queues[index - 1] if animals else worker_queues[index]
                hands.append(queue[step] if step < len(queue) else ["PASS"])
                continue
            if index > 0:
                hands.append(["PASS"])
                continue
            if not animals and index < len(worker_queues):
                queue = worker_queues[index]
                hands.append(queue[step] if step < len(queue) else ["PASS"])
                continue
            # The first hand performs the structure setup before entering the
            # recurring care queue.  The initial farm position is (4, 4), so
            # (4, 3) is the adjacent, unlocked animal tile.
            animal = animals[0].upper() if animals else ""
            structure_action = "BUILD_COOP" if _ANIMAL_STRUCTURE.get(animal) == "COOP" else "BUILD_PASTURE"
            setup = {
                1: ["PICKUP", animals[0].upper(), 1],
                2: ["WEST"],
                3: ["NORTH"],
                4: [structure_action],
                5: ["PLACE", animal],
            } if animals else {}
            care_offset = 6 if animals else 4
            if animals and step >= TURN_PER_DAY:
                day, hour = divmod(step, TURN_PER_DAY)
                animal_actions = {
                    0: ["PASS"],
                    1: ["EAST"],
                    2: ["PICKUP", "WHEAT", 1],
                    3: ["WEST"],
                    4: ["NORTH"],
                    5: ["FEED"],
                    6: ["CARE"],
                    7: ["HARVEST"],
                    8: ["COLLECT_FERTILIZER"],
                }
                hands.append(animal_actions.get(hour, ["PASS"]) if day >= 1 else ["PASS"])
            else:
                hands.append(setup.get(step, [care[step - care_offset]] if step >= care_offset and step - care_offset < len(care) else ["PASS"]))
        route[step] = {**turn, "hands": hands}
    if steps >= 2 and animals:
        terminal_market = list(route[-2]["market"])
        for animal in animals:
            product = _ANIMAL_PRODUCT[animal.upper()]
            terminal_market.append(["SELL", product, 100])
        terminal_market.append(["SELL", "FERTILIZER", 100])
        route[-2] = {**route[-2], "market": terminal_market}
    return route


def make_full_physical_agent(**kwargs: Any) -> Any:
    """Return a callable backed by :func:`generate_full_physical_route`."""
    route = generate_full_physical_route(**kwargs)

    def policy(observation: dict[str, Any]) -> dict[str, Any]:
        step = int(observation.get("step", 0))
        return route[step] if step < len(route) else _turn()

    return policy


def select_animal_configuration(
    *,
    crops: tuple[str, ...] = ("WHEAT",),
    training_seeds: Sequence[int] = (7, 1234),
    workers: int = 1,
    steps: int = TURN_PER_DAY * 30,
) -> dict[str, Any]:
    """Select livestock by official-engine reward, including the no-animal case."""
    from agriculture_kaggle.simulation import run_episode

    candidates: tuple[tuple[str, ...], ...] = ((), ("GOOSE",), ("SHEEP",), ("COW",))
    reports = []
    for animals in candidates:
        rewards = []
        for seed in training_seeds:
            result = run_episode(
                make_full_physical_agent(crops=crops, animals=animals, workers=workers if animals else 0, steps=steps),
                seed=seed,
                steps=steps,
            )
            if result.statuses != ["DONE", "DONE"]:
                raise RuntimeError(f"route failed for {animals or 'no animals'} on seed {seed}")
            rewards.append(float(result.rewards[0]))
        reports.append({"animals": list(animals), "rewards": rewards, "mean_reward": sum(rewards) / len(rewards)})
    selected = max(reports, key=lambda report: (report["mean_reward"], repr(report["animals"])))
    return {"selected": selected, "candidates": reports}


def search_physical_configurations(
    *,
    training_seeds: Sequence[int] = (7, 1234),
    holdout_seeds: Sequence[int] = (),
    crops: Sequence[str] = ("WHEAT", "CARROT", "STRAWBERRY", "MELON"),
    crop_pairs: Sequence[tuple[str, str]] = (),
    include_worker_lane: bool = True,
    include_animals: bool = True,
    include_fertilizer: bool = True,
    worker_day_options: Sequence[int | None] = (None,),
    opponent: Any = "pass",
    market_order_options: Sequence[tuple[tuple[Any, ...], ...]] = ((),),
    steps: int = TURN_PER_DAY * 30,
) -> dict[str, Any]:
    """Search executable route configurations on official-engine rewards."""
    from itertools import product

    from agriculture_kaggle.simulation import run_episode

    candidates: list[dict[str, Any]] = []
    animal_options: tuple[tuple[str, ...], ...] = ((), ("GOOSE",), ("SHEEP",), ("COW",)) if include_animals else ((),)
    worker_options: tuple[tuple[str, ...], ...] = ((),) + tuple((crop,) for crop in crops) if include_worker_lane else ((),)
    farmer_options: tuple[tuple[str, ...], ...] = tuple((crop,) for crop in crops) + tuple(
        (left, right) for left, right in crop_pairs
    )
    fertilizer_options = (False, True) if include_fertilizer else (False,)
    for farmer_crops, worker_crop, animals, fertilize, worker_days, market_orders in product(
        farmer_options, worker_options, animal_options, fertilizer_options, worker_day_options, market_order_options
    ):
        worker_crops = tuple(worker_crop)
        workers = (1 if worker_crops else 0) + (1 if animals else 0)
        configuration = {
            "crops": farmer_crops,
            "worker_crops": worker_crops,
            "animals": animals,
            "workers": workers,
            "fertilize": fertilize,
            "worker_days": worker_days,
            "opening_market_orders": market_orders,
            "steps": steps,
        }
        rewards = []
        for seed in training_seeds:
            result = run_episode(make_full_physical_agent(**configuration), seed=seed, steps=steps, opponent=opponent)
            if result.statuses != ["DONE", "DONE"]:
                raise RuntimeError(f"route failed for {configuration} on seed {seed}")
            rewards.append(float(result.rewards[0]))
        candidates.append({**configuration, "rewards": rewards, "mean_reward": sum(rewards) / len(rewards)})
    selected = max(candidates, key=lambda item: (item["mean_reward"], repr(item)))
    holdout_rewards = []
    for seed in holdout_seeds:
        result = run_episode(
            make_full_physical_agent(
                crops=tuple(selected["crops"]),
                worker_crops=tuple(selected["worker_crops"]),
                animals=tuple(selected["animals"]),
                workers=selected["workers"],
                fertilize=selected["fertilize"],
                worker_days=selected["worker_days"],
                opening_market_orders=tuple(tuple(order) for order in selected["opening_market_orders"]),
                steps=selected["steps"],
            ),
            seed=seed,
            steps=steps,
            opponent=opponent,
        )
        if result.statuses != ["DONE", "DONE"]:
            raise RuntimeError(f"holdout route failed for seed {seed}")
        holdout_rewards.append(float(result.rewards[0]))
    return {
        "selected": selected,
        "candidates": candidates,
        "holdout_rewards": holdout_rewards,
        "holdout_mean_reward": sum(holdout_rewards) / len(holdout_rewards) if holdout_rewards else None,
    }
