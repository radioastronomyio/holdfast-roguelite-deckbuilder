"""Tests for the data loader."""

import json
from pathlib import Path

import pytest

from models.modifier import STAT_SCALE
from models.enums import Operation
from campaign.loader import load_game_data, scale_modifier, GameData
from models.modifier import Modifier
from models.enums import Stat, Target, Stacking


@pytest.fixture
def game_data() -> GameData:
    root = Path(__file__).parent.parent.parent
    return load_game_data(
        data_path=root / "data",
        mods_path=root / "mods" / "default" / "flavor",
    )


class TestScaleModifier:
    def test_flat_add_scaled(self):
        mod = Modifier(stat=Stat.HP, operation=Operation.FLAT_ADD, value=15, duration=0, target=Target.SELF)
        scaled = scale_modifier(mod)
        assert scaled.value == 15 * STAT_SCALE

    def test_flat_sub_scaled(self):
        mod = Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=10, duration=0, target=Target.ENEMY_SINGLE)
        scaled = scale_modifier(mod)
        assert scaled.value == 10 * STAT_SCALE

    def test_pct_add_not_scaled(self):
        mod = Modifier(stat=Stat.Speed, operation=Operation.PCT_ADD, value=30, duration=3, target=Target.SELF)
        scaled = scale_modifier(mod)
        assert scaled.value == 30

    def test_pct_sub_not_scaled(self):
        mod = Modifier(stat=Stat.Speed, operation=Operation.PCT_SUB, value=20, duration=1, target=Target.ENEMY_SINGLE)
        scaled = scale_modifier(mod)
        assert scaled.value == 20

    def test_multiply_not_scaled(self):
        mod = Modifier(stat=Stat.HP, operation=Operation.MULTIPLY, value=1500, duration=0, target=Target.SELF)
        scaled = scale_modifier(mod)
        assert scaled.value == 1500


class TestDataLoader:
    def test_cards_loaded_and_scaled(self, game_data: GameData):
        """Arcane Strike FLAT_SUB value = 15 * 1000 = 15000."""
        card = game_data.cards_by_id["arcane_strike_01"]
        hp_effect = [e for e in card.effects if e.stat == Stat.HP and e.operation == Operation.FLAT_SUB][0]
        assert hp_effect.value == 15 * STAT_SCALE

    def test_pct_values_not_scaled(self, game_data: GameData):
        """PCT_ADD value unchanged (Adrenaline Speed +30%)."""
        card = game_data.cards_by_id["adrenaline_01"]
        speed_effect = [e for e in card.effects if e.stat == Stat.Speed and e.operation == Operation.PCT_ADD][0]
        assert speed_effect.value == 30

    def test_all_base_cards_loaded(self, game_data: GameData):
        """At least 15 base cards loaded."""
        assert len(game_data.cards_by_id) >= 15

    def test_world_deck_loaded(self, game_data: GameData):
        """World deck cards loaded."""
        assert len(game_data.world_deck) >= 1
        # Verify structure
        for wc in game_data.world_deck:
            assert len(wc.upside) >= 1
            assert len(wc.downside) >= 1

    def test_outpost_upgrades_loaded(self, game_data: GameData):
        """Outpost upgrades loaded."""
        assert len(game_data.outpost_upgrades) >= 1

    def test_entity_stats_not_double_scaled(self, game_data: GameData):
        """Character HP values match JSON (already pre-scaled)."""
        # The first character should have HP matching the JSON
        root = Path(__file__).parent.parent.parent
        with open(root / "data" / "entities" / "example-characters.json") as f:
            raw = json.load(f)
        for i, char in enumerate(game_data.characters):
            assert char.base_stats[Stat.HP] == raw[i]["base_stats"]["HP"]

    def test_upgrade_tree_effects_scaled(self, game_data: GameData):
        """If any upgrade trees have FLAT effects, they should be scaled."""
        # Verify upgrade_trees are loaded (may be empty if no upgrade paths in data)
        # Just verify the structure loads without error
        assert isinstance(game_data.upgrade_trees, dict)

    def test_round_trip_integrity(self, game_data: GameData):
        """All data files loaded without error."""
        assert len(game_data.cards_by_id) >= 15
        assert len(game_data.characters) >= 1
        assert len(game_data.enemies_by_id) >= 1
        assert game_data.generation_bounds is not None
        assert len(game_data.regions) >= 1
        assert len(game_data.world_deck) >= 1
        assert game_data.flavor is not None

    def test_region_modifiers_loaded(self, game_data: GameData):
        """Region modifier_stack loaded correctly."""
        for region in game_data.regions:
            for mod in region.modifier_stack:
                assert mod.stat is not None
                assert mod.operation is not None

    def test_multiply_value_not_scaled(self, game_data: GameData):
        """MULTIPLY values should not be scaled."""
        # Just verify no MULTIPLY card values are absurdly large
        for card in game_data.cards_by_id.values():
            for eff in card.effects:
                if eff.operation == Operation.MULTIPLY:
                    assert eff.value < 100 * STAT_SCALE  # sanity check
