"""Readable baseline route for Simple Joe."""

SEASON_STEPS = 720


def action_for_step(step: int) -> dict:
    """Return Simple Joe's planned action for one turn."""
    if step == 0:
        return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}
    return {"farmer": ["PASS"], "hands": [], "market": []}
