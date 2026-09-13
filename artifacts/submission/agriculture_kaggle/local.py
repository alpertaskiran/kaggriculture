DEFAULT_SEED = 20260824


def build_configuration(seed: int = DEFAULT_SEED) -> dict[str, int]:
    return {"episodeSteps": 10, "seed": seed}
