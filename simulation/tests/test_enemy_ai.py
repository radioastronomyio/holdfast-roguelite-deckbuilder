"""Tests for simulation/engine/enemy_ai.py — greedy enemy AI."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.card import Card
from models.enums import Stat, Operation, Target, Stacking
from engine.turn_order import CombatEntity
from engine.enemy_ai import pick_enemy_action


def make_mod(stat, operation, value, duration=0, target=Target.ENEMY_SINGLE, stacking=Stacking.replace):
    return Modifier(
        stat=stat,
        operation=operation,
        value=value,
        duration=duration,
        target=target,
        stacking=stacking,
    )


def make_card(id, cost, damage, target=Target.ENEMY_SINGLE, duration=0):
    return Card(
        id=id,
        name=id,
        energy_cost=cost,
        effects=[
            make_mod(Stat.HP, Operation.FLAT_SUB, damage, duration=duration, target=target)
        ],
    )


def make_entity(id, hp=50000, speed=100000, energy=3000, is_player=True):
    e = CombatEntity(
        id=id,
        name=id,
        base_stats={
            Stat.HP: hp,
            Stat.Speed: speed,
            Stat.Power: 0,
            Stat.Defense: 0,
            Stat.Energy: energy,
        },
        is_player=is_player,
    )
    e.current_energy = energy
    return e


class TestPickEnemyAction:
    def test_picks_highest_damage_card(self):
        """Enemy picks the card with highest total HP FLAT_SUB value."""
        enemy = make_entity("enemy", is_player=False)
        weak_card = make_card("weak", cost=1, damage=5000)
        strong_card = make_card("strong", cost=1, damage=20000)
        party = [make_entity("hero")]

        result = pick_enemy_action(enemy, [weak_card, strong_card], party)
        assert result is not None
        card, targets = result
        assert card.id == "strong"

    def test_respects_energy_budget(self):
        """Enemy cannot play cards that cost more than current_energy."""
        enemy = make_entity("enemy", energy=2000, is_player=False)
        # Set current_energy below expensive card cost but >= cheap card cost
        enemy.current_energy = 2
        cheap_card = make_card("cheap", cost=1, damage=5000)
        expensive_card = make_card("expensive", cost=3, damage=50000)
        party = [make_entity("hero")]

        result = pick_enemy_action(enemy, [cheap_card, expensive_card], party)
        assert result is not None
        card, _ = result
        assert card.id == "cheap"

    def test_no_affordable_card_returns_none(self):
        """Returns None when no card is within energy budget."""
        enemy = make_entity("enemy", energy=1000, is_player=False)
        enemy.current_energy = 0
        card = make_card("costly", cost=2, damage=10000)
        party = [make_entity("hero")]

        result = pick_enemy_action(enemy, [card], party)
        assert result is None

    def test_no_cards_returns_none(self):
        """Returns None when available_cards is empty."""
        enemy = make_entity("enemy", is_player=False)
        party = [make_entity("hero")]
        result = pick_enemy_action(enemy, [], party)
        assert result is None

    def test_targets_lowest_hp_party_member(self):
        """Enemy targets the party member with the lowest current HP."""
        enemy = make_entity("enemy", is_player=False)
        healthy = make_entity("healthy", hp=100000)
        wounded = make_entity("wounded", hp=20000)
        card = make_card("strike", cost=1, damage=10000)
        party = [healthy, wounded]

        result = pick_enemy_action(enemy, [card], party)
        assert result is not None
        _, targets = result
        assert len(targets) == 1
        assert targets[0].id == "wounded"

    def test_aoe_card_targets_all_party(self):
        """AoE card (ENEMY_ALL effect) returns all living party members as targets."""
        enemy = make_entity("enemy", is_player=False)
        hero1 = make_entity("hero1")
        hero2 = make_entity("hero2")
        hero3 = make_entity("hero3")
        aoe_card = make_card("aoe_blast", cost=1, damage=10000, target=Target.ENEMY_ALL)
        party = [hero1, hero2, hero3]

        result = pick_enemy_action(enemy, [aoe_card], party)
        assert result is not None
        _, targets = result
        assert len(targets) == 3
        assert {t.id for t in targets} == {"hero1", "hero2", "hero3"}

    def test_aoe_ignores_dead_party_members(self):
        """AoE card only targets living party members."""
        enemy = make_entity("enemy", is_player=False)
        alive = make_entity("alive")
        dead = make_entity("dead")
        dead.is_alive = False
        aoe_card = make_card("aoe_blast", cost=1, damage=10000, target=Target.ENEMY_ALL)
        party = [alive, dead]

        result = pick_enemy_action(enemy, [aoe_card], party)
        assert result is not None
        _, targets = result
        assert len(targets) == 1
        assert targets[0].id == "alive"

    def test_all_party_dead_returns_none(self):
        """Returns None when all party members are dead."""
        enemy = make_entity("enemy", is_player=False)
        dead_hero = make_entity("dead_hero")
        dead_hero.is_alive = False
        card = make_card("strike", cost=1, damage=10000)

        result = pick_enemy_action(enemy, [card], [dead_hero])
        assert result is None

    def test_free_card_always_affordable(self):
        """Card with energy_cost=0 is always affordable."""
        enemy = make_entity("enemy", energy=0, is_player=False)
        enemy.current_energy = 0
        free_card = make_card("free_strike", cost=0, damage=5000)
        party = [make_entity("hero")]

        result = pick_enemy_action(enemy, [free_card], party)
        assert result is not None
        card, _ = result
        assert card.id == "free_strike"
