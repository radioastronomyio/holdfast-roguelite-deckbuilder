"""Tests for analysis collectors (M3a Task 4.3)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from agents.monte_carlo import MonteCarloConfig, run_monte_carlo
from campaign.loader import load_game_data
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
    CardAnalysis,
    UpgradeAnalysis,
    RegionAnalysis,
    WorldCardAnalysis,
    SpeedAnalysis,
    DifficultyCurve,
    SeedClassification,
    CombatDurationAnalysis,
    ConvergenceAnalysis,
)


def _run_small_mc(seed_count=10):
    """Run a small Monte Carlo for collector testing."""
    gd = load_game_data(Path("data"), Path("mods/default/flavor"))
    config = MonteCarloConfig(seed_start=1, seed_count=seed_count, strategies=["aggressive", "defensive", "balanced"])
    return run_monte_carlo(config, gd)


class TestCollectorsReturnPopulated:
    """Each collector should return a non-default result against a small MC run."""

    def setup_method(self):
        self.mc_result = _run_small_mc(10)

    def test_collect_card_stats_returns_dict(self):
        result = collect_card_stats(self.mc_result)
        assert isinstance(result, dict)
        assert len(result) > 0, "collect_card_stats should return at least one card"

    def test_collect_card_stats_values_are_cardanalysis(self):
        result = collect_card_stats(self.mc_result)
        for v in result.values():
            assert isinstance(v, CardAnalysis)

    def test_collect_upgrade_stats_returns_dict(self):
        result = collect_upgrade_stats(self.mc_result)
        assert isinstance(result, dict)
        # May be empty if no upgrade trees, that's fine

    def test_collect_region_stats_returns_dict(self):
        result = collect_region_stats(self.mc_result)
        assert isinstance(result, dict)
        assert len(result) > 0, "collect_region_stats should return at least one region"

    def test_collect_region_stats_values_are_regionanalysis(self):
        result = collect_region_stats(self.mc_result)
        for v in result.values():
            assert isinstance(v, RegionAnalysis)

    def test_collect_world_card_stats_returns_dict(self):
        result = collect_world_card_stats(self.mc_result)
        assert isinstance(result, dict)

    def test_collect_speed_stats_returns_speedanalysis(self):
        result = collect_speed_stats(self.mc_result)
        assert isinstance(result, SpeedAnalysis)

    def test_collect_speed_stats_max_ratio_positive(self):
        result = collect_speed_stats(self.mc_result)
        assert result.max_ratio >= 0.0

    def test_collect_difficulty_curve_returns_correct_type(self):
        result = collect_difficulty_curve(self.mc_result)
        assert isinstance(result, DifficultyCurve)

    def test_collect_difficulty_curve_has_strategies(self):
        result = collect_difficulty_curve(self.mc_result)
        for sname in self.mc_result.config.strategies:
            assert sname in result.conditional_win_prob

    def test_collect_seed_classification_returns_correct_type(self):
        result = collect_seed_classification(self.mc_result)
        assert isinstance(result, SeedClassification)

    def test_collect_seed_classification_all_win_seeds_correct(self):
        """Seeds where all 3 strategies win should be in all_win bucket."""
        sc = collect_seed_classification(self.mc_result)
        for seed in sc.all_win_seeds:
            strats = self.mc_result.per_seed_results[seed]
            assert all(cr.victory for cr in strats.values()), \
                f"Seed {seed} in all_win_seeds but not all strategies won"

    def test_collect_seed_classification_all_loss_seeds_correct(self):
        sc = collect_seed_classification(self.mc_result)
        for seed in sc.all_loss_seeds:
            strats = self.mc_result.per_seed_results[seed]
            assert not any(cr.victory for cr in strats.values()), \
                f"Seed {seed} in all_loss_seeds but some strategy won"

    def test_collect_seed_classification_totals(self):
        sc = collect_seed_classification(self.mc_result)
        total = len(sc.all_win_seeds) + len(sc.all_loss_seeds) + len(sc.strategy_dependent_seeds)
        assert total == sc.total_seeds

    def test_collect_combat_duration_returns_correct_type(self):
        result = collect_combat_duration(self.mc_result)
        assert isinstance(result, CombatDurationAnalysis)

    def test_collect_combat_duration_mean_positive(self):
        result = collect_combat_duration(self.mc_result)
        assert result.mean_duration > 0.0

    def test_collect_convergence_returns_correct_type(self):
        result = collect_convergence_deep(self.mc_result)
        assert isinstance(result, ConvergenceAnalysis)

    def test_collect_convergence_pairwise_matrix_complete(self):
        result = collect_convergence_deep(self.mc_result)
        strategies = self.mc_result.config.strategies
        for s1 in strategies:
            for s2 in strategies:
                assert s2 in result.strategy_correlation.get(s1, {}), \
                    f"Missing pairwise correlation {s1}↔{s2}"

    def test_collect_convergence_self_agreement_is_one(self):
        result = collect_convergence_deep(self.mc_result)
        for s in self.mc_result.config.strategies:
            assert result.strategy_correlation[s][s] == 1.0
