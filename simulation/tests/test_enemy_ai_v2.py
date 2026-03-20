"""Tests for enhanced enemy AI v2."""

import pytest

from models.card import Card
from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking, AiHeuristic
from engine.turn_order import CombatEntity
from agents.enemy_ai_v2 import pick_enemy_action_v2


def _make_entity(name: str, hp: int = 100, power: int = 15, energy: int = 5,
                 is_player: bool = False, heuristic: AiHeuristic = AiHeuristic.aggressive) -> CombatEntity:
    return CombatEntity(
        id=name.lower().replace(" ", "_"),
        name=name,
        base_stats={
            Stat.HP: hp * STAT_SCALE,
            Stat.Power: power * STAT_SCALE,
            Stat.Speed: 80 * STAT_SCALE,
            Stat.Defense: 10 * STAT_SCALE,
            Stat.Energy: energy * STAT_SCALE,
        },
        is_player=is_player,
        ai_heuristic=heuristic,
        current_energy=energy * STAT_SCALE,
    )


def _damage_card(card_id: str, value: int, cost: int = 2, aoe: bool = False) -> Card:
    target = Target.ENEMY_ALL if aoe else Target.ENEMY_SINGLE
    return Card(
        id=card_id, name=card_id.replace("_", " ").title(), energy_cost=cost,
        effects=[Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=value * STAT_SCALE,
                          duration=0, target=target, stacking=Stacking.replace)],
    )


def _buff_card(card_id: str, stat: Stat = Stat.Power, cost: int = 1) -> Card:
    return Card(
        id=card_id, name=card_id.replace("_", " ").title(), energy_cost=cost,
        effects=[Modifier(stat=stat, operation=Operation.PCT_ADD, value=30,
                          duration=2, target=Target.SELF, stacking=Stacking.stack)],
    )


def _heal_card(card_id: str, value: int = 10, cost: int = 1) -> Card:
    return Card(
        id=card_id, name=card_id.replace("_", " ").title(), energy_cost=cost,
        effects=[Modifier(stat=Stat.HP, operation=Operation.FLAT_ADD, value=value * STAT_SCALE,
                          duration=0, target=Target.SELF, stacking=Stacking.replace)],
    )


def _debuff_card(card_id: str, cost: int = 1) -> Card:
    return Card(
        id=card_id, name=card_id.replace("_", " ").title(), energy_cost=cost,
        effects=[Modifier(stat=Stat.Defense, operation=Operation.PCT_SUB, value=25,
                          duration=2, target=Target.ENEMY_ALL, stacking=Stacking.stack)],
    )


class TestAggressiveEnemy:
    def test_highest_damage_card(self):
        """Picks highest damage card."""
        enemy = _make_entity("Enemy", heuristic=AiHeuristic.aggressive)
        party = [_make_entity("Player", is_player=True)]
        cards = [_damage_card("weak", 5), _damage_card("strong", 20), _damage_card("mid", 10)]
        result = pick_enemy_action_v2(enemy, cards, party, [], turn_number=5)
        assert result is not None
        assert result[0].id == "strong"

    def test_buff_on_turn_1(self):
        """Plays buff card on turn 1 if available."""
        enemy = _make_entity("Enemy", heuristic=AiHeuristic.aggressive)
        party = [_make_entity("Player", is_player=True)]
        cards = [_damage_card("attack", 15), _buff_card("buff")]
        result = pick_enemy_action_v2(enemy, cards, party, [], turn_number=1)
        assert result is not None
        assert result[0].id == "buff"


