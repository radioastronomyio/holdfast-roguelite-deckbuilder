"""Tests for _pick_greedy_upgrade randomization (M3d Task 5.3)."""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.modifier import Modifier, STAT_SCALE
from models.card import UpgradeEntry
from models.enums import Stat, Operation, Target, Stacking
from agents.heuristics import _pick_greedy_upgrade


def make_upgrade_entry(tier, stat=Stat.Power, value=10):
    mod = Modifier(
        stat=stat, operation=Operation.PCT_ADD, value=value,
        duration=-1, target=Target.SELF, stacking=Stacking.replace, tags=[],
    )
    return UpgradeEntry(added_effects=[mod], prerequisite=None, tier=tier, exclusions=[])


class TestUpgradePicker:
    def test_upgrade_picker_deterministic_without_rng(self):
        """Without rng, _pick_greedy_upgrade always returns the same (first) tied candidate."""
        trees = {
            "card_a": {"1A": make_upgrade_entry(tier=1), "1B": make_upgrade_entry(tier=1)},
        }
        result1 = _pick_greedy_upgrade(["card_a"], trees, {})
        result2 = _pick_greedy_upgrade(["card_a"], trees, {})
        assert result1 == result2, "Without rng, same input should always return same result"
        assert result1 is not None

    def test_upgrade_picker_randomizes_ties(self):
        """With rng, tied candidates are chosen randomly — different seeds produce different picks."""
        trees = {
            "card_a": {
                "1A": make_upgrade_entry(tier=1, stat=Stat.Power),
                "1B": make_upgrade_entry(tier=1, stat=Stat.Power),
                "1C": make_upgrade_entry(tier=1, stat=Stat.Power),
            },
        }
        results = set()
        for seed in range(20):
            rng = random.Random(seed)
            pick = _pick_greedy_upgrade(["card_a"], trees, {}, rng=rng)
            assert pick is not None
            results.add(pick[1])  # branch key

        # With 3 tied branches and 20 different seeds, we expect at least 2 distinct picks
        assert len(results) >= 2, (
            f"Expected randomization across tied branches, got only: {results}"
        )

    def test_upgrade_picker_same_seed_same_result(self):
        """Same RNG seed always produces the same pick (determinism)."""
        trees = {
            "card_a": {"1A": make_upgrade_entry(tier=1), "1B": make_upgrade_entry(tier=1)},
            "card_b": {"1A": make_upgrade_entry(tier=1), "1B": make_upgrade_entry(tier=1)},
        }
        rng1 = random.Random(42)
        rng2 = random.Random(42)
        result1 = _pick_greedy_upgrade(["card_a", "card_b"], trees, {}, rng=rng1)
        result2 = _pick_greedy_upgrade(["card_a", "card_b"], trees, {}, rng=rng2)
        assert result1 == result2, f"Same seed should produce same pick: {result1} vs {result2}"

    def test_upgrade_picker_respects_prerequisites(self):
        """Branches with unmet prerequisites are excluded from candidates."""
        trees = {
            "card_a": {
                "1A": make_upgrade_entry(tier=1),
                "2A": UpgradeEntry(
                    added_effects=[],
                    prerequisite="1A",
                    tier=2,
                    exclusions=[],
                ),
            },
        }
        # Without 1A applied, 2A should not be available
        result = _pick_greedy_upgrade(["card_a"], trees, {})
        assert result is not None
        assert result[1] == "1A", f"Expected 1A (no prereq), got {result[1]}"

    def test_upgrade_picker_returns_none_when_all_applied(self):
        """Returns None when all available upgrades are already applied."""
        trees = {
            "card_a": {"1A": make_upgrade_entry(tier=1)},
        }
        applied = {"card_a": ["1A"]}
        result = _pick_greedy_upgrade(["card_a"], trees, applied)
        assert result is None
