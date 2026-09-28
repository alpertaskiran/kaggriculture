"""Reusable seeded Kaggriculture episode and trajectory utilities."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from kaggle_environments import make


def _plain(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return value


@dataclass
class Frame:
    step: int
    observation: dict[str, Any]
    action: dict[str, Any]
    reward: float
    status: str


@dataclass
class EpisodeResult:
    seed: int
    frames: list[Frame]
    statuses: list[str]
    rewards: list[float]

    def write_json(self, path: str | Path) -> None:
        payload = asdict(self)
        Path(path).write_text(json.dumps(_plain(payload), indent=2) + "\n")


def run_episode(
    policy: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    seed: int,
    steps: int = 720,
    opponent: Callable[[dict[str, Any]], dict[str, Any]] | str = "pass",
) -> EpisodeResult:
    env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
    env.run([policy, opponent])
    frames = [
        Frame(
            step=index,
            observation=_plain(row[0].observation),
            action=_plain(row[0].action),
            reward=float(row[0].reward or 0),
            status=str(row[0].status),
        )
        for index, row in enumerate(env.steps)
    ]
    final = env.steps[-1]
    return EpisodeResult(
        seed=seed,
        frames=frames,
        statuses=[str(state.status) for state in final],
        rewards=[float(state.reward or 0) for state in final],
    )
