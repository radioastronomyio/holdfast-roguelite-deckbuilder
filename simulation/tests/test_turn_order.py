"""Tests for simulation/engine/turn_order.py — CT priority-queue turn order system."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking
from engine.turn_order import (
    CombatEntity,
    CT_THRESHOLD,
    get_current_stat,
    tick_until_next_turn,
    process_turn_start,
)


def make_mod(stat, operation, value, duration=-1, stacking=Stacking.replace, tags=None):
    return Modifier(
        stat=stat,
        operation=operation,
        value=value,
        duration=duration,
        target=Target.SELF,
        stacking=stacking,
        tags=tags or [],
    )


def make_entity(id, speed, hp=140000, energy=3000, is_player=True, modifiers=None):
    return CombatEntity(
        id=id,
        name=id,
        base_stats={
            Stat.HP: hp,
            Stat.Speed: speed,
            Stat.Power: 0,
            Stat.Defense: 0,
            Stat.Energy: energy,
        },
        active_modifiers=modifiers or [],
        is_player=is_player,
    )


class TestTickUntilNextTurn:
    def test_faster_entity_goes_first(self):
        """Entity with Speed 120000 acts before entity with Speed 80000."""
        a = make_entity("A", speed=120000)
        b = make_entity("B", speed=80000)
        actor = tick_until_next_turn([a, b])
        assert actor.id == "A"

    def test_no_living_entities_raises(self):
        a = make_entity("A", speed=100000)
        a.is_alive = False
        with pytest.raises(ValueError, match="No living entities"):
            tick_until_next_turn([a])

    def test_ct_decremented_after_turn(self):
        """Actor's CT should be reduced by CT_THRESHOLD after acting."""
        a = make_entity("A", speed=100000)
        tick_until_next_turn([a])
        assert a.ct == 0  # exactly hit threshold, no overflow

    def test_ct_overflow_preserved(self):
        """If entity overshoots threshold, overflow is kept."""
        # Speed 150000 means entity needs ceil(100000/150000) = 1 tick → CT = 150000
        a = make_entity("A", speed=150000)
        b = make_entity("B", speed=50000)
        tick_until_next_turn([a, b])
        # After tick: a.ct was 150000, subtract 100000 → 50000
        assert a.ct == 50000

    def test_speed_ratio_over_cycles(self):
        """
        A: Speed 150000, B: Speed 50000 — A should get ~3 turns per B turn over 10 cycles.
        """
        a = make_entity("A", speed=150000)
        b = make_entity("B", speed=50000)
        entities = [a, b]

        a_turns = 0
        b_turns = 0
        for _ in range(40):
            actor = tick_until_next_turn(entities)
            if actor.id == "A":
                a_turns += 1
            else:
                b_turns += 1

        # A should have roughly 3x the turns of B
        assert a_turns == pytest.approx(b_turns * 3, abs=3)

    def test_ct_tie_break_higher_overflow(self):
        """When two entities have same speed, tie should be resolved by overflow then list order."""
        # Both have same speed, start at same CT — first in list wins tie by list position
        a = make_entity("A", speed=100000)
        b = make_entity("B", speed=100000)
        actor = tick_until_next_turn([a, b])
        # Both reach CT_THRESHOLD exactly; a is first in list
        assert actor.id == "A"

    def test_dead_entity_skipped(self):
        """Dead entities do not participate in tick."""
        a = make_entity("A", speed=100000)
        b = make_entity("B", speed=200000)
        b.is_alive = False
        actor = tick_until_next_turn([a, b])
        assert actor.id == "A"

    def test_dead_entities_never_act(self):
        """Verify dead entity never gets a turn over multiple cycles."""
        a = make_entity("A", speed=100000)
        b = make_entity("B", speed=80000)
        b.is_alive = False
        entities = [a, b]
        for _ in range(5):
            actor = tick_until_next_turn(entities)
            assert actor.id == "A"


