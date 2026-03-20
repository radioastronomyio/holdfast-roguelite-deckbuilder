"""Tests for campaign-level telemetry instrumentation (M3a Task 4.2)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from campaign.loader import load_game_data
from campaign.runner import run_campaign
from agents.heuristics import AggressiveAI, BalancedAI
from pathlib import Path


def _load():
    return load_game_data(Path("data"), Path("mods/default/flavor"))


class TestCampaignTelemetryPopulated:
    """Verify campaign-level telemetry fields populate correctly."""

    def test_region_order_nonempty(self):
        gd = _load()
        result = run_campaign(1, gd, AggressiveAI())
        assert len(result.region_order) > 0, "region_order should contain at least one entry"

    def test_region_difficulties_populated(self):
        gd = _load()
        result = run_campaign(1, gd, AggressiveAI())
        assert len(result.region_difficulties) == 6, "Should have difficulty for all 6 regions"

    def test_starting_roster_ids_populated(self):
        gd = _load()
        result = run_campaign(1, gd, AggressiveAI())
        assert len(result.starting_roster_ids) == 2, "Should start with 2 characters"

    def test_card_pool_ids_nonempty(self):
        gd = _load()
        result = run_campaign(1, gd, AggressiveAI())
        assert len(result.card_pool_ids) > 0, "card_pool_ids should be populated"

    def test_world_cards_accepted_plus_skipped_equals_drawn(self):
        gd = _load()
        result = run_campaign(1, gd, BalancedAI())
        # accepted (including forced accepts) + voluntarily skipped = total drawn
        total = len(result.world_cards_accepted_ids) + len(result.world_cards_skipped_ids)
        assert total == result.world_cards_drawn, (
            f"accepted({len(result.world_cards_accepted_ids)}) + "
            f"skipped({len(result.world_cards_skipped_ids)}) = {total} "
            f"!= drawn({result.world_cards_drawn})"
        )

    def test_drafted_character_ids_match_regions_cleared(self):
        """One character is drafted per region conquered."""
        gd = _load()
        result = run_campaign(42, gd, AggressiveAI())
        # drafted characters count == regions cleared (one draft per conquest)
        assert len(result.drafted_character_ids) == result.regions_cleared

    def test_upgrade_branches_chosen_is_dict(self):
        """upgrade_branches_chosen should always be a dict (may be empty if no upgrade trees in data)."""
        gd = _load()
        result = run_campaign(1, gd, BalancedAI())
        assert isinstance(result.upgrade_branches_chosen, dict)
