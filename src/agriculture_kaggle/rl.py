"""Lightweight tabular policy utilities for high-level route experiments.

This module is development-facing. The Kaggle runtime does not train; it only
uses exported route or policy parameters.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

MODES = ("BALANCED", "MILK", "WOOL", "EGG", "LIQUIDATE")


@dataclass
class TabularPolicy:
    learning_rate: float = 0.15
    discount: float = 0.95
    values: dict[tuple[str, str], float] = field(default_factory=dict)

    def value(self, state: str, mode: str) -> float:
        return self.values.get((state, mode), 0.0)

    def choose(self, state: str, *, epsilon: float = 0.0, rng: random.Random | None = None) -> str:
        rng = rng or random.Random()
        if rng.random() < epsilon:
            return rng.choice(MODES)
        return max(MODES, key=lambda mode: self.value(state, mode))

    def update(self, state: str, mode: str, reward: float, next_state: str) -> None:
        old = self.value(state, mode)
        future = max(self.value(next_state, candidate) for candidate in MODES)
        target = reward + self.discount * future
        self.values[(state, mode)] = old + self.learning_rate * (target - old)

    def export(self) -> dict[str, float]:
        return {f"{state}|{mode}": value for (state, mode), value in self.values.items()}

    @classmethod
    def from_export(cls, values: dict[str, float]) -> TabularPolicy:
        policy = cls()
        for key, value in values.items():
            state, mode = key.split("|", 1)
            policy.values[(state, mode)] = float(value)
        return policy
