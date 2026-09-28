"""Search official-engine physical route configurations."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from agriculture_kaggle.production import (
    make_full_physical_agent,
    search_physical_configurations,
)
from agriculture_kaggle.training import evaluate_population


def load_opponent(path: str):
    module_path = Path(path)
    spec = importlib.util.spec_from_file_location("physical_opponent", module_path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load opponent: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    opponent = getattr(module, "agent", None) or getattr(module, "main", None)
    if not callable(opponent):
        raise TypeError(f"{path} must expose agent(observation) or main(observation)")
    return opponent


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-seeds", nargs="+", type=int, default=[7, 1234])
    parser.add_argument("--holdout-seeds", nargs="+", type=int, default=[543043])
    parser.add_argument("--crops", nargs="+", default=["WHEAT", "MELON"])
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--no-workers", action="store_true")
    parser.add_argument("--no-animals", action="store_true")
    parser.add_argument("--no-fertilizer", action="store_true")
    parser.add_argument(
        "--wheat-orders", nargs="*", type=int, default=[],
        help="candidate opening BUY_PRODUCT WHEAT quantities",
    )
    parser.add_argument(
        "--worker-days", nargs="*", type=int, default=[],
        help="candidate worker tenures; omit to test full-season workers only",
    )
    parser.add_argument("--json", dest="json_path")
    parser.add_argument("--opponent", help="Python file exposing agent() or main() for holdout comparison")
    args = parser.parse_args()
    opponent = load_opponent(args.opponent) if args.opponent else "pass"
    market_orders = [()]
    market_orders.extend((("BUY_PRODUCT", "WHEAT", quantity),) for quantity in args.wheat_orders)
    report = search_physical_configurations(
        training_seeds=args.training_seeds,
        holdout_seeds=args.holdout_seeds,
        crops=tuple(args.crops),
        crop_pairs=(("WHEAT", "MELON"),),
        include_worker_lane=not args.no_workers,
        include_animals=not args.no_animals,
        include_fertilizer=not args.no_fertilizer,
        worker_day_options=(None, *args.worker_days) if args.worker_days else (None,),
        steps=args.steps,
        opponent=opponent,
        market_order_options=tuple(market_orders),
    )
    if args.opponent and report["holdout_rewards"]:
        selected = report["selected"]
        candidate = make_full_physical_agent(
            crops=tuple(selected["crops"]),
            worker_crops=tuple(selected["worker_crops"]),
            animals=tuple(selected["animals"]),
            workers=selected["workers"],
            fertilize=selected["fertilize"],
            worker_days=selected["worker_days"],
            opening_market_orders=tuple(tuple(order) for order in selected["opening_market_orders"]),
            steps=selected["steps"],
        )
        report["opponent_report"] = evaluate_population(
            candidate,
            seeds=args.holdout_seeds,
            opponents=[opponent],
            steps=args.steps,
        )
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
