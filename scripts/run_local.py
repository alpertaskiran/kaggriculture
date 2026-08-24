import argparse

from kaggle_environments import make

from agriculture_kaggle.local import DEFAULT_SEED, build_configuration
from main import agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local Kaggriculture smoke episode.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    environment = make("kaggriculture", configuration=build_configuration(args.seed))
    environment.run([agent, "pass"])
    for player, state in enumerate(environment.steps[-1]):
        print(f"player={player} status={state.status} reward={state.reward}")


if __name__ == "__main__":
    main()
