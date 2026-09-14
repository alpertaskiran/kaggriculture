"""Small, conservative runtime safeguards for Simple Joe."""


def repair_action(action: dict, observation: dict) -> dict:
    """Keep route output valid when optional observation data is incomplete."""
    repaired = {
        "farmer": list(action.get("farmer", ["PASS"]))[:1] or ["PASS"],
        "hands": list(action.get("hands", [])),
        "market": list(action.get("market", [])),
    }
    worker_count = len(observation.get("private", {}).get("inventories", []))
    if worker_count > 0:
        repaired["hands"] = repaired["hands"][: max(0, worker_count - 1)]
    return repaired


def liquidate_if_terminal(action: dict, observation: dict) -> dict:
    """Sell known shed inventory on the final action turn when possible."""
    step = observation.get("step", 0)
    if step < 718:
        return action
    shed = observation.get("private", {}).get("shed", {})
    orders = [["SELL", item, int(quantity)] for item, quantity in shed.items() if quantity > 0]
    return {**action, "market": orders[:10]}
