"""Tests for AggressiveAI v2 rework (M3d Task 5.2)."""
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


def make_debuff_card(id, cost, shred_value):
    """Defense shred card — no HP damage."""
    return make_card(id, cost, [
        make_mod(Stat.Defense, Operation.PCT_SUB, shred_value, target=Target.ENEMY_ALL),
    ])


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


class FakeCampaignState:
    """Minimal campaign state stub for select_party tests."""
    def __init__(self, roster, party_size=2):
        self.roster = roster
        self.party_size = party_size


class FakeCharacter:
    """Minimal character stub."""
    def __init__(self, id, hp, power):
        self.id = id
        self.base_stats = {
            Stat.HP: hp * STAT_SCALE,
            Stat.Power: power * STAT_SCALE,
            Stat.Defense: 0,
            Stat.Speed: 50 * STAT_SCALE,
            Stat.Energy: 4,
        }


class TestAggressiveAIV2:
    def setup_method(self):
        self.ai = AggressiveAI()

    def test_world_card_acceptance_net_positive(self):
        """evaluate_world_card accepts a net-positive card (upside >= downside)."""
        from models.campaign import WorldCard

        upside_mod = make_mod(Stat.Power, Operation.PCT_ADD, 20, target=Target.ALLY_SINGLE)
        downside_mod = make_mod(Stat.Speed, Operation.PCT_SUB, 10, target=Target.ALLY_SINGLE)

        card = WorldCard(
            id="test_wc",
            name="Test World Card",
            description="Gain power, lose some speed.",
            upside=[upside_mod],
            downside=[downside_mod],
        )

        result = self.ai.evaluate_world_card(card, None, None)
        assert result is True, "Should accept net-positive world card"

    def test_world_card_rejection_catastrophic_hp_loss(self):
        """evaluate_world_card rejects a card with >= 30 display scale HP loss to allies."""
        from models.campaign import WorldCard

        ally_hp_loss = make_mod(
            Stat.HP, Operation.FLAT_SUB, 30 * STAT_SCALE,
            target=Target.ALLY_SINGLE,
        )
        upside_mod = make_mod(Stat.Power, Operation.PCT_ADD, 50, target=Target.ALLY_SINGLE)

        card = WorldCard(
            id="test_wc_bad",
            name="Dangerous World Card",
            description="Gain power, lose significant HP.",
            upside=[upside_mod],
            downside=[ally_hp_loss],
        )

        result = self.ai.evaluate_world_card(card, None, None)
        assert result is False, "Should reject card with catastrophic HP loss"

    def test_debuff_before_damage(self):
        """AggressiveAI plays defense shred before a damage card when both are affordable."""
        caster = make_entity("player", hp=100, energy=10)
        enemy = make_entity("enemy", hp=80, is_player=False)

        shred = make_debuff_card("acid_flask", cost=1, shred_value=25)
        strike = make_damage_card("strike", cost=2, damage=15)

        result = self.ai.select_card(caster, [shred, strike], [caster], [enemy])
        assert result is not None
        card, targets = result
        assert card.id == "acid_flask", (
            f"Expected defense shred card first, got {card.id}"
        )

    def test_focus_fire_on_lowest_hp(self):
        """AggressiveAI targets the lowest-HP enemy for focus-fire."""
        caster = make_entity("player", hp=100, energy=10)
        enemy_low = make_entity("e_low", hp=10, is_player=False)
        enemy_high = make_entity("e_high", hp=60, is_player=False)

        # Damage card that does 12 — doesn't massively overkill 10-HP enemy
        strike = make_damage_card("strike", cost=2, damage=12)

        result = self.ai.select_card(caster, [strike], [caster], [enemy_low, enemy_high])
        assert result is not None
        card, targets = result
        assert enemy_low in targets, (
            f"Expected focus-fire on lowest-HP enemy, got {[t.id for t in targets]}"
        )

    def test_party_includes_tank_when_all_picks_are_squishies(self):
        """select_party swaps the weakest Power pick for the tankiest character when all chosen are low-HP.

        Roster: dps0(hp=10,pow=80), dps1(hp=10,pow=75), dps2(hp=50,pow=70), tank(hp=100,pow=10)
        Sorted HP: [10k, 10k, 50k, 100k] — median at index 2 = 50k
        Top-2 by Power: dps0, dps1 — both hp=10k < median 50k → swap condition triggers
        Expected: tank replaces lowest-Power pick (dps1)
        """
        dps0 = FakeCharacter("dps0", hp=10, power=80)
        dps1 = FakeCharacter("dps1", hp=10, power=75)
        dps2 = FakeCharacter("dps2", hp=50, power=70)
        tank = FakeCharacter("tank", hp=100, power=10)

        state = FakeCampaignState(roster=[dps0, dps1, dps2, tank], party_size=2)

        party = self.ai.select_party(state, None, None)
        assert tank in party, (
            f"Tank should be in party when all high-Power picks are squishy. Got: {[c.id for c in party]}"
        )
