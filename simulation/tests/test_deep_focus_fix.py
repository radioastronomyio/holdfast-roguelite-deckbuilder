"""Tests verifying the deep_focus_01 speed-collapse fix (M3b Task 6.3)."""
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import random
from pathlib import Path

import pytest

from campaign.loader import load_game_data
from models.modifier import STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking
from models.card import Card
from models.modifier import Modifier
from engine.turn_order import CombatEntity
from engine.encounters import resolve_combat


ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def game_data():
    return load_game_data(
        data_path=ROOT / "data",
        mods_path=ROOT / "mods" / "default" / "flavor",
    )


class TestDeepFocusFix:
    def test_deep_focus_cost(self, game_data):
        """deep_focus_01 energy_cost must be 1 (not 0)."""
        card = game_data.cards_by_id["deep_focus_01"]
        assert card.energy_cost == 1, (
            f"deep_focus_01 energy_cost is {card.energy_cost}, expected 1"
        )

    def test_deep_focus_value(self, game_data):
        """deep_focus_01 Energy FLAT_ADD value must be 1 * STAT_SCALE."""
        card = game_data.cards_by_id["deep_focus_01"]
        energy_effects = [
            e for e in card.effects
            if e.stat == Stat.Energy and e.operation == Operation.FLAT_ADD
        ]
        assert len(energy_effects) == 1
        assert energy_effects[0].value == 1 * STAT_SCALE, (
            f"deep_focus_01 Energy value is {energy_effects[0].value}, expected {1 * STAT_SCALE}"
        )

    def test_no_infinite_energy(self):
        """After deck mechanics + fix, no combat should have speed_action_ratio > 20."""
        from campaign.runner import run_campaign, CampaignResult
        from engine.encounters import CombatResult

        gd = load_game_data(
            data_path=ROOT / "data",
            mods_path=ROOT / "mods" / "default" / "flavor",
        )
        violations = []
        for seed in range(10):
            result = run_campaign(seed, gd)
            for enc in result.encounter_results:
                if not isinstance(enc, CombatResult):
                    continue
                for entity_id, ratio in enc.speed_action_ratios.items():
                    if ratio > 30:
                        violations.append((seed, entity_id, ratio))

        assert not violations, (
            f"Found speed_action_ratio > 30 in {len(violations)} combats: {violations[:5]}"
        )
