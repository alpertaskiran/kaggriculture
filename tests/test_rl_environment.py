from agriculture_kaggle.rl_environment import (
    StrategicEnvironment,
    compile_strategic_action,
)
from agriculture_kaggle.strategic import StrategicAction


def test_action_compiler_emits_official_market_action():
    action = compile_strategic_action(StrategicAction("BUY_SEED", ("WHEAT", 1)))

    assert action == {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", "WHEAT", 1]]}


def test_action_compiler_emits_buy_sell_market_orders():
    buy = compile_strategic_action(StrategicAction("BUY_PRODUCT", ("WHEAT", 10)))
    sell = compile_strategic_action(StrategicAction("SELL", ("MILK", 5)))

    assert buy["market"] == [["BUY_PRODUCT", "WHEAT", 10]]
    assert sell["market"] == [["SELL", "MILK", 5]]


def test_official_environment_reset_and_day_step():
    environment = StrategicEnvironment(seed=7)
    state = environment.reset()

    next_state, reward, done, info = environment.step(StrategicAction("HOLD"))

    assert state.day == 0
    assert next_state.day == 1
    assert isinstance(reward, float)
    assert done is False
    assert info["engine_step"] == 24
