"""Tests for AggressiveAI improvements (M3c Task 6.2)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.card import Card
from models.enums import Stat, Operation, Target, Stacking
from engine.turn_order import CombatEntity
from agents.heuristics import AggressiveAI


def make_mod(stat, operation, value, duration=0, target=Target.ENEMY_SINGLE):
    return Modifier(
        stat=stat, operation=operation, value=value, duration=duration,
        target=target, stacking=Stacking.replace, tags=[],
    )


def make_card(id, cost, effects):
    return Card(id=id, name=id, energy_cost=cost, effects=effects)


def make_damage_card(id, cost, damage, target=Target.ENEMY_SINGLE):
    return make_card(id, cost, [make_mod(Stat.HP, Operation.FLAT_SUB, damage * STAT_SCALE, target=target)])


def make_heal_card(id, cost, heal):
    return make_card(id, cost, [make_mod(Stat.HP, Operation.FLAT_ADD, heal * STAT_SCALE, target=Target.SELF)])


def make_entity(id, hp, max_hp=None, speed=100000, power=0, energy=10, is_player=True):
    if max_hp is None:
        max_hp = hp
    return CombatEntity(
        id=id, name=id,
        base_stats={
            Stat.HP: max_hp * STAT_SCALE,
            Stat.Speed: speed,
            Stat.Power: power * STAT_SCALE,
            Stat.Defense: 0,
            Stat.Energy: energy,
        },
        is_player=is_player,
        card_pool=[],
        active_modifiers=[],
        current_energy=energy,
    )


class TestAggressiveAI:
    def setup_method(self):
        self.ai = AggressiveAI()

    def test_emergency_heal(self):
        """AggressiveAI plays a heal card when caster is below 25% HP."""
        # Caster at 20% HP (20/100)
        caster = make_entity("player", hp=20 * STAT_SCALE, max_hp=100 * STAT_SCALE)
        # Manually set base_stats so hp_ratio computes correctly
        caster.base_stats[Stat.HP] = 100 * STAT_SCALE  # max
        # Reduce current HP via modifier — use a simpler approach: set base_stats low
        caster2 = make_entity("player", hp=20, max_hp=100)
        # caster2's base_stats[HP] is the "max"; we need current HP to be low
        # Use a modified entity where base_stat represents current HP
        # hp_ratio uses get_current_stat(HP) / base_stats[HP]
        # get_current_stat = calculate_stat(base_stats[HP], modifiers) with no mods = base_stats[HP]
        # So to have 20% HP: base_stats[HP] = 20 * STAT_SCALE, and we need "max" = 100 * STAT_SCALE
        # But hp_ratio uses entity.base_stats.get(Stat.HP, current_hp) as max_hp
        # Since there are no modifiers, current_hp == base_stats[HP], so ratio = 100%
        # To simulate low HP: we need base_stats to differ from max. We can set a FLAT_SUB modifier.
        from models.modifier import Modifier
        damage_mod = Modifier(
            stat=Stat.HP, operation=Operation.FLAT_SUB,
            value=80 * STAT_SCALE,  # -80 HP damage taken
            duration=-1, target=Target.SELF, stacking=Stacking.stack, tags=[],
        )
        caster = make_entity("player", hp=100, max_hp=100)
        caster.active_modifiers = [damage_mod]

        heal = make_heal_card("heal", cost=1, heal=20)
        damage = make_damage_card("strike", cost=1, damage=15)
        enemy = make_entity("enemy", hp=50, is_player=False)

        result = self.ai.select_card(caster, [heal, damage], [caster], [enemy])
        assert result is not None
        card, targets = result
        assert card.id == "heal", f"Expected heal card, got {card.id}"

    def test_overkill_prevention(self):
        """AggressiveAI switches to highest-HP enemy instead of overkilling a near-dead one."""
        caster = make_entity("player", hp=100, energy=10)
        # Enemy 1: 1 HP (nearly dead)
        enemy_low = make_entity("e_low", hp=1, is_player=False)
        # Enemy 2: 50 HP (healthy)
        enemy_high = make_entity("e_high", hp=50, is_player=False)

        # Big damage card that would massively overkill the 1-HP enemy
        big_strike = make_damage_card("big_strike", cost=2, damage=15)

        result = self.ai.select_card(caster, [big_strike], [caster], [enemy_low, enemy_high])
        assert result is not None
        card, targets = result
        # Should target the high-HP enemy, not the near-dead one
        assert enemy_high in targets, (
            f"Expected to target high-HP enemy, got {[t.id for t in targets]}"
        )

    def test_aoe_preference(self):
        """AggressiveAI prefers AoE card over single-target when 3+ enemies alive."""
        caster = make_entity("player", hp=100, energy=10)
        enemies = [
            make_entity(f"e{i}", hp=30, is_player=False)
            for i in range(3)
        ]

        single = make_damage_card("single", cost=2, damage=12)
        aoe = make_damage_card("aoe", cost=2, damage=8, target=Target.ENEMY_ALL)

        result = self.ai.select_card(caster, [single, aoe], [caster], enemies)
        assert result is not None
        card, targets = result
        assert card.id == "aoe", (
            f"Expected AoE card with 3 enemies, got {card.id}"
        )
