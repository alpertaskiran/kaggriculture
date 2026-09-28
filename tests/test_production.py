from agriculture_kaggle.production import (
    WorkerQueue,
    animal_care_cycle,
    animal_care_queue,
    generate_multi_plot_route,
    generate_production_route,
    manhattan_moves,
    route_from_strategic_plan,
)
from agriculture_kaggle.simulation import run_episode
from agriculture_kaggle.strategic import initial_strategic_state, plan_season
from agriculture_kaggle.training import make_production_agent


def test_manhattan_moves_reaches_target():
    moves = manhattan_moves((4, 4), (3, 4))

    assert moves == ["WEST"]


def test_worker_queue_pads_missing_actions_with_pass():
    queue = WorkerQueue({"farmer": ["WEST", "PLANT"], "hand-1": ["WATER"]})

    assert queue.action("farmer", 0) == "WEST"
    assert queue.action("farmer", 2) == "PASS"
    assert queue.actions(0, ("farmer", "hand-1")) == ["WEST", "WATER"]
    assert queue.actions(1, ("farmer", "hand-1")) == ["PLANT", "PASS"]


def test_animal_care_cycle_has_one_action_per_turn():
    assert animal_care_cycle() == ["FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER"]


def test_animal_care_queue_schedules_daily_needs_and_periodic_harvest():
    queue = animal_care_queue(days=3, production_interval=2)

    assert queue[:4] == ["FEED", "CARE", "PASS", "COLLECT_FERTILIZER"]
    assert queue[24:28] == ["FEED", "CARE", "HARVEST", "COLLECT_FERTILIZER"]


def test_production_route_contains_full_crop_lifecycle():
    route = generate_production_route(steps=720, crop="WHEAT")
    farmer_actions = [turn["farmer"][0] for turn in route]

    assert len(route) == 720
    assert route[0]["market"] == [["BUY_SEED", "WHEAT", 1]]
    assert "WEST" in farmer_actions
    assert ["PLANT", "WHEAT"] in [turn["farmer"] for turn in route]
    assert "WATER" in farmer_actions
    assert "HARVEST" in farmer_actions
    assert "EAST" in farmer_actions
    assert "DROP" in farmer_actions
    assert route[-2]["market"] == [["SELL", "WHEAT", 3]]


def test_production_agent_completes_and_sells_real_harvest():
    result = run_episode(make_production_agent("WHEAT"), seed=7, steps=720)

    assert result.statuses == ["DONE", "DONE"]
    assert result.rewards[0] > 3000


def test_strategic_plan_compiles_to_a_full_physical_route():
    plan = plan_season(initial_strategic_state(), days=4, width=4)
    route = route_from_strategic_plan(plan, steps=720)

    assert len(route) == 720
    assert any(turn["market"] for turn in route)
    assert any(turn["farmer"] == ["HARVEST"] for turn in route)


def test_multi_plot_route_buys_and_plants_two_crops():
    route = generate_multi_plot_route(crops=("WHEAT", "MELON"), steps=720)

    assert route[0]["market"] == [
        ["BUY_SEED", "WHEAT", 1],
        ["BUY_SEED", "MELON", 1],
    ]
    assert ["PLANT", "WHEAT"] in [turn["farmer"] for turn in route]
    assert ["PLANT", "MELON"] in [turn["farmer"] for turn in route]
    assert len(route) == 720


def test_multi_plot_agent_produces_more_than_single_plot_baseline():
    from agriculture_kaggle.production import make_multi_plot_agent

    result = run_episode(make_multi_plot_agent(), seed=7, steps=720)

    assert result.statuses == ["DONE", "DONE"]
    assert result.rewards[0] > 4318


def test_full_physical_route_compiles_workers_and_animals():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(crops=("WHEAT", "MELON"), animals=("COW",), workers=1, steps=720)

    assert ["BUY_ANIMAL", "COW", 1] in route[0]["market"]
    assert ["HIRE"] in route[0]["market"]
    assert len(route[1]["hands"]) == 1
    assert route[1]["hands"][0] == ["PICKUP", "COW", 1]
    assert ["FEED"] in [turn["hands"][0] for turn in route]
    assert ["CARE"] in [turn["hands"][0] for turn in route]
    assert ["COLLECT_FERTILIZER"] in [turn["hands"][0] for turn in route]


def test_full_physical_route_places_animal_in_official_engine():
    from agriculture_kaggle.production import make_full_physical_agent

    result = run_episode(
        make_full_physical_agent(crops=("WHEAT",), animals=("COW",), workers=1),
        seed=7,
        steps=120,
    )

    assert result.statuses == ["DONE", "DONE"]


