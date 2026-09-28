import argparse
import json
from pathlib import Path

from agriculture_kaggle.q_learning import QLearningConfig, train_q_policy


def main() -> None:
    parser = argparse.ArgumentParser(description="Train tabular Q-values on strategic model episodes.")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seeds", type=int, nargs="+", default=[7, 1234, 543043])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epsilon", type=float, default=0.2)
    args = parser.parse_args()
    result = train_q_policy(
        episodes=args.episodes,
        seeds=args.seeds,
        config=QLearningConfig(epsilon=args.epsilon),
    )
    payload = {
        "episodes": result.episodes,
        "rewards": list(result.rewards),
        "values": result.policy.export(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {len(payload['values'])} Q-values to {args.output}")


if __name__ == "__main__":
    main()
