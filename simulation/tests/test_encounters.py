"""Tests for simulation/engine/encounters.py — combat, hazard, event resolution."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.card import Card
from models.campaign import EventChoice
from models.enums import Stat, Operation, Target, Stacking
from engine.turn_order import CombatEntity, get_current_stat
from engine.encounters import (
    COMBAT_TURN_CAP,
    CombatResult,
    HazardResult,
    EventResult,
    play_card,
    resolve_combat,
    resolve_hazard,
    resolve_event,
)


def make_mod(stat, operation, value, duration=0, target=Target.ENEMY_SINGLE,
             stacking=Stacking.replace, tags=None):
    return Modifier(
        stat=stat,
        operation=operation,
        value=value,
        duration=duration,
        target=target,
        stacking=stacking,
        tags=tags or [],
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


def make_entity(id, hp=50000, speed=100000, power=0, defense=0, energy=3000,
                is_player=True, card_pool=None):
    e = CombatEntity(
        id=id,
        name=id,
        base_stats={
            Stat.HP: hp,
            Stat.Speed: speed,
            Stat.Power: power,
            Stat.Defense: defense,
            Stat.Energy: energy,
        },
        is_player=is_player,
        card_pool=card_pool or [],
    )
    e.current_energy = energy
    return e


# ---------------------------------------------------------------------------
# play_card tests
# ---------------------------------------------------------------------------

class TestPlayCard:
    def test_energy_cost_deducted(self):
        """Playing a card deducts its energy cost from caster.current_energy."""
        hero = make_entity("hero", energy=5)
        hero.current_energy = 5
        enemy = make_entity("enemy", is_player=False)
        card = make_card("strike", cost=2, damage=10000)

        play_card(card, hero, [enemy], [hero, enemy])

        assert hero.current_energy == 3

    def test_damage_applied_to_target(self):
        """FLAT_SUB HP effect reduces target's HP."""
        hero = make_entity("hero", power=0, defense=0)
        enemy = make_entity("enemy", hp=50000, defense=0, is_player=False)
        card = make_card("strike", cost=1, damage=10000)
        initial_hp = enemy.base_stats[Stat.HP]

        play_card(card, hero, [enemy], [hero, enemy])

        assert enemy.base_stats[Stat.HP] < initial_hp

    def test_power_adds_to_damage(self):
        """Caster's Power is added to damage dealt."""
        hero = make_entity("hero", power=5000, defense=0)
        enemy = make_entity("enemy", hp=50000, defense=0, is_player=False)
        card = make_card("strike", cost=1, damage=10000)
        initial_hp = enemy.base_stats[Stat.HP]

        play_card(card, hero, [enemy], [hero, enemy])

        # damage = 10000 + 5000 = 15000
        assert enemy.base_stats[Stat.HP] == initial_hp - 15000

    def test_defense_mitigates_damage(self):
        """Target's Defense is subtracted from incoming damage."""
        hero = make_entity("hero", power=0, defense=0)
        enemy = make_entity("enemy", hp=50000, defense=5000, is_player=False)
        card = make_card("strike", cost=1, damage=10000)
        initial_hp = enemy.base_stats[Stat.HP]

        play_card(card, hero, [enemy], [hero, enemy])

        # damage = 10000 - 5000 = 5000
        assert enemy.base_stats[Stat.HP] == initial_hp - 5000

    def test_damage_cannot_go_negative(self):
        """Defense >= attack means 0 damage dealt."""
        hero = make_entity("hero", power=0, defense=0)
        enemy = make_entity("enemy", hp=50000, defense=50000, is_player=False)
        card = make_card("strike", cost=1, damage=10000)
        initial_hp = enemy.base_stats[Stat.HP]

        play_card(card, hero, [enemy], [hero, enemy])

        assert enemy.base_stats[Stat.HP] == initial_hp  # no damage

    def test_target_dies_from_damage(self):
        """Target is marked dead if HP drops to 0."""
        hero = make_entity("hero", power=0)
        enemy = make_entity("enemy", hp=5000, defense=0, is_player=False)
        card = make_card("fatal_strike", cost=1, damage=10000)

        play_card(card, hero, [enemy], [hero, enemy])

        assert enemy.is_alive is False

    def test_insufficient_energy_prevents_card(self):
        """If current_energy < cost, energy goes negative (caller must enforce budget)."""
        hero = make_entity("hero", energy=1)
        hero.current_energy = 1
        enemy = make_entity("enemy", is_player=False)
        card = make_card("costly", cost=3, damage=10000)

        # play_card itself deducts; caller is responsible for checking budget
        play_card(card, hero, [enemy], [hero, enemy])
        assert hero.current_energy == -2

    def test_aoe_targets_all_enemies(self):
        """ENEMY_ALL card hits all living enemies."""
        hero = make_entity("hero", power=0)
        enemy1 = make_entity("e1", hp=20000, defense=0, is_player=False)
        enemy2 = make_entity("e2", hp=20000, defense=0, is_player=False)
        enemy3 = make_entity("e3", hp=20000, defense=0, is_player=False)
        aoe_card = make_card("aoe", cost=1, damage=5000, target=Target.ENEMY_ALL)

        play_card(aoe_card, hero, [], [hero, enemy1, enemy2, enemy3])

        assert enemy1.base_stats[Stat.HP] == 15000
        assert enemy2.base_stats[Stat.HP] == 15000
        assert enemy3.base_stats[Stat.HP] == 15000

    def test_dot_applied_to_active_modifiers(self):
        """Duration > 0 HP effect is added to target's active_modifiers."""
        hero = make_entity("hero")
        enemy = make_entity("enemy", is_player=False)
        dot_card = make_card("poison", cost=1, damage=5000, duration=3)

        play_card(dot_card, hero, [enemy], [hero, enemy])

        assert len(enemy.active_modifiers) > 0
        assert any(m.duration == 3 for m in enemy.active_modifiers)

    def test_dead_target_skipped(self):
        """play_card skips already-dead targets in AoE."""
        hero = make_entity("hero", power=0)
        dead_enemy = make_entity("dead", hp=20000, defense=0, is_player=False)
        dead_enemy.is_alive = False
        aoe_card = make_card("aoe", cost=1, damage=5000, target=Target.ENEMY_ALL)
        initial_hp = dead_enemy.base_stats[Stat.HP]

        play_card(aoe_card, hero, [], [hero, dead_enemy])

        # Dead enemy's HP should be unchanged
        assert dead_enemy.base_stats[Stat.HP] == initial_hp


