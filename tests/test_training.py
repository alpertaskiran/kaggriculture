from agriculture_kaggle.optimization import BeamPlanner, DailyState, generate_route
from agriculture_kaggle.training import (
    evaluate_population,
    make_route_agent,
    make_strategic_agent,
    optimize_route_policy,
    train_tabular_policy,
)


def test_generate_route_has_one_action_per_turn():
    state = DailyState(day=0, cash=3000, crop_count=0, animal_count=0, shed_load=0, shops=())

    route = generate_route(state, days=2, planner=BeamPlanner(width=2))

    assert len(route) == 48
    assert route[0]["market"] == [["BUY_SEED", "MELON", 1]]
    assert route[24]["farmer"] == ["PASS"]


def test_population_evaluation_reports_both_seats():
    policy = lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}

    summary = evaluate_population(policy, seeds=[7], opponents=["pass"])

    assert summary["games"] == 2
    assert summary["completed"] == 2
    assert len(summary["results"]) == 2


def test_route_agent_compiles_a_full_tape_once():
    policy = make_route_agent(BeamPlanner(width=2))

    first = policy({"step": 0, "day": 0, "town": {}, "farms": [{"money": 3000, "tiles": []}], "private": {"shed": {}, "inventories": []}})
    later = policy({"step": 24, "day": 1, "town": {}, "farms": [{"money": 3000, "tiles": []}], "private": {"shed": {}, "inventories": []}})

    assert first["farmer"] == ["PASS"]
    assert later["farmer"] == ["PASS"]


def test_optimizer_returns_training_and_holdout_reports():
    result = optimize_route_policy(
        candidate_widths=[1],
        training_seeds=[7],
        holdout_seeds=[1234],
        opponents=["pass"],
    )

    assert result["selected_width"] == 1
    assert result["holdout"]["games"] == 2


def test_tabular_training_returns_exportable_policy():
    result = train_tabular_policy(episodes=1, seeds=[7], opponents=["pass"])

    assert result["episodes"] == 1
    assert result["policy"]


def test_strategic_agent_returns_compiled_actions():
    policy = make_strategic_agent(days=4, width=4)

    first = policy({"step": 0})
    later = policy({"step": 97})

    assert "market" in first
    assert later["farmer"] in (["WEST"], ["HARVEST"], ["EAST"], ["DROP"], ["PASS"])