def test_goose_route_uses_a_coop_setup_action():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(crops=("WHEAT",), animals=("GOOSE",), workers=1, steps=120)

    assert route[4]["hands"] == [["BUILD_COOP"]]


def test_animal_selector_can_reject_unprofitable_livestock():
    from agriculture_kaggle.production import select_animal_configuration

    report = select_animal_configuration(crops=("WHEAT",), training_seeds=(7,), steps=720)

    assert report["selected"]["animals"] == []
    assert len(report["candidates"]) == 4


def test_animal_selector_prefers_cow_for_melon_route_after_liquidation():
    from agriculture_kaggle.production import select_animal_configuration

    report = select_animal_configuration(crops=("MELON",), training_seeds=(7,), workers=1, steps=720)

    assert report["selected"]["animals"] == ["COW"]


def test_worker_crop_queue_contains_daily_movement_and_care_actions():
    from agriculture_kaggle.production import worker_crop_queue

    queue = worker_crop_queue(crop="WHEAT", days=5)

    assert queue[1] == ["WEST"]
    assert ["PLANT", "WHEAT"] in queue
    assert ["WATER"] in queue
    assert ["HARVEST"] in queue


def test_full_route_supports_multiple_independent_worker_lanes():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(
        crops=("MELON",), worker_crops=("WHEAT", "CARROT"), workers=2, steps=720
    )

    assert route[0]["market"].count(["BUY_SEED", "WHEAT", 1]) == 1
    assert route[0]["market"].count(["BUY_SEED", "CARROT", 1]) == 1
    assert len(route[1]["hands"]) == 2
    assert ["PLANT", "WHEAT"] in [turn["hands"][0] for turn in route]
    assert ["PLANT", "CARROT"] in [turn["hands"][1] for turn in route]


def test_full_route_composes_animal_care_with_crop_worker():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(
        crops=("MELON",), worker_crops=("WHEAT",), animals=("GOOSE",), workers=2, steps=720
    )

    assert route[5]["hands"][0] == ["PLACE", "GOOSE"]
    assert route[1]["hands"][1] == ["WEST"]
    assert ["FEED"] in [turn["hands"][0] for turn in route]
    assert ["PLANT", "WHEAT"] in [turn["hands"][1] for turn in route]


def test_worker_tenure_limits_rehiring_market_orders():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(
        crops=("MELON",), worker_crops=("WHEAT",), workers=1, worker_days=5, steps=720
    )

    assert sum(["HIRE"] in turn["market"] for turn in route) == 5


def test_animal_route_liquidates_animal_products():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(crops=("MELON",), animals=("GOOSE",), workers=1, steps=720)

    assert ["SELL", "EGG", 100] in route[-2]["market"]
    assert ["SELL", "FERTILIZER", 100] in route[-2]["market"]


def test_physical_route_accepts_opening_market_orders():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(
        crops=("MELON",), opening_market_orders=(("BUY_PRODUCT", "WHEAT", 5),), steps=120
    )

    assert ["BUY_PRODUCT", "WHEAT", 5] in route[0]["market"]


def test_two_animals_get_independent_structures():
    from agriculture_kaggle.production import generate_full_physical_route

    route = generate_full_physical_route(
        crops=("MELON",), animals=("GOOSE", "COW"), workers=2, steps=120
    )

    assert route[4]["hands"] == [["BUILD_COOP"], ["WEST"]]
    assert route[5]["hands"] == [["PLACE", "GOOSE"], ["BUILD_PASTURE"]]
    assert route[6]["hands"][1] == ["PLACE", "COW"]


def test_physical_search_returns_an_official_engine_configuration():
    from agriculture_kaggle.production import search_physical_configurations

    report = search_physical_configurations(
        training_seeds=(7,), holdout_seeds=(1234,), crops=("WHEAT", "MELON"), include_animals=False, steps=120
    )

    assert report["selected"]["mean_reward"] == max(item["mean_reward"] for item in report["candidates"])
    assert report["selected"]["rewards"]
    assert len(report["holdout_rewards"]) == 1


def test_physical_search_includes_two_plot_farmer_plans():
    from agriculture_kaggle.production import search_physical_configurations

    report = search_physical_configurations(
        training_seeds=(7,), crops=("WHEAT",), crop_pairs=(("WHEAT", "MELON"),),
        include_worker_lane=False, include_animals=False, steps=720
    )

    assert any(item["crops"] == ("WHEAT", "MELON") for item in report["candidates"])