# ---------------------------------------------------------------------------
# resolve_combat tests
# ---------------------------------------------------------------------------

class TestResolveCombat:
    def test_party_wins_strong_vs_weak(self):
        """Strong party destroys weak enemy."""
        hero = make_entity("hero", hp=100000, power=50000, defense=0, speed=100000, card_pool=["strike"])
        enemy = make_entity("enemy", hp=5000, power=0, defense=0, speed=50000, is_player=False)
        cards = {"strike": make_card("strike", cost=1, damage=20000)}

        result = resolve_combat([hero], [enemy], cards_by_id=cards)

        assert result.player_won is True
        assert "hero" in result.survivors

    def test_party_loses_weak_vs_strong(self):
        """Weak party is destroyed by strong enemies."""
        hero = make_entity("hero", hp=5000, power=0, defense=0, speed=50000)
        enemy = make_entity("enemy", hp=100000, power=50000, defense=0, speed=100000,
                            is_player=False, card_pool=["smash"])
        cards = {"smash": make_card("smash", cost=1, damage=30000)}

        result = resolve_combat([hero], [enemy], cards_by_id=cards)

        assert result.player_won is False

    def test_200_turn_cap(self):
        """Combat with unkillable entities (no cards, pure HP) hits 200-turn cap."""
        # Give both sides massive defense so they can't hurt each other, and no card_pool
        hero = make_entity("hero", hp=1000000, power=0, defense=999999, speed=100000)
        enemy = make_entity("enemy", hp=1000000, power=0, defense=999999, speed=100000, is_player=False)

        result = resolve_combat([hero], [enemy], cards_by_id={})

        assert result.turns_taken == COMBAT_TURN_CAP
        assert result.player_won is False  # cap returns False

    def test_region_modifier_applies_to_party(self):
        """Region modifier (ALLY_ALL Speed buff) applies to all party members."""
        hero = make_entity("hero", hp=100000, power=20000, speed=100000, card_pool=["strike"])
        enemy = make_entity("enemy", hp=5000, power=0, defense=0, speed=50000, is_player=False)
        cards = {"strike": make_card("strike", cost=1, damage=20000)}
        region_mod = make_mod(Stat.Speed, Operation.PCT_ADD, 50, duration=-1, target=Target.ALLY_ALL)

        result = resolve_combat([hero], [enemy], cards_by_id=cards, region_modifiers=[region_mod])

        # Hero should have gotten the speed buff; combat should still end
        assert result.player_won is True

    def test_stacking_in_combat_defense_replace(self):
        """Replace-type Defense buffs: only last one applies."""
        hero = make_entity("hero", hp=100000, speed=100000)
        # Add two defense mods with replace stacking — only the higher one should be active
        defense_mod1 = make_mod(Stat.Defense, Operation.FLAT_ADD, 1000, duration=-1,
                                target=Target.SELF, stacking=Stacking.replace)
        defense_mod2 = make_mod(Stat.Defense, Operation.FLAT_ADD, 5000, duration=-1,
                                target=Target.SELF, stacking=Stacking.replace)
        hero.active_modifiers = [defense_mod1, defense_mod2]
        # With replace stacking, only the last (5000) applies
        effective_defense = get_current_stat(hero, Stat.Defense)
        assert effective_defense == 5000

    def test_combat_logs_contain_entries(self):
        """Combat produces log messages."""
        hero = make_entity("hero", hp=100000, power=20000, speed=100000, card_pool=["strike"])
        enemy = make_entity("enemy", hp=5000, power=0, defense=0, speed=50000, is_player=False)
        cards = {"strike": make_card("strike", cost=1, damage=20000)}

        result = resolve_combat([hero], [enemy], cards_by_id=cards)

        assert len(result.combat_log) > 0


