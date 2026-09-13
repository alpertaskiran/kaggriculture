from typing import Any


def agent(observation: dict[str, Any]) -> dict[str, Any]:
    """Return a safe deterministic starter action for Kaggriculture."""
    if observation.get("step") == 0:
        return {
            "farmer": ["PASS"],
            "hands": [],
            "market": [["BUY_SEED", "WHEAT", 1]],
        }
    return {"farmer": ["PASS"], "hands": [], "market": []}
