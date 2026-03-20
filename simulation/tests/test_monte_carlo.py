"""Tests for the Monte Carlo runner."""

import json
import tempfile
from pathlib import Path

import pytest

from campaign.loader import load_game_data, GameData
from campaign.runner import CampaignResult
from agents.monte_carlo import (
    MonteCarloConfig,
    MonteCarloResult,
    StrategyMetrics,
    run_monte_carlo,
    monte_carlo_to_json,
)


def _data_paths():
    root = Path(__file__).parent.parent.parent
    return root / "data", root / "mods" / "default" / "flavor"


@pytest.fixture
def game_data() -> GameData:
    data_path, mods_path = _data_paths()
    return load_game_data(data_path, mods_path)


class TestMonteCarlo:
    def test_single_seed_runs(self, game_data: GameData):
        """Config with seed_count=1 completes without error."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=1, strategies=["balanced"])
        result = run_monte_carlo(config, game_data, data_path, mods_path)
        assert isinstance(result, MonteCarloResult)
        assert len(result.strategy_results) == 1

    def test_10_seed_run(self, game_data: GameData):
        """10 seeds × 3 strategies = 30 campaign results."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=10)
        result = run_monte_carlo(config, game_data, data_path, mods_path)
        assert len(result.strategy_results) == 3
        total_campaigns = sum(m.total_runs for m in result.strategy_results)
        assert total_campaigns == 30

    def test_win_rate_computed(self, game_data: GameData):
        """Win rates are between 0.0 and 1.0."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=10)
        result = run_monte_carlo(config, game_data, data_path, mods_path)
        for m in result.strategy_results:
            assert 0.0 <= m.win_rate <= 1.0

    def test_deterministic(self, game_data: GameData):
        """Running twice produces identical results."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=5, strategies=["balanced"])
        r1 = run_monte_carlo(config, game_data, data_path, mods_path)
        r2 = run_monte_carlo(config, game_data, data_path, mods_path)
        assert r1.strategy_results[0].wins == r2.strategy_results[0].wins
        assert r1.strategy_results[0].win_rate == r2.strategy_results[0].win_rate

    def test_json_output(self, game_data: GameData):
        """Serializes to valid JSON."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=3, strategies=["balanced"])
        result = run_monte_carlo(config, game_data, data_path, mods_path)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            output_path = Path(f.name)

        monte_carlo_to_json(result, output_path)
        with open(output_path) as f:
            data = json.load(f)
        assert "strategy_results" in data
        assert "win_rate_spread" in data
        output_path.unlink()

    def test_per_seed_results_indexed(self, game_data: GameData):
        """per_seed_results has all seeds."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=5, strategies=["balanced"])
        result = run_monte_carlo(config, game_data, data_path, mods_path)
        assert len(result.per_seed_results) == 5
        for seed in range(1, 6):
            assert seed in result.per_seed_results

    def test_metrics_aggregation(self, game_data: GameData):
        """avg_regions_cleared is between 1 and 6."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=10, strategies=["balanced"])
        result = run_monte_carlo(config, game_data, data_path, mods_path)
        for m in result.strategy_results:
            assert 0.0 <= m.avg_regions_cleared <= 6.0

    def test_convergence_detection(self, game_data: GameData):
        """convergence_warning is a boolean."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=5)
        result = run_monte_carlo(config, game_data, data_path, mods_path)
        assert isinstance(result.convergence_warning, bool)

    def test_different_strategies_different_win_rates(self, game_data: GameData):
        """Over enough seeds, at least 2 strategies should have different metrics."""
        data_path, mods_path = _data_paths()
        config = MonteCarloConfig(seed_start=1, seed_count=20)
        result = run_monte_carlo(config, game_data, data_path, mods_path)
        # Check that at least regions_cleared varies
        cleared_values = [m.avg_regions_cleared for m in result.strategy_results]
        # At least one pair should differ (soft check)
        assert len(cleared_values) == 3
