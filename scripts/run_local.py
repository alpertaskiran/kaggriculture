from kaggle_environments import make

from main import agent


def main() -> None:
    environment = make("kaggriculture", configuration={"episodeSteps": 10})
    environment.run([agent, "pass"])
    for player, state in enumerate(environment.steps[-1]):
        print(f"player={player} status={state.status} reward={state.reward}")


if __name__ == "__main__":
    main()
