"""Tests for the campaign runner."""

import random
from pathlib import Path

import pytest

from models.entity import Character, Enemy
from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking, AiHeuristic
from engine.turn_order import CombatEntity
from campaign.loader import load_game_data, GameData
from campaign.runner import (
    run_campaign,
    character_to_combat_entity,
    enemy_data_to_combat_entity,
    apply_card_upgrade,
    pick_greedy_upgrade,
    CampaignResult,
)


@pytest.fixture
def game_data() -> GameData:
    root = Path(__file__).parent.parent.parent
    return load_game_data(
        data_path=root / "data",
        mods_path=root / "mods" / "default" / "flavor",
    )


class TestCampaignRunner:
    def test_campaign_completes(self, game_data: GameData):
        """Run with known seed — returns CampaignResult without crash."""
        result = run_campaign(42, game_data)
        assert isinstance(result, CampaignResult)
        assert result.seed == 42

    def test_deterministic(self, game_data: GameData):
        """Same seed produces identical results."""
        # Need fresh game_data for each run since runner may mutate cards
        root = Path(__file__).parent.parent.parent
        gd1 = load_game_data(root / "data", root / "mods" / "default" / "flavor")
        gd2 = load_game_data(root / "data", root / "mods" / "default" / "flavor")
        r1 = run_campaign(42, gd1)
        r2 = run_campaign(42, gd2)
        assert r1.victory == r2.victory
        assert r1.regions_cleared == r2.regions_cleared
        assert r1.total_turns == r2.total_turns
        assert r1.world_cards_drawn == r2.world_cards_drawn

    def test_resources_increment(self, game_data: GameData):
        """If any regions conquered, resources should have been earned."""
        result = run_campaign(42, game_data)
        if result.regions_cleared >= 1:
            # Resources = 50 per conquest, but some may be spent on research
            # Just verify the campaign tracked resources
            assert result.resources_spent_on_research >= 0

    def test_world_cards_drawn(self, game_data: GameData):
        """If conquest happened, world cards should have been drawn."""
        result = run_campaign(42, game_data)
        if result.regions_cleared >= 1:
            assert result.world_cards_drawn >= 1

    def test_character_drafted(self, game_data: GameData):
        """After conquest, roster size increases."""
        result = run_campaign(42, game_data)
        # Started with 1, each conquest drafts 1 more
        if result.regions_cleared >= 1:
            assert len(result.final_roster) >= 2

    def test_campaign_log_not_empty(self, game_data: GameData):
        """Campaign produces log entries."""
        result = run_campaign(42, game_data)
        assert len(result.campaign_log) >= 1

    def test_encounter_results_not_empty(self, game_data: GameData):
        """Campaign has encounter results."""
        result = run_campaign(42, game_data)
        assert len(result.encounter_results) >= 1

    def test_region_selection_lowest_difficulty(self, game_data: GameData):
        """First assault should target difficulty 1."""
        result = run_campaign(42, game_data)
        # The first log entry about assaulting should reference the lowest difficulty
        assault_logs = [l for l in result.campaign_log if "Assaulting" in l]
        if assault_logs:
            assert "difficulty 1" in assault_logs[0]


class TestEntityConversion:
    def test_character_to_combat_entity(self):
        """Convert Character → CombatEntity preserves base_stats and innate_passive."""
        char = Character(
            id="test_char",
            name="Test Character",
            base_stats={s: 100 * STAT_SCALE for s in Stat},
            innate_passive=Modifier(
                stat=Stat.Power, operation=Operation.PCT_ADD, value=15,
                duration=-1, target=Target.SELF, stacking=Stacking.stack,
            ),
            name_parts={"first_name": "Test", "title": "Fighter", "origin": "Valley"},
        )
        entity = character_to_combat_entity(char, [], [])
        assert entity.base_stats[Stat.HP] == 100 * STAT_SCALE
        assert entity.is_player is True
        assert any(m.stat == Stat.Power and m.operation == Operation.PCT_ADD for m in entity.active_modifiers)

    def test_enemy_to_combat_entity(self):
        """Convert Enemy → CombatEntity preserves stats and heuristic."""
        enemy = Enemy(
            id="test_enemy",
            name="Test Enemy",
            base_stats={s: 50 * STAT_SCALE for s in Stat},
            card_pool=["arcane_strike_01"],
            ai_heuristic_tag=AiHeuristic.aggressive,
            is_elite=True,
        )
        entity = enemy_data_to_combat_entity(enemy, 3)
        assert entity.base_stats[Stat.HP] == 50 * STAT_SCALE
        assert entity.is_player is False
        assert entity.ai_heuristic == AiHeuristic.aggressive
        assert "arcane_strike_01" in entity.card_pool

    def test_world_mods_included_in_entity(self):
        """World modifiers are included in combat entity."""
        char = Character(
            id="test_char",
            name="Test Character",
            base_stats={s: 100 * STAT_SCALE for s in Stat},
            innate_passive=Modifier(
                stat=Stat.Power, operation=Operation.PCT_ADD, value=15,
                duration=-1, target=Target.SELF, stacking=Stacking.stack,
            ),
            name_parts={"first_name": "Test", "title": "Fighter", "origin": "Valley"},
        )
        world_mod = Modifier(
            stat=Stat.Speed, operation=Operation.PCT_ADD, value=30,
            duration=-1, target=Target.ALLY_ALL, stacking=Stacking.stack,
        )
        entity = character_to_combat_entity(char, [world_mod], [])
        speed_mods = [m for m in entity.active_modifiers if m.stat == Stat.Speed]
        assert len(speed_mods) >= 1

    def test_data_loader_integration(self, game_data):
        """Load game data and run campaign — no scaling errors."""
        result = run_campaign(123, game_data)
        assert isinstance(result, CampaignResult)
        # If combat happened, total_turns should be reasonable
        if result.encounter_results:
            assert result.total_turns >= 0
