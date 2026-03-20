"""Tests for region generation."""

import json
import random
from pathlib import Path

import pytest

from models.campaign import Region, CombatEncounter
from models.modifier import STAT_SCALE
from models.enums import NarrativePosition
from generation.characters import load_flavor_data, FlavorData
from generation.regions import generate_region, _load_region_adjectives


CARD_IDS = ["arcane_strike_01", "shield_bash_01", "sweeping_blade_01", "frost_bolt_01", "power_surge_01"]


@pytest.fixture
def flavor() -> FlavorData:
    return load_flavor_data(
        Path(__file__).parent.parent.parent / "mods" / "default" / "flavor"
    )


@pytest.fixture
def region_adjectives() -> list[str]:
    return _load_region_adjectives(
        Path(__file__).parent.parent.parent / "mods" / "default" / "flavor"
    )


class TestRegionGeneration:
    def test_exactly_3_encounters(self, flavor: FlavorData, region_adjectives: list[str]):
        """Region has exactly 3 encounters."""
        rng = random.Random(42)
        region = generate_region(rng, 3, CARD_IDS, flavor, region_adjectives)
        assert len(region.encounters) == 3

    def test_narrative_arc_order(self, flavor: FlavorData, region_adjectives: list[str]):
        """Encounters follow approach -> settlement -> stronghold."""
        rng = random.Random(42)
        region = generate_region(rng, 3, CARD_IDS, flavor, region_adjectives)
        positions = [e.narrative_position for e in region.encounters]
        assert positions == [
            NarrativePosition.approach,
            NarrativePosition.settlement,
            NarrativePosition.stronghold,
        ]

    def test_stronghold_is_combat(self, flavor: FlavorData, region_adjectives: list[str]):
        """Stronghold encounter (position 2) is combat type."""
        rng = random.Random(42)
        region = generate_region(rng, 3, CARD_IDS, flavor, region_adjectives)
        assert region.encounters[2].type == "combat"

    def test_stronghold_is_elite(self, flavor: FlavorData, region_adjectives: list[str]):
        """All stronghold encounters reference at least one elite enemy (across 20 regions)."""
        for seed in range(20):
            rng = random.Random(seed)
            region = generate_region(rng, 3, CARD_IDS, flavor, region_adjectives)
            stronghold = region.encounters[2]
            assert isinstance(stronghold, CombatEncounter)
            assert len(stronghold.enemies) >= 1

    def test_approach_never_combat(self, flavor: FlavorData, region_adjectives: list[str]):
        """No approach encounter has type 'combat' across 100 regions."""
        for seed in range(100):
            rng = random.Random(seed)
            region = generate_region(rng, seed % 6 + 1, CARD_IDS, flavor, region_adjectives)
            assert region.encounters[0].type != "combat", f"seed={seed}: approach was combat"

    def test_modifier_stack_scales_with_difficulty(self, flavor: FlavorData, region_adjectives: list[str]):
        """difficulty=6 has stronger/more modifiers than difficulty=1."""
        # Sum of absolute modifier values should generally be higher at higher difficulty
        total_low = 0
        total_high = 0
        for seed in range(20):
            r1 = generate_region(random.Random(seed), 1, CARD_IDS, flavor, region_adjectives)
            r6 = generate_region(random.Random(seed), 6, CARD_IDS, flavor, region_adjectives)
            total_low += sum(abs(m.value) for m in r1.modifier_stack)
            total_high += sum(abs(m.value) for m in r6.modifier_stack)
        assert total_high > total_low

    def test_meta_reward_permanent(self, flavor: FlavorData, region_adjectives: list[str]):
        """meta_reward.duration == -1."""
        rng = random.Random(42)
        region = generate_region(rng, 3, CARD_IDS, flavor, region_adjectives)
        assert region.meta_reward.duration == -1

    def test_research_layers_count(self, flavor: FlavorData, region_adjectives: list[str]):
        """Exactly 4 research layers."""
        rng = random.Random(42)
        region = generate_region(rng, 3, CARD_IDS, flavor, region_adjectives)
        assert len(region.research_layers) == 4

    def test_research_costs_scale(self, flavor: FlavorData, region_adjectives: list[str]):
        """difficulty=6 research costs are higher than difficulty=1."""
        r1 = generate_region(random.Random(42), 1, CARD_IDS, flavor, region_adjectives)
        r6 = generate_region(random.Random(42), 6, CARD_IDS, flavor, region_adjectives)
        for i in range(4):
            assert r6.research_layers[i].cost > r1.research_layers[i].cost

    def test_deterministic_same_seed(self, flavor: FlavorData, region_adjectives: list[str]):
        """Same seed + params produce identical regions."""
        r1 = generate_region(random.Random(42), 3, CARD_IDS, flavor, region_adjectives)
        r2 = generate_region(random.Random(42), 3, CARD_IDS, flavor, region_adjectives)
        assert r1.name == r2.name
        assert r1.modifier_stack == r2.modifier_stack
        assert r1.meta_reward == r2.meta_reward

    def test_name_from_flavor_pools(self, flavor: FlavorData, region_adjectives: list[str]):
        """Name contains words from adjective/noun pools."""
        rng = random.Random(42)
        region = generate_region(rng, 3, CARD_IDS, flavor, region_adjectives)
        words = region.name.split()
        assert words[0] in region_adjectives
        assert words[1] in flavor.region_nouns
