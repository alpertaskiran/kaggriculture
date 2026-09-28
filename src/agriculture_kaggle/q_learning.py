"""Tabular Q-learning over the compact strategic planning model.

This is the learning layer, not the Kaggle submission runtime. Policies must
still be compiled to physical routes and validated in the official engine.
"""

from __future__ import annotations

import random
from collections.abc import Iterable
from dataclasses import dataclass

from agriculture_kaggle.rl_environment import StrategicEnvironment
from agriculture_kaggle.strategic import (
    ANIMAL_COST,
    CROP_COST,
    StrategicAction,
    StrategicState,
    advance_day,
    apply_action,
    estimate_plan_value,
    initial_strategic_state,
)


def state_key(state: StrategicState) -> tuple:
    return (
        state.day,
        int(state.cash // 100),
        state.land_quadrants,
        state.workers,
        state.seeds,
        state.crops,
        state.animals,
        state.fertilizer,
        state.worker_allocations,
        state.shops,
        state.crop_ages,
        state.market_prices,
        state.shop_demand,
        state.opponent_signal,
        state.reserves,
    )


def enumerate_actions(state: StrategicState) -> list[StrategicAction]:
    candidates = [StrategicAction("HOLD")]
    market_quantities = (1, 5, 10, 30)
    for quantity in market_quantities:
        candidates.append(StrategicAction("BUY_PRODUCT", ("WHEAT", quantity)))
        candidates.append(StrategicAction("BUY_PRODUCT", ("FERTILIZER", quantity)))
    shed = dict(state.shed)
    for product, quantity in shed.items():
        for bucket in (1, 5, 10, quantity):
            if 0 < bucket <= quantity:
                candidates.append(StrategicAction("SELL", (product, bucket)))
    for product in ("WHEAT", "FERTILIZER", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"):
        for quantity in (1, 5, 10, 30):
            candidates.append(StrategicAction("RESERVE", (product, quantity)))
    for crop, cost in CROP_COST.items():
        if state.cash >= cost:
            candidates.append(StrategicAction("BUY_SEED", (crop, 1)))
            if dict(state.seeds).get(crop, 0):
                candidates.append(StrategicAction("PLANT_BATCH", (crop, 1)))
    for animal, cost in ANIMAL_COST.items():
        if state.cash >= cost:
            candidates.append(StrategicAction("BUY_ANIMAL", (animal, 1)))
    if state.cash >= 100:
        candidates.append(StrategicAction("BUY_FERTILIZER", (1,)))
    legal: list[StrategicAction] = []
    for action in candidates:
        if apply_action(state, action) is not None:
            legal.append(action)
    return legal


@dataclass(frozen=True)
class QLearningConfig:
    alpha: float = 0.2
    gamma: float = 0.95
    epsilon: float = 0.2
    horizon_days: int = 30


class TabularQPolicy:
    def __init__(self) -> None:
        self.values: dict[tuple[tuple, StrategicAction], float] = {}

    def value(self, state: StrategicState, action: StrategicAction) -> float:
        return self.values.get((state_key(state), action), 0.0)

    def choose(
        self,
        state: StrategicState,
        actions: Iterable[StrategicAction],
        *,
        epsilon: float,
        rng: random.Random,
    ) -> StrategicAction:
        options = list(actions)
        if not options:
            return StrategicAction("HOLD")
        if rng.random() < epsilon:
            return rng.choice(options)
        return max(options, key=lambda action: (-self.value(state, action), repr(action)))

    def update(
        self,
        state: StrategicState,
        action: StrategicAction,
        reward: float,
        next_state: StrategicState,
        next_actions: Iterable[StrategicAction],
        *,
        alpha: float,
        gamma: float,
    ) -> None:
        old = self.value(state, action)
        future = max((self.value(next_state, candidate) for candidate in next_actions), default=0.0)
        target = reward + gamma * future
        self.values[(state_key(state), action)] = old + alpha * (target - old)

    def export(self) -> dict[str, float]:
        return {repr(key): value for key, value in self.values.items()}


@dataclass(frozen=True)
class QLearningResult:
    episodes: int
    policy: TabularQPolicy
    rewards: tuple[float, ...]


def train_official_q_policy(
    *, episodes: int, seeds: Iterable[int], config: QLearningConfig | None = None,
) -> QLearningResult:
    """Train tabular values using rewards emitted by the official engine."""
    config = config or QLearningConfig()
    seeds = list(seeds)
    if episodes < 1 or not seeds:
        raise ValueError("episodes and seeds must be non-empty")
    policy = TabularQPolicy()
    rewards: list[float] = []
    for episode in range(episodes):
        environment = StrategicEnvironment(seed=seeds[episode % len(seeds)])
        state = environment.reset()
        rng = random.Random(seeds[episode % len(seeds)] + episode)
        total = 0.0
        for _ in range(config.horizon_days):
            actions = enumerate_actions(state)
            action = policy.choose(state, actions, epsilon=config.epsilon, rng=rng)
            next_state, reward, done, _ = environment.step(action)
            policy.update(state, action, reward, next_state, enumerate_actions(next_state), alpha=config.alpha, gamma=config.gamma)
            state, total = next_state, total + reward
            if done:
                break
        rewards.append(total)
    return QLearningResult(episodes=episodes, policy=policy, rewards=tuple(rewards))


def train_q_policy(
    *,
    episodes: int,
    seeds: Iterable[int],
    config: QLearningConfig | None = None,
) -> QLearningResult:
    config = config or QLearningConfig()
    seeds = list(seeds)
    if episodes < 1 or not seeds:
        raise ValueError("episodes and seeds must be non-empty")
    policy = TabularQPolicy()
    rewards: list[float] = []
    for episode in range(episodes):
        seed = seeds[episode % len(seeds)]
        rng = random.Random(seed + episode)
        state = initial_strategic_state()
        start_value = estimate_plan_value(state)
        for _ in range(config.horizon_days):
            actions = enumerate_actions(state)
            action = policy.choose(state, actions, epsilon=config.epsilon, rng=rng)
            next_state = advance_day(state, (action,)) or state
            reward = estimate_plan_value(next_state) - estimate_plan_value(state)
            policy.update(state, action, reward, next_state, enumerate_actions(next_state), alpha=config.alpha, gamma=config.gamma)
            state = next_state
        rewards.append(estimate_plan_value(state) - start_value)
    return QLearningResult(episodes=episodes, policy=policy, rewards=tuple(rewards))