class TestProcessTurnStart:
    def test_energy_refreshes_to_base(self):
        """current_energy is set to calculated Energy stat on turn start."""
        e = make_entity("A", speed=100000, energy=3000)
        e.current_energy = 0
        process_turn_start(e)
        assert e.current_energy == 3000

    def test_modifier_duration_decrements(self):
        """Modifier with duration 3 has duration 2 after one turn start."""
        mod = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=3)
        e = make_entity("A", speed=100000)
        e.active_modifiers = [mod]
        process_turn_start(e)
        assert e.active_modifiers[0].duration == 2

    def test_modifier_expires_after_duration(self):
        """Modifier with duration 1 is gone after turn start (decrements to 0, then removed)."""
        mod = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=1)
        e = make_entity("A", speed=100000)
        e.active_modifiers = [mod]
        process_turn_start(e)
        assert len(e.active_modifiers) == 0

    def test_modifier_duration_3_gone_after_3_turns(self):
        """Modifier with duration 3 should be gone after 3 turn starts."""
        mod = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=3)
        e = make_entity("A", speed=100000)
        e.active_modifiers = [mod]
        for _ in range(3):
            process_turn_start(e)
        assert len(e.active_modifiers) == 0

    def test_permanent_modifier_persists(self):
        """Modifier with duration -1 persists after many turns."""
        mod = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=-1)
        e = make_entity("A", speed=100000)
        e.active_modifiers = [mod]
        for _ in range(10):
            process_turn_start(e)
        assert len(e.active_modifiers) == 1
        assert e.active_modifiers[0].duration == -1

    def test_dot_damage_reduces_effective_hp(self):
        """A FLAT_SUB HP modifier reduces effective HP via get_current_stat."""
        # Add a HP reduction modifier (DoT)
        dot = make_mod(Stat.HP, Operation.FLAT_SUB, 20000, duration=3)
        e = make_entity("A", speed=100000, hp=50000)
        e.active_modifiers = [dot]
        effective_hp = get_current_stat(e, Stat.HP)
        assert effective_hp == 30000  # 50000 - 20000

    def test_entity_dies_from_dot(self):
        """Entity with HP mod that makes effective HP <= 0 is marked dead at turn start."""
        dot = make_mod(Stat.HP, Operation.FLAT_SUB, 60000, duration=3)
        e = make_entity("A", speed=100000, hp=50000)
        e.active_modifiers = [dot]
        assert e.is_alive is True
        logs = process_turn_start(e)
        assert e.is_alive is False
        assert any("died" in log for log in logs)

    def test_speed_buff_changes_turn_frequency(self):
        """Entity with PCT_ADD Speed 50 modifier gets 50% more turns."""
        # Entity A with speed buff vs entity B without
        a = make_entity("A", speed=100000)
        speed_buff = make_mod(Stat.Speed, Operation.PCT_ADD, 50, duration=-1)
        a.active_modifiers = [speed_buff]
        b = make_entity("B", speed=100000)
        entities = [a, b]

        a_turns = 0
        b_turns = 0
        for _ in range(25):
            actor = tick_until_next_turn(entities)
            if actor.id == "A":
                a_turns += 1
            else:
                b_turns += 1

        # A should have ~1.5x the turns of B
        assert a_turns > b_turns

    def test_expired_modifier_log_message(self):
        """process_turn_start logs when modifiers expire."""
        mod = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=1)
        e = make_entity("A", speed=100000)
        e.active_modifiers = [mod]
        logs = process_turn_start(e)
        assert any("expired" in log for log in logs)

    def test_energy_refreshes_with_modifier(self):
        """current_energy reflects Energy stat including active modifiers."""
        energy_buff = make_mod(Stat.Energy, Operation.FLAT_ADD, 1000, duration=-1)
        e = make_entity("A", speed=100000, energy=3000)
        e.active_modifiers = [energy_buff]
        process_turn_start(e)
        assert e.current_energy == 4000
