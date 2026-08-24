from agriculture_kaggle.agent import agent


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
