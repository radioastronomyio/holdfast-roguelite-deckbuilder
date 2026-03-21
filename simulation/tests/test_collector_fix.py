"""Tests for upgrade branch collector fix (M3c Task 6.3)."""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from analysis.collectors import _classify_branch, collect_upgrade_stats


ROOT = Path(__file__).resolve().parent.parent.parent


class TestClassifyBranch:
    def test_1a(self):
        assert _classify_branch("1A") == "A"

    def test_1b(self):
        assert _classify_branch("1B") == "B"

    def test_2a_from_1a(self):
        assert _classify_branch("2A_from_1A") == "A"

    def test_2b_from_1b(self):
        assert _classify_branch("2B_from_1B") == "B"

    def test_3a_from_2a(self):
        assert _classify_branch("3A_from_2A") == "A"

    def test_3b_from_2b(self):
        assert _classify_branch("3B_from_2B") == "B"


class TestUpgradeStatsPopulated:
    def test_upgrade_stats_populated(self):
        """After a small Monte Carlo run with upgrade trees loaded, branch picks are non-zero."""
        from campaign.loader import load_game_data
        from agents.monte_carlo import MonteCarloConfig, run_monte_carlo

        game_data = load_game_data(
            data_path=ROOT / "data",
            mods_path=ROOT / "mods" / "default" / "flavor",
        )

        config = MonteCarloConfig(
            seed_count=10,
            strategies=["aggressive", "defensive", "balanced"],
            workers=1,
        )
        mc_result = run_monte_carlo(config, game_data, ROOT / "data", ROOT / "mods" / "default" / "flavor")
        upgrade_stats = collect_upgrade_stats(mc_result)

        # At least one card should have non-zero A or B picks
        total_picks = sum(
            ua.branch_a_picks + ua.branch_b_picks
            for ua in upgrade_stats.values()
        )
        assert total_picks > 0, (
            "No upgrade branch picks found across 10 seeds — upgrade tree data not flowing through"
        )
