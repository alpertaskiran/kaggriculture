import argparse
from pathlib import Path

from agriculture_kaggle.simulation import run_episode
from main import agent


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect a seeded Kaggriculture trajectory.")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_episode(agent, seed=args.seed, steps=args.steps)
    result.write_json(args.output)
    print(f"wrote {len(result.frames)} frames to {args.output}")


if __name__ == "__main__":
    main()
