import argparse
import json
from pathlib import Path

from kaggle_environments import make
from run_local import load_agent

from main import agent

DEFAULT_SEEDS = [7, 1234, 543043]


def play(our_agent, opponent, seed: int, seat: int) -> dict:
    players = [our_agent, opponent] if seat == 0 else [opponent, our_agent]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run(players)
    states = env.steps[-1]
    rewards = [state.reward for state in states]
    ours, theirs = rewards if seat == 0 else rewards[::-1]
    return {"seed": seed, "seat": seat, "our_reward": ours, "opponent_reward": theirs,
            "margin": ours - theirs, "status": [state.status for state in states]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Kaggriculture agents.")
    parser.add_argument("--opponent", default="pass")
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS)
    parser.add_argument("--games-per-seed", type=int, default=1)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    opponent = load_agent(args.opponent)
    results = [play(agent, opponent, seed, seat)
               for seed in args.seeds for _ in range(args.games_per_seed) for seat in (0, 1)]
    wins = sum(row["margin"] > 0 for row in results)
    losses = sum(row["margin"] < 0 for row in results)
    summary = {"games": len(results), "wins": wins, "losses": losses,
               "draws": len(results) - wins - losses,
               "mean_margin": sum(row["margin"] for row in results) / len(results),
               "results": results}
    print(json.dumps(summary, indent=2))
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