# ---------------------------------------------------------------------------
# resolve_hazard tests
# ---------------------------------------------------------------------------

class TestResolveHazard:
    def test_party_survives_light_hazard(self):
        """Party with enough HP survives a short low-damage hazard."""
        hero = make_entity("hero", hp=100000, defense=0)
        hazard_mod = make_mod(Stat.HP, Operation.FLAT_SUB, 5000, duration=0, target=Target.ALLY_ALL)

        result = resolve_hazard([hero], [hazard_mod], hazard_duration=3)

        assert result.survived is True
        assert result.damage_taken["hero"] == 15000  # 5000 * 3 turns

    def test_party_wipe_from_hazard(self):
        """Party with low HP is wiped by hazard."""
        hero = make_entity("hero", hp=10000, defense=0)
        hazard_mod = make_mod(Stat.HP, Operation.FLAT_SUB, 15000, duration=0, target=Target.ALLY_ALL)

        result = resolve_hazard([hero], [hazard_mod], hazard_duration=1)

        assert result.survived is False
        assert not hero.is_alive

    def test_defense_mitigates_hazard(self):
        """Party defense reduces hazard damage."""
        hero = make_entity("hero", hp=100000, defense=3000)
        hazard_mod = make_mod(Stat.HP, Operation.FLAT_SUB, 5000, duration=0, target=Target.ALLY_ALL)

        result = resolve_hazard([hero], [hazard_mod], hazard_duration=2)

        # damage per turn = 5000 - 3000 = 2000; total = 4000
        assert result.damage_taken["hero"] == 4000
        assert result.survived is True

    def test_multiple_party_members_take_damage(self):
        """All living party members take hazard damage."""
        hero1 = make_entity("h1", hp=100000, defense=0)
        hero2 = make_entity("h2", hp=100000, defense=0)
        hazard_mod = make_mod(Stat.HP, Operation.FLAT_SUB, 10000, duration=0, target=Target.ALLY_ALL)

        result = resolve_hazard([hero1, hero2], [hazard_mod], hazard_duration=1)

        assert result.damage_taken["h1"] == 10000
        assert result.damage_taken["h2"] == 10000

    def test_dead_member_skipped(self):
        """Already dead members do not take hazard damage."""
        hero1 = make_entity("h1", hp=100000, defense=0)
        dead = make_entity("dead", hp=100000, defense=0)
        dead.is_alive = False
        hazard_mod = make_mod(Stat.HP, Operation.FLAT_SUB, 10000, duration=0, target=Target.ALLY_ALL)

        result = resolve_hazard([hero1, dead], [hazard_mod], hazard_duration=1)

        assert result.damage_taken["dead"] == 0
        assert result.damage_taken["h1"] == 10000


