"""Tests for simulation/engine/special_handlers.py — resolver special handlers."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking
from engine.turn_order import CombatEntity
from engine.special_handlers import (
    SpecialHandlerContext,
    handle_no_refresh,
    handle_duration_multiply,
    handle_delayed_start,
    check_special_tags,
    apply_special_handler,
    SPECIAL_TAG_SET,
)


def make_mod(stat, operation, value, duration=-1, tags=None, stacking=Stacking.replace):
    return Modifier(
        stat=stat,
        operation=operation,
        value=value,
        duration=duration,
        target=Target.SELF,
        stacking=stacking,
        tags=tags or [],
    )


def make_entity(id, hp=50000, speed=100000, energy=3000):
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
        is_player=True,
    )


class TestHandleNoRefresh:
    def test_turn_1_excludes_modifier_from_energy_calc(self):
        """Turn 1: modifier is excluded from energy calc (modifiers_to_exclude populated)."""
        no_refresh_mod = make_mod(
            Stat.Energy, Operation.FLAT_SUB, 3000,
            duration=2, tags=["no_refresh_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [no_refresh_mod]

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1)
        handle_no_refresh(ctx)

        assert no_refresh_mod in ctx.modifiers_to_exclude
        assert ctx.suppress_energy_refresh is False

    def test_turn_1_does_not_suppress_energy_refresh(self):
        """Turn 1: energy refreshes normally (modifier excluded but not suppressed)."""
        no_refresh_mod = make_mod(
            Stat.Energy, Operation.FLAT_SUB, 3000,
            duration=2, tags=["no_refresh_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [no_refresh_mod]

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1)
        handle_no_refresh(ctx)

        assert ctx.suppress_energy_refresh is False

    def test_turn_2_suppresses_energy_refresh(self):
        """Turn 2: suppress_energy_refresh is True."""
        no_refresh_mod = make_mod(
            Stat.Energy, Operation.FLAT_SUB, 3000,
            duration=1, tags=["no_refresh_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [no_refresh_mod]

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=2)
        handle_no_refresh(ctx)

        assert ctx.suppress_energy_refresh is True

    def test_turn_3_no_suppression(self):
        """Turn 3: modifier expired, no suppression, no exclusion."""
        entity = make_entity("A")
        entity.active_modifiers = []  # modifier has expired by turn 3

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=3)
        handle_no_refresh(ctx)

        assert ctx.suppress_energy_refresh is False
        assert ctx.modifiers_to_exclude == []


class TestHandleDurationMultiply:
    def test_doubles_positive_duration(self):
        """Incoming modifier with duration 3 becomes duration 6."""
        incoming = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=3)
        entity = make_entity("A")
        entity.active_modifiers = []

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1, incoming_modifier=incoming)
        handle_duration_multiply(ctx)

        assert ctx.modified_incoming is not None
        assert ctx.modified_incoming.duration == 6

    def test_ignores_permanent_duration(self):
        """Incoming modifier with duration -1 stays -1."""
        incoming = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=-1)
        entity = make_entity("A")

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1, incoming_modifier=incoming)
        handle_duration_multiply(ctx)

        assert ctx.modified_incoming is not None
        assert ctx.modified_incoming.duration == -1

    def test_ignores_instant_duration(self):
        """Incoming modifier with duration 0 stays 0."""
        incoming = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=0)
        entity = make_entity("A")

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1, incoming_modifier=incoming)
        handle_duration_multiply(ctx)

        assert ctx.modified_incoming is not None
        assert ctx.modified_incoming.duration == 0

    def test_no_incoming_modifier_noop(self):
        """No incoming_modifier: handler does nothing."""
        entity = make_entity("A")
        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1, incoming_modifier=None)
        handle_duration_multiply(ctx)

        assert ctx.modified_incoming is None

    def test_doubles_duration_1(self):
        """Duration 1 becomes 2."""
        incoming = make_mod(Stat.Defense, Operation.PCT_ADD, 20, duration=1)
        entity = make_entity("A")

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1, incoming_modifier=incoming)
        handle_duration_multiply(ctx)

        assert ctx.modified_incoming.duration == 2


class TestHandleDelayedStart:
    def test_turn_1_excludes_and_skips_decrement(self):
        """Turn 1: delayed modifier excluded from stat calc AND skipped from duration decrement."""
        delayed_mod = make_mod(
            Stat.Speed, Operation.PCT_SUB, 50,
            duration=3, tags=["delayed_start_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [delayed_mod]

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1)
        handle_delayed_start(ctx)

        assert delayed_mod in ctx.modifiers_to_exclude
        assert delayed_mod in ctx.modifiers_to_skip_decrement

    def test_turn_2_modifier_active(self):
        """Turn 2: delayed modifier is NOT excluded or skipped."""
        delayed_mod = make_mod(
            Stat.Speed, Operation.PCT_SUB, 50,
            duration=2, tags=["delayed_start_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [delayed_mod]

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=2)
        handle_delayed_start(ctx)

        assert delayed_mod not in ctx.modifiers_to_exclude
        assert delayed_mod not in ctx.modifiers_to_skip_decrement

    def test_turn_3_modifier_active(self):
        """Turn 3: same as turn 2, modifier active and counting down."""
        delayed_mod = make_mod(
            Stat.Speed, Operation.PCT_SUB, 50,
            duration=1, tags=["delayed_start_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [delayed_mod]

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=3)
        handle_delayed_start(ctx)

        assert delayed_mod not in ctx.modifiers_to_exclude
        assert delayed_mod not in ctx.modifiers_to_skip_decrement


class TestCheckSpecialTags:
    def test_finds_no_refresh_tag(self):
        mod = make_mod(Stat.Energy, Operation.FLAT_SUB, 3000, tags=["no_refresh_turn_2"])
        assert check_special_tags(mod) == "no_refresh_turn_2"

    def test_finds_duration_multiply_tag(self):
        mod = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, tags=["status_duration_multiply_2"])
        assert check_special_tags(mod) == "status_duration_multiply_2"

    def test_finds_delayed_start_tag(self):
        mod = make_mod(Stat.Speed, Operation.PCT_SUB, 50, tags=["delayed_start_turn_2"])
        assert check_special_tags(mod) == "delayed_start_turn_2"

    def test_no_special_tag_returns_none(self):
        mod = make_mod(Stat.HP, Operation.FLAT_ADD, 10000, tags=["attack", "physical"])
        assert check_special_tags(mod) is None

    def test_empty_tags_returns_none(self):
        mod = make_mod(Stat.HP, Operation.FLAT_ADD, 10000, tags=[])
        assert check_special_tags(mod) is None

    def test_returns_first_matching_tag(self):
        """If multiple special tags, returns first found."""
        mod = make_mod(Stat.HP, Operation.FLAT_ADD, 10000,
                       tags=["no_refresh_turn_2", "delayed_start_turn_2"])
        result = check_special_tags(mod)
        assert result in SPECIAL_TAG_SET


class TestApplySpecialHandler:
    def test_dispatches_no_refresh_handler(self):
        """apply_special_handler correctly dispatches to handle_no_refresh."""
        no_refresh_mod = make_mod(
            Stat.Energy, Operation.FLAT_SUB, 3000,
            duration=2, tags=["no_refresh_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [no_refresh_mod]

        ctx = SpecialHandlerContext(entity=entity, encounter_turn=2)
        apply_special_handler("no_refresh_turn_2", ctx)

        assert ctx.suppress_energy_refresh is True

    def test_dispatches_duration_multiply_handler(self):
        """apply_special_handler correctly dispatches to handle_duration_multiply."""
        incoming = make_mod(Stat.Power, Operation.FLAT_ADD, 5000, duration=3)
        entity = make_entity("A")
        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1, incoming_modifier=incoming)

        apply_special_handler("status_duration_multiply_2", ctx)

        assert ctx.modified_incoming is not None
        assert ctx.modified_incoming.duration == 6

    def test_dispatches_delayed_start_handler(self):
        """apply_special_handler correctly dispatches to handle_delayed_start."""
        delayed_mod = make_mod(
            Stat.Speed, Operation.PCT_SUB, 50,
            duration=3, tags=["delayed_start_turn_2"]
        )
        entity = make_entity("A")
        entity.active_modifiers = [delayed_mod]
        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1)

        apply_special_handler("delayed_start_turn_2", ctx)

        assert delayed_mod in ctx.modifiers_to_exclude

    def test_unknown_tag_ignored(self):
        """Unknown tag does not raise an error."""
        entity = make_entity("A")
        ctx = SpecialHandlerContext(entity=entity, encounter_turn=1)
        # Should not raise
        apply_special_handler("nonexistent_tag_xyz", ctx)
        assert ctx.suppress_energy_refresh is False
        assert ctx.modified_incoming is None
