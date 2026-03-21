"""Tests for Speed percentage cap in calculate_stat (M3c Task 6.1)."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking
from engine.stats import calculate_stat, SPEED_PCT_CAP


def make_pct_mod(stat: Stat, operation: Operation, value: int) -> Modifier:
    return Modifier(
        stat=stat, operation=operation, value=value, duration=-1,
        target=Target.SELF, stacking=Stacking.stack, tags=[],
    )


class TestSpeedCap:
    def test_speed_pct_capped(self):
        """Two +50% Speed mods (total +100%) are capped at +75%."""
        base = 50 * STAT_SCALE
        mods = [
            make_pct_mod(Stat.Speed, Operation.PCT_ADD, 50),
            make_pct_mod(Stat.Speed, Operation.PCT_ADD, 50),
        ]
        result = calculate_stat(base, mods, Stat.Speed)
        expected_uncapped = base * (100 + 100) // 100
        expected_capped = base * (100 + SPEED_PCT_CAP) // 100
        assert result == expected_capped, f"Expected {expected_capped}, got {result}"
        assert result < expected_uncapped, "Cap did not reduce the value"

    def test_speed_negative_not_capped_by_speed_pct_cap(self):
        """Negative Speed debuffs are not capped by SPEED_PCT_CAP (only positive side is capped).
        The result floors at SPEED_MIN_FLOOR * STAT_SCALE, not at the cap value (M3d)."""
        from engine.stats import SPEED_MIN_FLOOR
        base = 50 * STAT_SCALE
        mods = [make_pct_mod(Stat.Speed, Operation.PCT_SUB, 200)]
        result = calculate_stat(base, mods, Stat.Speed)
        # Negative debuffs bypass SPEED_PCT_CAP; result is clamped to SPEED_MIN_FLOOR
        assert result == SPEED_MIN_FLOOR * STAT_SCALE, (
            f"Expected {SPEED_MIN_FLOOR * STAT_SCALE} (min floor), got {result}"
        )

    def test_speed_cap_constant(self):
        """SPEED_PCT_CAP is a named constant with value 75."""
        assert SPEED_PCT_CAP == 75

    def test_speed_below_cap_not_affected(self):
        """A +50% Speed bonus (under cap) is applied without modification."""
        base = 40 * STAT_SCALE
        mods = [make_pct_mod(Stat.Speed, Operation.PCT_ADD, 50)]
        result = calculate_stat(base, mods, Stat.Speed)
        expected = base * (100 + 50) // 100
        assert result == expected

    def test_other_stats_uncapped(self):
        """Power at +200% is NOT capped (cap only applies to Speed)."""
        base = 20 * STAT_SCALE
        mods = [
            make_pct_mod(Stat.Power, Operation.PCT_ADD, 100),
            make_pct_mod(Stat.Power, Operation.PCT_ADD, 100),
        ]
        result = calculate_stat(base, mods, Stat.Power)
        expected = base * (100 + 200) // 100
        assert result == expected
