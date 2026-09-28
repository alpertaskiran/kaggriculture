"""Offline policy evaluation and training helpers."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from kaggle_environments import make

from agriculture_kaggle.optimization import (
    BeamPlanner,
    encode_observation,
    generate_route,
)
from agriculture_kaggle.production import (
    generate_production_route,
    route_from_strategic_plan,
)
from agriculture_kaggle.rl import MODES, TabularPolicy
from agriculture_kaggle.strategic import initial_strategic_state, plan_season


def _resolve_opponent(opponent: Callable | str) -> Callable:
    if opponent == "pass":
        return lambda observation: {"farmer": ["PASS"], "hands": [], "market": []}
    if opponent == "random":
        from kaggle_environments.envs.kaggriculture.kaggriculture import random_agent

        return random_agent
    if callable(opponent):
        return opponent
    raise TypeError(f"Unsupported opponent: {opponent}")


def evaluate_population(
    policy: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    seeds: Iterable[int],
    opponents: Iterable[Callable | str],
    steps: int = 720,
) -> dict[str, Any]:
    seeds = list(seeds)
    opponents = list(opponents)
    results: list[dict[str, Any]] = []
    for seed in seeds:
        for opponent in opponents:
            resolved_opponent = _resolve_opponent(opponent)
            for seat in (0, 1):
                players = [policy, resolved_opponent] if seat == 0 else [resolved_opponent, policy]
                env = make("kaggriculture", configuration={"episodeSteps": steps, "seed": seed})
                env.run(players)
                states = env.steps[-1]
                rewards = [float(state.reward or 0) for state in states]
                ours, theirs = rewards if seat == 0 else rewards[::-1]
                opponent_label = opponent if isinstance(opponent, str) else getattr(opponent, "__name__", "callable")
                results.append({
                    "seed": seed,
                    "opponent": opponent_label,
                    "seat": seat,
                    "our_reward": ours,
                    "opponent_reward": theirs,
                    "margin": ours - theirs,
                    "status": [str(state.status) for state in states],
                })
    wins = sum(row["margin"] > 0 for row in results)
    losses = sum(row["margin"] < 0 for row in results)
    completed = sum(all(status == "DONE" for status in row["status"]) for row in results)
    return {
        "games": len(results),
        "wins": wins,
        "losses": losses,
        "draws": len(results) - wins - losses,
        "completed": completed,
        "mean_margin": sum(row["margin"] for row in results) / len(results) if results else 0.0,
        "results": results,
    }


def make_route_agent(planner: BeamPlanner) -> Callable[[dict[str, Any]], dict[str, Any]]:
    route: list[dict[str, Any]] | None = None

    def policy(observation: dict[str, Any]) -> dict[str, Any]:
        nonlocal route
        step = int(observation.get("step", 0))
        if step == 0 or route is None:
            route = generate_route(encode_observation(observation), planner=planner)
        if step >= len(route):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        return route[step]

    return policy


def make_production_agent(crop: str = "WHEAT") -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a stateful agent backed by a physical single-plot route."""
    route: list[dict[str, Any]] | None = None

    def policy(observation: dict[str, Any]) -> dict[str, Any]:
        nonlocal route
        step = int(observation.get("step", 0))
        if step == 0 or route is None:
            route = generate_production_route(crop=crop)
        if step >= len(route):
            return {"farmer": ["PASS"], "hands": [], "market": []}
        return route[step]

    return policy


def make_strategic_agent(*, days: int = 30, width: int = 32) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Compile one deterministic strategic plan into a physical agent tape."""
    route: list[dict[str, Any]] | None = None

    def policy(observation: dict[str, Any]) -> dict[str, Any]:
        nonlocal route
        step = int(observation.get("step", 0))
        if step == 0 or route is None:
            route = route_from_strategic_plan(plan_season(initial_strategic_state(), days=days, width=width))
        return route[step] if step < len(route) else {"farmer": ["PASS"], "hands": [], "market": []}

    return policy


def optimize_route_policy(
    *,
    candidate_widths: Iterable[int],
    training_seeds: Iterable[int],
    holdout_seeds: Iterable[int],
    opponents: Iterable[Callable | str],
) -> dict[str, Any]:
    training_seeds = list(training_seeds)
    holdout_seeds = list(holdout_seeds)
    opponents = list(opponents)
    candidates = []
    for width in candidate_widths:
        policy = make_route_agent(BeamPlanner(width=width))
        report = evaluate_population(policy, seeds=training_seeds, opponents=opponents)
        candidates.append({"width": width, "report": report})
    selected = max(candidates, key=lambda item: (item["report"]["mean_margin"], item["report"]["completed"]))
    holdout = evaluate_population(
        make_route_agent(BeamPlanner(width=selected["width"])),
        seeds=holdout_seeds,
        opponents=opponents,
    )
    return {"selected_width": selected["width"], "candidates": candidates, "holdout": holdout}


def train_tabular_policy(
    *,
    episodes: int,
    seeds: Iterable[int],
    opponents: Iterable[Callable | str],
) -> dict[str, Any]:
    """Train a high-level route-mode policy from simulated episode margins."""
    policy = TabularPolicy()
    seeds = list(seeds)
    opponents = list(opponents)
    crop_for_mode = {"BALANCED": "WHEAT", "MILK": "STRAWBERRY", "WOOL": "MELON", "EGG": "CARROT", "LIQUIDATE": None}
    completed = 0
    for episode in range(episodes):
        for seed in seeds:
            for opponent in opponents:
                resolved_opponent = _resolve_opponent(opponent)
                mode = policy.choose("opening", epsilon=max(0.05, 1.0 - episode / max(1, episodes)))
                selected_crop = crop_for_mode[mode]

                def make_candidate(crop: str | None) -> Callable[[dict[str, Any]], dict[str, Any]]:
                    def policy_fn(observation: dict[str, Any]) -> dict[str, Any]:
                        if observation.get("step") == 0 and crop:
                            return {"farmer": ["PASS"], "hands": [], "market": [["BUY_SEED", crop, 1]]}
                        return {"farmer": ["PASS"], "hands": [], "market": []}

                    return policy_fn

                candidate = make_candidate(selected_crop)

                env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
                env.run([candidate, resolved_opponent])
                final = env.steps[-1]
                margin = float(final[0].reward or 0) - float(final[1].reward or 0)
                policy.update("opening", mode, margin, "terminal")
                completed += 1
    return {"episodes": completed, "policy": policy.export(), "modes": list(MODES)}


def export_if_better(
    candidate: Callable, baseline: Callable, *, seeds: Iterable[int], output: str | Path,
) -> dict[str, Any]:
    """Write a small policy manifest only when candidate beats the baseline."""
    seeds = list(seeds)
    candidate_report = evaluate_population(candidate, seeds=seeds, opponents=[baseline])
    baseline_report = evaluate_population(baseline, seeds=seeds, opponents=[candidate])
    candidate_mean = sum(row["our_reward"] for row in candidate_report["results"]) / max(1, len(candidate_report["results"]))
    baseline_mean = sum(row["our_reward"] for row in baseline_report["results"]) / max(1, len(baseline_report["results"]))
    exported = candidate_mean > baseline_mean and candidate_report["completed"] == candidate_report["games"]
    report = {"exported": exported, "candidate_mean_reward": candidate_mean, "baseline_mean_reward": baseline_mean,
              "candidate": candidate_report, "baseline": baseline_report}
    if exported:
        Path(output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report
