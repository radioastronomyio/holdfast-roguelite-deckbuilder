"""Tests for character generation."""

import json
import random
from pathlib import Path

import pytest

from models.entity import Character, CharacterGenerationBounds
from models.modifier import STAT_SCALE
from models.enums import Stat, Target
from models.flavor import EpithetEntry, EpithetCondition1, EpithetCondition2, ElementStatMap
from generation.characters import (
    generate_character,
    evaluate_epithet,
    load_flavor_data,
    FlavorData,
)


@pytest.fixture
def bounds() -> CharacterGenerationBounds:
    bounds_path = Path(__file__).parent.parent.parent / "data" / "entities" / "generation-bounds.json"
    with open(bounds_path) as f:
        return CharacterGenerationBounds(**json.load(f))


@pytest.fixture
def flavor() -> FlavorData:
    return load_flavor_data(
        Path(__file__).parent.parent.parent / "mods" / "default" / "flavor"
    )


class TestCharacterGeneration:
    def test_stats_within_bounds(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """Generate 100 characters — all stats within per_stat_min/max, total within budget."""
        for seed in range(100):
            rng = random.Random(seed)
            char = generate_character(rng, bounds, flavor)

            for stat in Stat:
                display_val = char.base_stats[stat] // STAT_SCALE
                assert display_val >= bounds.per_stat_min[stat], (
                    f"seed={seed}: {stat} = {display_val} < min {bounds.per_stat_min[stat]}"
                )
                assert display_val <= bounds.per_stat_max[stat], (
                    f"seed={seed}: {stat} = {display_val} > max {bounds.per_stat_max[stat]}"
                )

            total = sum(char.base_stats[s] // STAT_SCALE for s in Stat)
            assert total >= bounds.total_budget_min, (
                f"seed={seed}: total {total} < budget_min {bounds.total_budget_min}"
            )
            assert total <= bounds.total_budget_max, (
                f"seed={seed}: total {total} > budget_max {bounds.total_budget_max}"
            )

    def test_stats_pre_scaled(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """All base_stats values are display_value * STAT_SCALE."""
        rng = random.Random(42)
        char = generate_character(rng, bounds, flavor)
        for stat in Stat:
            assert char.base_stats[stat] % STAT_SCALE == 0, (
                f"{stat} = {char.base_stats[stat]} not a multiple of {STAT_SCALE}"
            )

    def test_deterministic_same_seed(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """Same seed produces identical characters."""
        char1 = generate_character(random.Random(42), bounds, flavor)
        char2 = generate_character(random.Random(42), bounds, flavor)
        assert char1.base_stats == char2.base_stats
        assert char1.name == char2.name
        assert char1.innate_passive == char2.innate_passive

    def test_different_seeds_different_characters(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """Different seeds produce different stats."""
        char1 = generate_character(random.Random(42), bounds, flavor)
        char2 = generate_character(random.Random(99), bounds, flavor)
        assert char1.base_stats != char2.base_stats

    def test_name_contains_first_name(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """name_parts['first_name'] is from given_names pool."""
        rng = random.Random(42)
        char = generate_character(rng, bounds, flavor)
        assert char.name_parts["first_name"] in flavor.given_names

    def test_name_contains_archetype(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """name_parts['title'] is from archetypes pool."""
        rng = random.Random(42)
        char = generate_character(rng, bounds, flavor)
        assert char.name_parts["title"] in flavor.archetypes

    def test_innate_passive_permanent(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """innate_passive.duration == -1."""
        rng = random.Random(42)
        char = generate_character(rng, bounds, flavor)
        assert char.innate_passive.duration == -1

    def test_innate_passive_targets_self(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """innate_passive.target == SELF."""
        rng = random.Random(42)
        char = generate_character(rng, bounds, flavor)
        assert char.innate_passive.target == Target.SELF

    def test_character_has_valid_id(self, bounds: CharacterGenerationBounds, flavor: FlavorData):
        """id is non-empty, lowercase, underscore-separated."""
        rng = random.Random(42)
        char = generate_character(rng, bounds, flavor)
        assert char.id
        assert char.id == char.id.lower()
        assert " " not in char.id


class TestEpithetEvaluation:
    def test_type1_positive(self):
        """stats={Power: 80}, condition 'power >= 70' -> True."""
        stats = {Stat.HP: 100, Stat.Power: 80, Stat.Speed: 70, Stat.Defense: 10, Stat.Energy: 3}
        entry = EpithetEntry(
            epithet="the Strong",
            conditions=[EpithetCondition1(type=1, stat=Stat.Power, op=">=", value=70)],
            pool="default",
        )
        assert evaluate_epithet(stats, entry) is True

    def test_type1_negative(self):
        """stats={Power: 50}, condition 'power >= 70' -> False."""
        stats = {Stat.HP: 100, Stat.Power: 50, Stat.Speed: 70, Stat.Defense: 10, Stat.Energy: 3}
        entry = EpithetEntry(
            epithet="the Strong",
            conditions=[EpithetCondition1(type=1, stat=Stat.Power, op=">=", value=70)],
            pool="default",
        )
        assert evaluate_epithet(stats, entry) is False

    def test_type2_and(self):
        """stats meeting both conditions -> True."""
        stats = {Stat.HP: 100, Stat.Power: 75, Stat.Speed: 80, Stat.Defense: 10, Stat.Energy: 3}
        entry = EpithetEntry(
            epithet="the Balanced",
            conditions=[EpithetCondition2(
                type=2, stat_a=Stat.Power, op_a=">=", value_a=70,
                logic="AND",
                stat_b=Stat.Speed, op_b=">=", value_b=70,
            )],
            pool="rare",
        )
        assert evaluate_epithet(stats, entry) is True

    def test_type2_xor_one_met(self):
        """stats meeting exactly one condition -> True."""
        stats = {Stat.HP: 100, Stat.Power: 80, Stat.Speed: 70, Stat.Defense: 30, Stat.Energy: 3}
        entry = EpithetEntry(
            epithet="the Volatile",
            conditions=[EpithetCondition2(
                type=2, stat_a=Stat.Power, op_a=">=", value_a=75,
                logic="XOR",
                stat_b=Stat.Defense, op_b="<=", value_b=25,
            )],
            pool="rare",
        )
        assert evaluate_epithet(stats, entry) is True

    def test_type2_xor_both_met(self):
        """stats meeting both conditions -> False (XOR)."""
        stats = {Stat.HP: 100, Stat.Power: 80, Stat.Speed: 70, Stat.Defense: 20, Stat.Energy: 3}
        entry = EpithetEntry(
            epithet="the Volatile",
            conditions=[EpithetCondition2(
                type=2, stat_a=Stat.Power, op_a=">=", value_a=75,
                logic="XOR",
                stat_b=Stat.Defense, op_b="<=", value_b=25,
            )],
            pool="rare",
        )
        assert evaluate_epithet(stats, entry) is False
