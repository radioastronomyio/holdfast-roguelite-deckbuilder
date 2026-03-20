"""Exports analysis data as JSON for archival and exploration."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from agents.monte_carlo import MonteCarloResult
from analysis.collectors import (
    collect_card_stats,
    collect_upgrade_stats,
    collect_region_stats,
    collect_world_card_stats,
    collect_speed_stats,
    collect_difficulty_curve,
    collect_seed_classification,
    collect_combat_duration,
    collect_convergence_deep,
)


def _write_json(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def _to_serializable(obj):
    """Recursively convert dataclasses and non-JSON-native types to dicts/lists."""
    if isinstance(obj, dict):
        return {str(k): _to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_serializable(v) for v in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_serializable(v) for k, v in asdict(obj).items()}
    return obj


def export_analysis_data(result: MonteCarloResult, output_dir: Path) -> None:
    """Write all 9 JSON files to reports/m3-analysis/data/."""
    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    card_stats = collect_card_stats(result)
    _write_json(
        {cid: _to_serializable(cs) for cid, cs in card_stats.items()},
        data_dir / "card_stats.json",
    )

    upgrade_stats = collect_upgrade_stats(result)
    _write_json(
        {cid: _to_serializable(ua) for cid, ua in upgrade_stats.items()},
        data_dir / "upgrade_stats.json",
    )

    region_stats = collect_region_stats(result)
    _write_json(
        {str(idx): _to_serializable(ra) for idx, ra in region_stats.items()},
        data_dir / "region_stats.json",
    )

    world_card_stats = collect_world_card_stats(result)
    _write_json(
        {cid: _to_serializable(wca) for cid, wca in world_card_stats.items()},
        data_dir / "world_card_stats.json",
    )

    speed_stats = collect_speed_stats(result)
    # Don't serialize all raw ratios (could be huge) — just summary stats
    _write_json(
        {
            "mean_ratio": speed_stats.mean_ratio,
            "max_ratio": speed_stats.max_ratio,
            "pct_above_3x": speed_stats.pct_above_3x,
            "pct_above_5x": speed_stats.pct_above_5x,
            "flagged_count": speed_stats.flagged_count,
            "sample_ratios": speed_stats.ratios[:100],  # first 100 only
        },
        data_dir / "speed_stats.json",
    )

    difficulty_curve = collect_difficulty_curve(result)
    _write_json(_to_serializable(difficulty_curve), data_dir / "difficulty_curve.json")

    seed_class = collect_seed_classification(result)
    # Don't dump full seed lists in the JSON (too verbose) — just summary + samples
    _write_json(
        {
            "total_seeds": seed_class.total_seeds,
            "all_win_rate": seed_class.all_win_rate,
            "all_loss_rate": seed_class.all_loss_rate,
            "strategy_dependent_rate": seed_class.strategy_dependent_rate,
            "all_win_count": len(seed_class.all_win_seeds),
            "all_loss_count": len(seed_class.all_loss_seeds),
            "strategy_dependent_count": len(seed_class.strategy_dependent_seeds),
            "sample_all_win_seeds": seed_class.all_win_seeds[:20],
            "sample_all_loss_seeds": seed_class.all_loss_seeds[:20],
            "sample_strategy_dependent_seeds": seed_class.strategy_dependent_seeds[:20],
        },
        data_dir / "seed_classification.json",
    )

    combat_duration = collect_combat_duration(result)
    _write_json(
        {
            "mean_duration": combat_duration.mean_duration,
            "median_duration": combat_duration.median_duration,
            "p95_duration": combat_duration.p95_duration,
            "turn_cap_rate": combat_duration.turn_cap_rate,
            "turn_cap_rate_by_region": {
                str(k): v for k, v in combat_duration.turn_cap_rate_by_region.items()
            },
            "sample_durations": combat_duration.all_durations[:200],
        },
        data_dir / "combat_duration.json",
    )

    convergence = collect_convergence_deep(result)
    _write_json(
        {
            "first_region_agreement": convergence.first_region_agreement,
            "full_order_agreement": convergence.full_order_agreement,
            "strategy_correlation": convergence.strategy_correlation,
        },
        data_dir / "convergence.json",
    )
