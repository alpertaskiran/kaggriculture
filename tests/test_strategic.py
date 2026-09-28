from agriculture_kaggle.strategic import (
    StrategicAction,
    StrategicBeamPlanner,
    StrategicState,
    advance_day,
    apply_action,
    estimate_plan_value,
    initial_strategic_state,
    plan_season,
)


def test_initial_strategic_state_matches_game_defaults():
    state = initial_strategic_state()

    assert state.day == 0
    assert state.cash == 3000
    assert state.land_quadrants == 1
    assert state.workers == 1
    assert state.crops == ()


def test_buy_seed_returns_new_state_and_reduces_cash():
    state = initial_strategic_state()
    updated = apply_action(state, StrategicAction("BUY_SEED", ("MELON", 1)))

    assert updated is not None
    assert updated is not state
    assert updated.cash == 2920
    assert updated.seeds == (("MELON", 1),)
    assert state.cash == 3000


def test_unaffordable_action_is_rejected_without_mutation():
    state = StrategicState(day=0, cash=10, land_quadrants=1, workers=1)

    assert apply_action(state, StrategicAction("BUY_ANIMAL", ("COW", 1))) is None
    assert state.cash == 10


def test_action_values_are_structurally_equal():
    assert StrategicAction("HOLD") == StrategicAction("HOLD")


def test_crop_value_does_not_appear_before_first_yield_day():
    state = apply_action(initial_strategic_state(), StrategicAction("BUY_SEED", ("MELON", 1)))
    state = apply_action(state, StrategicAction("PLANT_BATCH", ("MELON", 1)))

    early = advance_day(state)
    assert early is not None
    assert early.expected_value == 0


def test_transition_advances_day_and_adds_later_crop_value():
    state = StrategicState(day=10, cash=2920, crops=(("MELON", 1),))

    updated = advance_day(state)

    assert updated is not None
    assert updated.day == 11
    assert updated.expected_value > 0


def test_plan_value_includes_cash_and_expected_production():
    state = StrategicState(cash=100, expected_value=25)

    assert estimate_plan_value(state) == 125


def test_beam_planner_is_deterministic_and_respects_width():
    planner = StrategicBeamPlanner(width=3)

    first = planner.plan(initial_strategic_state(), days=3)
    second = planner.plan(initial_strategic_state(), days=3)

    assert first == second
    assert len(first) <= 3
    assert first[0].actions_by_day


def test_season_plan_contains_one_action_per_day():
    result = plan_season(initial_strategic_state(), days=4, width=4)

    assert len(result.actions_by_day) == 4
    assert result.final_state.day == 4


def test_planner_can_choose_a_second_plot_and_crop_mix():
    result = plan_season(initial_strategic_state(), days=30, width=64)

    assert sum(quantity for _, quantity in result.final_state.crops) >= 2
    assert len(result.final_state.crops) >= 2


def test_animal_purchase_requires_worker_capacity_and_records_allocation():
    state = initial_strategic_state()
    state = apply_action(state, StrategicAction("BUY_ANIMAL", ("COW", 1)))
    state = apply_action(state, StrategicAction("ASSIGN_WORKER", ("ANIMALS", 1)))

    assert state is not None
    assert state.animals == (("COW", 1),)
    assert state.worker_allocations == (("ANIMALS", 1),)
