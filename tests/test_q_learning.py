from agriculture_kaggle.q_learning import (
    QLearningConfig,
    TabularQPolicy,
    enumerate_actions,
    state_key,
    train_q_policy,
)
from agriculture_kaggle.strategic import initial_strategic_state


def test_state_key_is_hashable_and_deterministic():
    state = initial_strategic_state()

    assert state_key(state) == state_key(state)
    assert isinstance(state_key(state), tuple)


def test_action_enumerator_returns_legal_seed_actions():
    actions = enumerate_actions(initial_strategic_state())

    assert any(action.name == "BUY_SEED" for action in actions)
    assert all(action.name != "BUY_ANIMAL" or action.payload for action in actions)


def test_action_enumerator_exposes_market_and_reserve_actions():
    actions = enumerate_actions(initial_strategic_state())

    assert any(action == type(actions[0])("BUY_PRODUCT", ("WHEAT", 10)) for action in actions)
    assert any(action == type(actions[0])("BUY_PRODUCT", ("FERTILIZER", 10)) for action in actions)
    assert any(action.name == "RESERVE" for action in actions)


def test_q_policy_updates_and_exports_values():
    policy = TabularQPolicy()
    state = initial_strategic_state()
    action = enumerate_actions(state)[0]

    policy.update(state, action, reward=10, next_state=state, next_actions=[action], alpha=1.0, gamma=0.0)

    assert policy.value(state, action) == 10
    assert policy.export()


def test_training_is_seeded_and_returns_policy():
    result = train_q_policy(episodes=2, seeds=[7], config=QLearningConfig(epsilon=0.0))

    assert result.episodes == 2
    assert result.policy.export()
