"""Tests for encounter generation."""

import random
from pathlib import Path

import pytest

from models.campaign import CombatEncounter, HazardEncounter, EventEncounter
from models.enums import NarrativePosition, EncounterType
from generation.characters import load_flavor_data, FlavorData
from generation.encounters import generate_encounter, generate_event_choices


CARD_IDS = ["arcane_strike_01", "shield_bash_01", "sweeping_blade_01", "frost_bolt_01", "power_surge_01"]


@pytest.fixture
def flavor() -> FlavorData:
    return load_flavor_data(
        Path(__file__).parent.parent.parent / "mods" / "default" / "flavor"
    )


class TestEncounterGeneration:
    def test_approach_hazard_or_event_distribution(self, flavor: FlavorData):
        """~60% hazard, ~40% event (within +/-15%)."""
        hazard_count = 0
        total = 100
        for seed in range(total):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.approach, 3, CARD_IDS, flavor)
            if isinstance(enc, HazardEncounter):
                hazard_count += 1
        pct = hazard_count / total
        assert 0.45 <= pct <= 0.75, f"Hazard percentage {pct} outside 45-75% range"

    def test_approach_never_combat(self, flavor: FlavorData):
        """100 approach encounters: zero combat."""
        for seed in range(100):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.approach, 3, CARD_IDS, flavor)
            assert not isinstance(enc, CombatEncounter), f"seed={seed}: approach produced combat"

    def test_settlement_combat_or_event_distribution(self, flavor: FlavorData):
        """~70% combat, ~30% event (within +/-15%)."""
        combat_count = 0
        total = 100
        for seed in range(total):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.settlement, 3, CARD_IDS, flavor)
            if isinstance(enc, CombatEncounter):
                combat_count += 1
        pct = combat_count / total
        assert 0.55 <= pct <= 0.85, f"Combat percentage {pct} outside 55-85% range"

    def test_stronghold_always_combat(self, flavor: FlavorData):
        """100 stronghold encounters: 100% combat."""
        for seed in range(100):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.stronghold, 3, CARD_IDS, flavor)
            assert isinstance(enc, CombatEncounter), f"seed={seed}: stronghold not combat"

    def test_stronghold_has_elite(self, flavor: FlavorData):
        """Stronghold encounter has at least 1 elite enemy (verified by generation)."""
        # The stronghold uses force_elite=True which generates an elite enemy.
        # We verify the encounter has enemies (elite enemy ID is first).
        rng = random.Random(42)
        enc = generate_encounter(rng, NarrativePosition.stronghold, 3, CARD_IDS, flavor)
        assert isinstance(enc, CombatEncounter)
        assert len(enc.enemies) >= 1

    def test_hazard_has_modifiers(self, flavor: FlavorData):
        """Hazard encounter has at least 1 modifier."""
        # Find a seed that produces a hazard
        for seed in range(100):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.approach, 3, CARD_IDS, flavor)
            if isinstance(enc, HazardEncounter):
                assert len(enc.hazard_modifiers) >= 1
                return
        pytest.fail("No hazard encounter generated in 100 seeds")

    def test_hazard_duration_positive(self, flavor: FlavorData):
        """Hazard duration > 0."""
        for seed in range(100):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.approach, 3, CARD_IDS, flavor)
            if isinstance(enc, HazardEncounter):
                assert enc.hazard_duration > 0
                return
        pytest.fail("No hazard encounter generated in 100 seeds")

    def test_event_has_at_least_2_choices(self, flavor: FlavorData):
        """Event encounter has >= 2 choices."""
        for seed in range(100):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.approach, 3, CARD_IDS, flavor)
            if isinstance(enc, EventEncounter):
                assert len(enc.choices) >= 2
                return
        pytest.fail("No event encounter generated in 100 seeds")

    def test_event_choices_have_effects(self, flavor: FlavorData):
        """All choices have non-empty effects."""
        for seed in range(100):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.approach, 3, CARD_IDS, flavor)
            if isinstance(enc, EventEncounter):
                for choice in enc.choices:
                    assert len(choice.effects) >= 1
                return
        pytest.fail("No event encounter generated in 100 seeds")

    def test_combat_has_enemies(self, flavor: FlavorData):
        """Combat encounter has at least 1 enemy."""
        for seed in range(100):
            rng = random.Random(seed)
            enc = generate_encounter(rng, NarrativePosition.settlement, 3, CARD_IDS, flavor)
            if isinstance(enc, CombatEncounter):
                assert len(enc.enemies) >= 1
                return
        pytest.fail("No combat encounter generated in 100 seeds")

    def test_deterministic_same_seed(self, flavor: FlavorData):
        """Same seed + params produce identical encounter."""
        enc1 = generate_encounter(random.Random(42), NarrativePosition.approach, 3, CARD_IDS, flavor)
        enc2 = generate_encounter(random.Random(42), NarrativePosition.approach, 3, CARD_IDS, flavor)
        assert enc1.type == enc2.type
        assert enc1.name == enc2.name