# ---------------------------------------------------------------------------
# resolve_event tests
# ---------------------------------------------------------------------------

class TestResolveEvent:
    def _make_choices(self):
        """Build two event choices for testing."""
        buff_mod = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=-1, target=Target.SELF)
        cost_mod = make_mod(Stat.HP, Operation.FLAT_SUB, 10000, duration=0, target=Target.SELF)
        choice_0 = EventChoice(
            description="Take the power boost at cost of HP",
            effects=[buff_mod],
            cost=[cost_mod],
        )
        choice_1 = EventChoice(
            description="Pass without benefit",
            effects=[],
            cost=[],
        )
        return [choice_0, choice_1]

    def test_choice_0_applies_effects(self):
        """Choosing option 0 applies its effects to party."""
        hero = make_entity("hero")
        choices = self._make_choices()

        result = resolve_event([hero], choices, choice_index=0)

        assert result.choice_index == 0
        assert len(result.effects_applied) == 1
        assert any(m.stat == Stat.Power for m in hero.active_modifiers)

    def test_choice_0_applies_costs(self):
        """Choosing option 0 applies its HP cost to party."""
        hero = make_entity("hero", hp=50000)
        choices = self._make_choices()
        initial_hp = hero.base_stats[Stat.HP]

        result = resolve_event([hero], choices, choice_index=0)

        assert result.costs_applied is not None
        assert hero.base_stats[Stat.HP] == initial_hp - 10000

    def test_choice_1_no_effects(self):
        """Choosing option 1 (no effects/cost) leaves party unchanged."""
        hero = make_entity("hero", hp=50000)
        choices = self._make_choices()
        initial_hp = hero.base_stats[Stat.HP]

        result = resolve_event([hero], choices, choice_index=1)

        assert result.effects_applied == []
        assert result.costs_applied == []
        assert hero.base_stats[Stat.HP] == initial_hp

    def test_result_contains_log(self):
        """EventResult includes a log message."""
        hero = make_entity("hero")
        choices = self._make_choices()

        result = resolve_event([hero], choices, choice_index=0)

        assert len(result.combat_log) > 0
        assert "0" in result.combat_log[0]  # choice index in message

    def test_multiple_party_members_get_effects(self):
        """Effects from event choice are applied to all party members."""
        hero1 = make_entity("h1")
        hero2 = make_entity("h2")
        buff_mod = make_mod(Stat.Defense, Operation.FLAT_ADD, 2000, duration=-1, target=Target.SELF)
        choice = EventChoice(description="Fortify", effects=[buff_mod], cost=[])

        result = resolve_event([hero1, hero2], [choice], choice_index=0)

        assert any(m.stat == Stat.Defense for m in hero1.active_modifiers)
        assert any(m.stat == Stat.Defense for m in hero2.active_modifiers)
