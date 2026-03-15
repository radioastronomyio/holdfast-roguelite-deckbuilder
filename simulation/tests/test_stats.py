"""Tests for simulation/engine/stats.py — stat resolver with stacking rules."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking
from engine.stats import apply_stacking, calculate_stat


def make_mod(stat, operation, value, stacking=Stacking.replace, duration=0, tags=None):
    return Modifier(
        stat=stat,
        operation=operation,
        value=value,
        duration=duration,
        target=Target.SELF,
        stacking=stacking,
        tags=tags or [],
    )


class TestCalculateStat:
    def test_base_only(self):
        assert calculate_stat(100000, [], Stat.HP) == 100000

    def test_single_flat_add(self):
        mods = [make_mod(Stat.HP, Operation.FLAT_ADD, 20000)]
        assert calculate_stat(100000, mods, Stat.HP) == 120000

    def test_single_pct_add(self):
        mods = [make_mod(Stat.HP, Operation.PCT_ADD, 50)]
        assert calculate_stat(100000, mods, Stat.HP) == 150000

    def test_flat_then_pct(self):
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 20000),
            make_mod(Stat.HP, Operation.PCT_ADD, 50),
        ]
        assert calculate_stat(100000, mods, Stat.HP) == 180000

    def test_zero_base_with_pct(self):
        mods = [make_mod(Stat.HP, Operation.PCT_ADD, 50)]
        assert calculate_stat(0, mods, Stat.HP) == 0

    def test_flat_pct_multiply(self):
        # (100000+10000) * (100+20) // 100 = 132000; 132000 * 1500 // 1000 = 198000
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 10000),
            make_mod(Stat.HP, Operation.PCT_ADD, 20),
            make_mod(Stat.HP, Operation.MULTIPLY, 1500),
        ]
        assert calculate_stat(100000, mods, Stat.HP) == 198000

    def test_flat_sub(self):
        mods = [make_mod(Stat.HP, Operation.FLAT_SUB, 30000)]
        assert calculate_stat(100000, mods, Stat.HP) == 70000

    def test_pct_sub(self):
        mods = [make_mod(Stat.HP, Operation.PCT_SUB, 25)]
        assert calculate_stat(100000, mods, Stat.HP) == 75000

    def test_floor_at_zero_for_defense(self):
        mods = [make_mod(Stat.Defense, Operation.FLAT_SUB, 50000)]
        result = calculate_stat(10000, mods, Stat.Defense)
        assert result == 0

    def test_hp_can_go_negative(self):
        mods = [make_mod(Stat.HP, Operation.FLAT_SUB, 50000)]
        result = calculate_stat(10000, mods, Stat.HP)
        assert result == -40000

    def test_multiple_multiply(self):
        # 100000 * 1500 // 1000 = 150000; 150000 * 2000 // 1000 = 300000
        # Must use stacking=stack so both MULTIPLY mods survive apply_stacking
        mods = [
            make_mod(Stat.HP, Operation.MULTIPLY, 1500, stacking=Stacking.stack),
            make_mod(Stat.HP, Operation.MULTIPLY, 2000, stacking=Stacking.stack),
        ]
        assert calculate_stat(100000, mods, Stat.HP) == 300000

    def test_filters_by_stat(self):
        """Modifiers for other stats should not affect the target stat."""
        mods = [make_mod(Stat.Power, Operation.FLAT_ADD, 50000)]
        assert calculate_stat(100000, mods, Stat.HP) == 100000

    def test_speed_floors_at_zero(self):
        mods = [make_mod(Stat.Speed, Operation.FLAT_SUB, 200000)]
        assert calculate_stat(100000, mods, Stat.Speed) == 0

    def test_energy_floors_at_zero(self):
        mods = [make_mod(Stat.Energy, Operation.FLAT_SUB, 200000)]
        assert calculate_stat(5000, mods, Stat.Energy) == 0


class TestApplyStacking:
    def test_stacking_replace_keeps_last(self):
        """Two FLAT_ADD replace mods: only last (value=20000) applies."""
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 10000, stacking=Stacking.replace),
            make_mod(Stat.HP, Operation.FLAT_ADD, 20000, stacking=Stacking.replace),
        ]
        result = calculate_stat(100000, mods, Stat.HP)
        assert result == 120000  # 100000 + 20000

    def test_stacking_stack_sums_all(self):
        """Two FLAT_ADD stack mods: both apply (10000 + 20000)."""
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 10000, stacking=Stacking.stack),
            make_mod(Stat.HP, Operation.FLAT_ADD, 20000, stacking=Stacking.stack),
        ]
        result = calculate_stat(100000, mods, Stat.HP)
        assert result == 130000  # 100000 + 10000 + 20000

    def test_stacking_max_keeps_highest(self):
        """Two FLAT_ADD max mods: only highest (20000) applies."""
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 10000, stacking=Stacking.max),
            make_mod(Stat.HP, Operation.FLAT_ADD, 20000, stacking=Stacking.max),
        ]
        result = calculate_stat(100000, mods, Stat.HP)
        assert result == 120000  # 100000 + 20000

    def test_apply_stacking_replace_returns_one(self):
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 10000, stacking=Stacking.replace),
            make_mod(Stat.HP, Operation.FLAT_ADD, 20000, stacking=Stacking.replace),
        ]
        collapsed = apply_stacking(mods)
        assert len(collapsed) == 1
        assert collapsed[0].value == 20000

    def test_apply_stacking_stack_returns_all(self):
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 10000, stacking=Stacking.stack),
            make_mod(Stat.HP, Operation.FLAT_ADD, 20000, stacking=Stacking.stack),
        ]
        collapsed = apply_stacking(mods)
        assert len(collapsed) == 2

    def test_apply_stacking_max_returns_highest(self):
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 5000, stacking=Stacking.max),
            make_mod(Stat.HP, Operation.FLAT_ADD, 30000, stacking=Stacking.max),
            make_mod(Stat.HP, Operation.FLAT_ADD, 15000, stacking=Stacking.max),
        ]
        collapsed = apply_stacking(mods)
        assert len(collapsed) == 1
        assert collapsed[0].value == 30000

    def test_different_operations_kept_separate(self):
        """FLAT_ADD and PCT_ADD are in separate groups even with same stat."""
        mods = [
            make_mod(Stat.HP, Operation.FLAT_ADD, 10000, stacking=Stacking.replace),
            make_mod(Stat.HP, Operation.FLAT_ADD, 20000, stacking=Stacking.replace),
            make_mod(Stat.HP, Operation.PCT_ADD, 10, stacking=Stacking.replace),
            make_mod(Stat.HP, Operation.PCT_ADD, 20, stacking=Stacking.replace),
        ]
        collapsed = apply_stacking(mods)
        # Should have one FLAT_ADD (last=20000) and one PCT_ADD (last=20)
        assert len(collapsed) == 2

    def test_empty_modifiers(self):
        collapsed = apply_stacking([])
        assert collapsed == []
