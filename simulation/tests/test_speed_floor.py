"""Tests for Speed minimum floor in calculate_stat (M3d Task 5.1)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking
from engine.stats import calculate_stat, SPEED_MIN_FLOOR


def make_pct_mod(stat: Stat, operation: Operation, value: int) -> Modifier:
    return Modifier(
        stat=stat, operation=operation, value=value, duration=-1,
        target=Target.SELF, stacking=Stacking.stack, tags=[],
    )


class TestSpeedFloor:
    def test_speed_floor_constant_exists(self):
        """SPEED_MIN_FLOOR is a named constant with value 10."""
        assert SPEED_MIN_FLOOR == 10

    def test_speed_minimum_floor(self):
        """Speed debuffed below the floor is clamped to SPEED_MIN_FLOOR * STAT_SCALE."""
        base = 50 * STAT_SCALE
        # -200% Speed — would normally floor at 0, but min floor applies
        mods = [make_pct_mod(Stat.Speed, Operation.PCT_SUB, 200)]
        result = calculate_stat(base, mods, Stat.Speed)
        assert result == SPEED_MIN_FLOOR * STAT_SCALE, (
            f"Expected {SPEED_MIN_FLOOR * STAT_SCALE}, got {result}"
        )

    def test_speed_floor_with_stacking(self):
        """Multiple Speed debuffs together still cannot drop below the floor."""
        base = 40 * STAT_SCALE
        mods = [
            make_pct_mod(Stat.Speed, Operation.PCT_SUB, 100),
            make_pct_mod(Stat.Speed, Operation.PCT_SUB, 100),
        ]
        result = calculate_stat(base, mods, Stat.Speed)
        assert result == SPEED_MIN_FLOOR * STAT_SCALE, (
            f"Expected {SPEED_MIN_FLOOR * STAT_SCALE}, got {result}"
        )

    def test_shield_bash_not_full_stun(self):
        """shield_bash debuff at -50% Speed on a base-50 entity still leaves CT > 0."""
        base = 50 * STAT_SCALE
        # shield_bash applies PCT_SUB 50 (as of M3d fix)
        mods = [make_pct_mod(Stat.Speed, Operation.PCT_SUB, 50)]
        result = calculate_stat(base, mods, Stat.Speed)
        # -50% of 50 = 25, which is above the floor — entity is slowed, NOT stunned
        expected = base * (100 - 50) // 100
        assert result == expected, f"Expected {expected}, got {result}"
        assert result > 0, "Entity should retain positive Speed after shield_bash"
        assert result >= SPEED_MIN_FLOOR * STAT_SCALE, "Speed must be at or above floor"

    def test_speed_floor_does_not_affect_other_stats(self):
        """The minimum floor only applies to Speed, not HP or Defense."""
        base = 50 * STAT_SCALE
        mods = [make_pct_mod(Stat.Defense, Operation.PCT_SUB, 200)]
        result = calculate_stat(base, mods, Stat.Defense)
        # Defense floors at 0 (non-HP stats can't go below 0)
        assert result == 0, f"Defense should floor at 0, got {result}"
