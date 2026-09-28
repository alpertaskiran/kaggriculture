import json

from agriculture_kaggle.optimization import BeamPlanner, DailyState, encode_observation
from agriculture_kaggle.rl import TabularPolicy
from agriculture_kaggle.simulation import run_episode


def test_run_episode_records_seeded_trajectory():
    result = run_episode(lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}, seed=7, steps=2)

    assert result.seed == 7
    assert len(result.frames) == 2
    assert result.statuses == ["DONE", "DONE"]


def test_encode_observation_extracts_daily_planning_state():
    state = encode_observation({
        "step": 48,
        "public": {"town": {"unlocked_shops": ["YARN_STORE"]}},
        "private": {"cash": 2500, "shed": {"WHEAT": 4}, "animals": []},
    })

    assert state.day == 2
    assert state.cash == 2500
    assert state.shops == ("YARN_STORE",)
    assert state.shed_load == 4


def test_beam_planner_prefers_affordable_high_value_action():
    planner = BeamPlanner(width=2)
    state = DailyState(day=0, cash=3000, crop_count=0, animal_count=0, shed_load=0, shops=())

    plan = planner.plan(state, days=1)

    assert plan[0].name == "BUY_SEED"
    assert plan[0].payload == ("MELON", 1)


def test_trajectory_can_be_written_as_json(tmp_path):
    result = run_episode(lambda obs: {"farmer": ["PASS"], "hands": [], "market": []}, seed=7, steps=1)
    path = tmp_path / "trajectory.json"
    result.write_json(path)

    assert json.loads(path.read_text())["seed"] == 7


def test_tabular_policy_updates_and_round_trips():
    policy = TabularPolicy()
    policy.update("day0:yarn", "WOOL", 10, "day1:yarn")
    restored = TabularPolicy.from_export(policy.export())

    assert restored.value("day0:yarn", "WOOL") > 0