class TestDefensiveEnemy:
    def test_heals_when_low(self):
        """Heals when HP < 50%."""
        from models.enums import Stacking as St
        enemy = _make_entity("Enemy", hp=100, heuristic=AiHeuristic.defensive)
        # Add a HP reduction modifier so get_current_stat returns low HP
        # while base_stats stays at 100*STAT_SCALE (for the ratio check)
        enemy.active_modifiers.append(
            Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=60 * STAT_SCALE,
                     duration=-1, target=Target.SELF, stacking=St.stack)
        )
        party = [_make_entity("Player", is_player=True)]
        cards = [_damage_card("attack", 10), _heal_card("heal")]
        result = pick_enemy_action_v2(enemy, cards, party, [], turn_number=3)
        assert result is not None
        assert result[0].id == "heal"

    def test_attacks_when_healthy(self):
        """Attacks when HP > 80%."""
        enemy = _make_entity("Enemy", hp=100, heuristic=AiHeuristic.defensive)
        party = [_make_entity("Player", is_player=True)]
        cards = [_damage_card("attack", 10), _heal_card("heal")]
        result = pick_enemy_action_v2(enemy, cards, party, [], turn_number=3)
        assert result is not None
        assert result[0].id == "attack"


class TestBalancedEnemy:
    def test_debuffs_turn_1(self):
        """Plays debuff card on turn 1 if available."""
        enemy = _make_entity("Enemy", heuristic=AiHeuristic.balanced)
        party = [_make_entity("Player", is_player=True)]
        cards = [_damage_card("attack", 15), _debuff_card("debuff")]
        result = pick_enemy_action_v2(enemy, cards, party, [], turn_number=1)
        assert result is not None
        assert result[0].id == "debuff"

    def test_aoe_multiple_targets(self):
        """Prefers AoE when multiple party members alive."""
        enemy = _make_entity("Enemy", heuristic=AiHeuristic.balanced)
        party = [_make_entity(f"Player{i}", is_player=True) for i in range(3)]
        cards = [_damage_card("single", 15), _damage_card("aoe", 8, aoe=True)]
        result = pick_enemy_action_v2(enemy, cards, party, [], turn_number=3)
        assert result is not None
        assert result[0].id == "aoe"

    def test_focus_fire_carry(self):
        """Targets high-Power low-HP party member."""
        enemy = _make_entity("Enemy", heuristic=AiHeuristic.balanced)
        tank = _make_entity("Tank", hp=200, power=5, is_player=True)
        carry = _make_entity("Carry", hp=40, power=50, is_player=True)
        cards = [_damage_card("attack", 15)]
        result = pick_enemy_action_v2(enemy, cards, [tank, carry], [], turn_number=3)
        assert result is not None
        # Should target the carry (high power, low HP)
        assert result[1][0].id == "carry"


class TestGeneral:
    def test_respects_energy_budget(self):
        """Falls back to affordable card when best is too expensive."""
        enemy = _make_entity("Enemy", energy=2)
        enemy.current_energy = 2  # Low raw energy (energy_cost is compared directly)
        party = [_make_entity("Player", is_player=True)]
        cheap = _damage_card("cheap", 5, cost=1)
        expensive = _damage_card("expensive", 20, cost=10)
        result = pick_enemy_action_v2(enemy, [cheap, expensive], party, [], turn_number=3)
        assert result is not None
        assert result[0].id == "cheap"

    def test_no_card_returns_none(self):
        """Returns None when all cards too expensive."""
        enemy = _make_entity("Enemy", energy=0)
        enemy.current_energy = 0
        party = [_make_entity("Player", is_player=True)]
        cards = [_damage_card("attack", 10, cost=2)]
        result = pick_enemy_action_v2(enemy, cards, party, [], turn_number=3)
        assert result is None

    def test_backward_compatible(self):
        """Same behavior as M2a greedy for aggressive with no buffs, turn > 1."""
        from engine.enemy_ai import pick_enemy_action
        enemy_v1 = _make_entity("Enemy", heuristic=AiHeuristic.aggressive)
        enemy_v2 = _make_entity("Enemy", heuristic=AiHeuristic.aggressive)
        party = [_make_entity("Player", is_player=True)]
        cards = [_damage_card("weak", 5), _damage_card("strong", 20)]
        r1 = pick_enemy_action(enemy_v1, cards, party)
        r2 = pick_enemy_action_v2(enemy_v2, cards, party, [], turn_number=5)
        assert r1 is not None and r2 is not None
        assert r1[0].id == r2[0].id
