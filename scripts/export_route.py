import argparse
import json
from pathlib import Path

from agriculture_kaggle.optimization import BeamPlanner, DailyState, generate_route


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a planner-generated action tape.")
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--cash", type=float, default=3000)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    state = DailyState(day=0, cash=args.cash, crop_count=0, animal_count=0, shed_load=0, shops=())
    route = generate_route(state, days=args.days, planner=BeamPlanner(width=args.width))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(route, indent=2) + "\n")
    print(f"wrote {len(route)} actions to {args.output}")


if __name__ == "__main__":
    main()
