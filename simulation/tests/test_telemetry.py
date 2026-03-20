"""Tests for combat telemetry instrumentation (M3a Task 4.1)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.card import Card
from models.enums import Stat, Operation, Target, Stacking
from engine.turn_order import CombatEntity
from engine.encounters import (
    COMBAT_TURN_CAP,
    resolve_combat,
    CardPlayRecord,
)


def make_mod(stat, operation, value, duration=0, target=Target.ENEMY_SINGLE, stacking=Stacking.replace):
    return Modifier(stat=stat, operation=operation, value=value, duration=duration,
                    target=target, stacking=stacking, tags=[])


def make_card(id, cost, damage, target=Target.ENEMY_SINGLE, duration=0):
    return Card(
        id=id, name=id, energy_cost=cost,
        effects=[make_mod(Stat.HP, Operation.FLAT_SUB, damage, duration=duration, target=target)],
    )


def make_entity(id, hp=50000, speed=100000, power=0, defense=0, energy=3000,
                is_player=True, card_pool=None):
    return CombatEntity(
        id=id, name=id,
        base_stats={
            Stat.HP: hp * STAT_SCALE,
            Stat.Speed: speed,
            Stat.Power: power * STAT_SCALE,
            Stat.Defense: defense * STAT_SCALE,
            Stat.Energy: energy,
        },
        is_player=is_player,
        card_pool=card_pool or [],
        active_modifiers=[],
    )


class TestCombatTelemetryPopulated:
    """Verify instrumented combat produces populated telemetry."""

    def _run_simple_combat(self):
        """Run a short, deterministic combat: 1 player vs 1 enemy, player wins quickly."""
        card = make_card("strike", cost=1, damage=100)  # 100 * STAT_SCALE flat, no power bonus
        player = make_entity("player1", hp=100, speed=200, power=0, defense=0, energy=5, is_player=True, card_pool=["strike"])
        enemy = make_entity("enemy1", hp=10, speed=50, power=0, defense=0, energy=5, is_player=False, card_pool=["strike"])
        cards_by_id = {"strike": card}
        result = resolve_combat([player], [enemy], cards_by_id=cards_by_id)
        return result

    def test_card_plays_nonempty(self):
        result = self._run_simple_combat()
        assert len(result.card_plays) > 0, "card_plays should be populated after combat"

    def test_card_plays_are_records(self):
        result = self._run_simple_combat()
        for cp in result.card_plays:
            assert isinstance(cp, CardPlayRecord)

    def test_entity_turns_populated(self):
        result = self._run_simple_combat()
        assert len(result.entity_turns) > 0
        # Sum of entity turns >= turns_taken (each turn maps to one actor's increment)
        total = sum(result.entity_turns.values())
        assert total == result.turns_taken

    def test_entity_turns_sum_matches_turns_taken(self):
        result = self._run_simple_combat()
        total = sum(result.entity_turns.values())
        assert total == result.turns_taken

    def test_damage_dealt_at_display_scale(self):
        """Values in damage_dealt should be at display scale (not STAT_SCALE multiples)."""
        card = make_card("heavy", cost=1, damage=15)  # 15 display scale = 15000 internal
        player = make_entity("p", hp=100, speed=300, power=0, defense=0, energy=5, is_player=True, card_pool=["heavy"])
        enemy = make_entity("e", hp=20, speed=50, power=0, defense=0, energy=1, is_player=False, card_pool=[])
        result = resolve_combat([player], [enemy], cards_by_id={"heavy": card})
        # damage_dealt values should be small integers (display scale), not 15000+
        for eid, dmg in result.damage_dealt.items():
            assert dmg < 10000, f"damage_dealt[{eid}]={dmg} looks like it's in internal scale"

    def test_hit_turn_cap_false_in_normal_combat(self):
        result = self._run_simple_combat()
        assert result.hit_turn_cap is False

    def test_hit_turn_cap_true_when_cap_reached(self):
        """Two immortal entities — neither can die, should hit cap."""
        card = make_card("scratch", cost=1, damage=0)
        player = make_entity("p", hp=999999, speed=100, power=0, defense=999, energy=5, is_player=True, card_pool=["scratch"])
        enemy = make_entity("e", hp=999999, speed=100, power=0, defense=999, energy=5, is_player=False, card_pool=["scratch"])
        result = resolve_combat([player], [enemy], cards_by_id={"scratch": card})
        assert result.hit_turn_cap is True

    def test_speed_action_ratios_computed(self):
        result = self._run_simple_combat()
        assert len(result.speed_action_ratios) > 0

    def test_speed_action_ratios_positive(self):
        result = self._run_simple_combat()
        for eid, ratio in result.speed_action_ratios.items():
            assert ratio >= 0.0, f"speed_action_ratios[{eid}] is negative: {ratio}"

    def test_final_hp_populated(self):
        result = self._run_simple_combat()
        assert len(result.final_hp) > 0

    def test_damage_taken_populated(self):
        """Use STAT_SCALE-level damage so display-scale conversion yields > 0."""
        card = make_card("big_hit", cost=1, damage=STAT_SCALE * 20)  # 20 display units of damage
        player = make_entity("p", hp=100, speed=300, power=0, defense=0, energy=5, is_player=True, card_pool=["big_hit"])
        enemy = make_entity("e", hp=5, speed=50, power=0, defense=0, energy=1, is_player=False, card_pool=[])
        result = resolve_combat([player], [enemy], cards_by_id={"big_hit": card})
        total_taken = sum(result.damage_taken.values())
        assert total_taken > 0
