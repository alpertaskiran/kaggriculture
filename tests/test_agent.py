from agriculture_kaggle.agent import agent
from agriculture_kaggle.local import DEFAULT_SEED, build_configuration


def test_first_turn_buys_one_wheat_seed():
    action = agent({"step": 0})

    assert action == {
        "farmer": ["PASS"],
        "hands": [],
        "market": [["BUY_SEED", "WHEAT", 1]],
    }


def test_later_turn_passes_without_market_orders():
    action = agent({"step": 1})

    assert action == {"farmer": ["PASS"], "hands": [], "market": []}


def test_missing_step_is_safe():
    action = agent({})

    assert action == {"farmer": ["PASS"], "hands": [], "market": []}


def test_local_configuration_uses_reproducible_default_seed():
    assert build_configuration() == {"episodeSteps": 10, "seed": DEFAULT_SEED}


def test_local_configuration_accepts_seed_override():
    assert build_configuration(12345) == {"episodeSteps": 10, "seed": 12345}
