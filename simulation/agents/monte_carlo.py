"""Monte Carlo runner — runs campaigns at scale and outputs balance metrics."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List

from campaign.loader import GameData, load_game_data
from campaign.runner import run_campaign, CampaignResult
from agents.heuristics import AggressiveAI, DefensiveAI, BalancedAI


@dataclass
class MonteCarloConfig:
    seed_start: int = 1
    seed_count: int = 1000
    strategies: list[str] = field(default_factory=lambda: ["aggressive", "defensive", "balanced"])
    workers: int = 1


@dataclass
class StrategyMetrics:
    strategy_name: str
    total_runs: int
    wins: int
    losses: int
    win_rate: float
    avg_regions_cleared: float
    avg_total_turns: float
    world_cards_accepted_rate: float
    world_cards_skipped_rate: float
    avg_resources_spent: float


@dataclass
class MonteCarloResult:
    config: MonteCarloConfig
    strategy_results: list[StrategyMetrics]
    per_seed_results: dict[int, dict[str, CampaignResult]]
    win_rate_spread: float
    convergence_warning: bool


def _get_strategy(name: str):
    """Get a strategy instance by name."""
    if name == "aggressive":
        return AggressiveAI()
    elif name == "defensive":
        return DefensiveAI()
    elif name == "balanced":
        return BalancedAI()
    raise ValueError(f"Unknown strategy: {name}")


def _run_single(seed: int, strategy_name: str, data_path: Path, mods_path: Path) -> CampaignResult:
    """Run a single campaign (for multiprocessing compatibility)."""
    game_data = load_game_data(data_path, mods_path)
    strategy = _get_strategy(strategy_name)
    return run_campaign(seed, game_data, strategy)


def run_monte_carlo(
    config: MonteCarloConfig,
    game_data: GameData,
    data_path: Path = Path("data"),
    mods_path: Path = Path("mods/default/flavor"),
) -> MonteCarloResult:
    """Execute Monte Carlo simulation."""
    per_seed_results: dict[int, dict[str, CampaignResult]] = {}

    # Collect results per strategy
    strategy_campaign_results: dict[str, list[CampaignResult]] = {
        s: [] for s in config.strategies
    }

    seeds = list(range(config.seed_start, config.seed_start + config.seed_count))

    if config.workers <= 1:
        # Single-threaded
        for seed in seeds:
            per_seed_results[seed] = {}
            for strategy_name in config.strategies:
                # Load fresh game_data per run to avoid mutation issues
                gd = load_game_data(data_path, mods_path)
                strategy = _get_strategy(strategy_name)
                result = run_campaign(seed, gd, strategy)
                per_seed_results[seed][strategy_name] = result
                strategy_campaign_results[strategy_name].append(result)
    else:
        # Parallel via multiprocessing
        from multiprocessing import Pool
        tasks = [
            (seed, strategy_name, data_path, mods_path)
            for seed in seeds
            for strategy_name in config.strategies
        ]
        with Pool(config.workers) as pool:
            results = pool.starmap(_run_single, tasks)

        idx = 0
        for seed in seeds:
            per_seed_results[seed] = {}
            for strategy_name in config.strategies:
                result = results[idx]
                per_seed_results[seed][strategy_name] = result
                strategy_campaign_results[strategy_name].append(result)
                idx += 1

    # Aggregate metrics per strategy
    strategy_metrics: list[StrategyMetrics] = []
    for strategy_name in config.strategies:
        runs = strategy_campaign_results[strategy_name]
        total = len(runs)
        wins = sum(1 for r in runs if r.victory)
        losses = total - wins
        win_rate = wins / total if total > 0 else 0.0
        avg_cleared = sum(r.regions_cleared for r in runs) / total if total > 0 else 0.0
        avg_turns = sum(r.total_turns for r in runs) / total if total > 0 else 0.0
        total_drawn = sum(r.world_cards_drawn for r in runs)
        total_skipped = sum(r.world_cards_skipped for r in runs)
        accepted_rate = (total_drawn - total_skipped) / total_drawn if total_drawn > 0 else 0.0
        skipped_rate = total_skipped / total_drawn if total_drawn > 0 else 0.0
        avg_resources = sum(r.resources_spent_on_research for r in runs) / total if total > 0 else 0.0

        strategy_metrics.append(StrategyMetrics(
            strategy_name=strategy_name,
            total_runs=total,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            avg_regions_cleared=avg_cleared,
            avg_total_turns=avg_turns,
            world_cards_accepted_rate=accepted_rate,
            world_cards_skipped_rate=skipped_rate,
            avg_resources_spent=avg_resources,
        ))

    # Balance signals
    win_rates = [m.win_rate for m in strategy_metrics]
    win_rate_spread = max(win_rates) - min(win_rates) if win_rates else 0.0

    # Convergence check: do all strategies select same first region >80%?
    convergence_count = 0
    for seed in seeds:
        first_regions = set()
        for strategy_name in config.strategies:
            result = per_seed_results[seed][strategy_name]
            # Check first assault log
            assault_logs = [l for l in result.campaign_log if "Assaulting" in l]
            if assault_logs:
                first_regions.add(assault_logs[0])
        if len(first_regions) <= 1:
            convergence_count += 1
    convergence_rate = convergence_count / len(seeds) if seeds else 0.0
    convergence_warning = convergence_rate > 0.8

    return MonteCarloResult(
        config=config,
        strategy_results=strategy_metrics,
        per_seed_results=per_seed_results,
        win_rate_spread=win_rate_spread,
        convergence_warning=convergence_warning,
    )


def monte_carlo_to_json(result: MonteCarloResult, output_path: Path) -> None:
    """Serialize results to JSON for analysis."""
    data = {
        "config": {
            "seed_start": result.config.seed_start,
            "seed_count": result.config.seed_count,
            "strategies": result.config.strategies,
            "workers": result.config.workers,
        },
        "strategy_results": [
            {
                "strategy_name": m.strategy_name,
                "total_runs": m.total_runs,
                "wins": m.wins,
                "losses": m.losses,
                "win_rate": m.win_rate,
                "avg_regions_cleared": m.avg_regions_cleared,
                "avg_total_turns": m.avg_total_turns,
                "world_cards_accepted_rate": m.world_cards_accepted_rate,
                "world_cards_skipped_rate": m.world_cards_skipped_rate,
                "avg_resources_spent": m.avg_resources_spent,
            }
            for m in result.strategy_results
        ],
        "win_rate_spread": result.win_rate_spread,
        "convergence_warning": result.convergence_warning,
        "per_seed_summary": {
            str(seed): {
                strategy_name: {
                    "victory": r.victory,
                    "regions_cleared": r.regions_cleared,
                    "total_turns": r.total_turns,
                }
                for strategy_name, r in strats.items()
            }
            for seed, strats in result.per_seed_results.items()
        },
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
