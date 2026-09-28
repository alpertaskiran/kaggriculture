import argparse
import json
from pathlib import Path

from run_local import load_agent

from agriculture_kaggle.training import optimize_route_policy


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize route-planner width on held-out seeds.")
    parser.add_argument("--training-seeds", type=int, nargs="+", default=[7, 1234])
    parser.add_argument("--holdout-seeds", type=int, nargs="+", default=[543043])
    parser.add_argument("--widths", type=int, nargs="+", default=[1, 2, 4, 8])
    parser.add_argument("--opponent", action="append", default=None)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    opponent_names = args.opponent or ["pass", "random"]
    opponents = [load_agent(value) for value in opponent_names]
    report = optimize_route_policy(
        candidate_widths=args.widths,
        training_seeds=args.training_seeds,
        holdout_seeds=args.holdout_seeds,
        opponents=opponents,
    )
    encoded = json.dumps(report, indent=2)
    print(encoded)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n")


if __name__ == "__main__":
    main()
