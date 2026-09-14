"""Simple Joe: a deterministic route follower without opponent modeling."""

from typing import Any

from agriculture_kaggle.simple_joe.route import action_for_step
from agriculture_kaggle.simple_joe.safety import liquidate_if_terminal, repair_action


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    if "step" not in observation:
        return {"farmer": ["PASS"], "hands": [], "market": []}
    step = int(observation["step"])
    action = action_for_step(step)
    action = repair_action(action, observation)
    return liquidate_if_terminal(action, observation)
