import argparse
import importlib.util
from collections.abc import Callable
from pathlib import Path

from kaggle_environments import make

from agriculture_kaggle.local import DEFAULT_SEED
from main import agent


def load_agent(value: str) -> Callable:
    if value == "pass":
        return lambda observation: {"farmer": ["PASS"], "hands": [], "market": []}
    if value == "random":
        from kaggle_environments.envs.kaggriculture.kaggriculture import random_agent
        return random_agent
    path = Path(value).resolve()
    spec = importlib.util.spec_from_file_location("kaggriculture_opponent", path)
    if spec is None or spec.loader is None:
        raise TypeError(f"Could not load opponent: {value}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    candidate = getattr(module, "agent", getattr(module, "main", None))
    if not callable(candidate):
        raise TypeError(f"{value} must expose agent(observation) or main(observation)")
    return candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local Kaggriculture episode.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--steps", type=int, default=720)
    parser.add_argument("--opponent", default="pass")
    parser.add_argument("--render", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.steps < 1:
        raise ValueError("--steps must be positive")
    environment = make("kaggriculture", configuration={"episodeSteps": args.steps, "seed": args.seed})
    environment.run([agent, load_agent(args.opponent)])
    if args.render:
        environment.render(mode="ipython", width=800, height=800)
    for player, state in enumerate(environment.steps[-1]):
        print(f"player={player} status={state.status} reward={state.reward}")


if __name__ == "__main__":
    main()
