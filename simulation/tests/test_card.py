import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from models.card import Card, UpgradeEntry
from models.modifier import Modifier

FIXTURE_DIR = Path(__file__).parent / "fixtures"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CARDS_DIR = DATA_DIR / "cards"


class TestCardModel:
    def test_card_construction_valid(self):
        card = Card(
            id="test_card",
            name="Test Card",
            energy_cost=2,
            effects=[
                Modifier(
                    stat="HP",
                    operation="FLAT_SUB",
                    value=10,
                    duration=0,
                    target="ENEMY_SINGLE"
                )
            ],
            tags=["attack"],
            upgrade_tier=0,
            upgrade_paths={}
        )
        assert card.id == "test_card"
        assert card.energy_cost == 2

    def test_zero_energy_cost_allowed(self):
        card = Card(
            id="zero_cost",
            name="Zero Cost",
            energy_cost=0,
            effects=[Modifier(stat="Energy", operation="FLAT_ADD", value=2, duration=0, target="SELF")],
            tags=["utility"],
            upgrade_tier=0,
            upgrade_paths={}
        )
        assert card.energy_cost == 0

    def test_negative_energy_cost_rejected(self):
        with pytest.raises(ValidationError):
            Card(
                id="negative_cost",
                name="Bad Card",
                energy_cost=-1,
                effects=[Modifier(stat="HP", operation="FLAT_SUB", value=10, duration=0, target="ENEMY_SINGLE")],
                tags=["attack"],
                upgrade_tier=0,
                upgrade_paths={}
            )


class TestCardFixtures:
    def test_valid_cards_load(self):
        fixture_path = FIXTURE_DIR / "valid" / "cards.json"
        with open(fixture_path) as f:
            cards_data = json.load(f)
        for card_data in cards_data:
            card = Card(**card_data)
            assert isinstance(card, Card)

    def test_invalid_cards_reject(self):
        fixture_path = FIXTURE_DIR / "invalid" / "cards.json"
        with open(fixture_path) as f:
            cards_data = json.load(f)
        for card_data in cards_data:
            with pytest.raises(ValidationError):
                Card(**card_data)


class TestBaseCardsData:
    def test_all_base_cards_valid(self):
        base_cards_path = CARDS_DIR / "base-cards.json"
        with open(base_cards_path) as f:
            base_cards = json.load(f)
        assert len(base_cards) >= 10
        for card_data in base_cards:
            card = Card(**card_data)
            assert isinstance(card, Card)

    def test_base_cards_have_gdd_examples(self):
        base_cards_path = CARDS_DIR / "base-cards.json"
        with open(base_cards_path) as f:
            base_cards = json.load(f)
        card_names = [card["name"] for card in base_cards]
        required = ["Arcane Strike", "Immolate", "Shield Bash", "Sweeping Blade", "Phalanx", "Adrenaline", "Cleanse", "Deep Focus", "Acid Flask"]
        for r in required:
            assert r in card_names


class TestUpgradeTreesData:
    def test_all_upgrade_trees_valid(self):
        upgrade_trees_path = CARDS_DIR / "upgrade-trees.json"
        with open(upgrade_trees_path) as f:
            upgrade_trees = json.load(f)
        assert len(upgrade_trees) >= 10
        for card_id, tree in upgrade_trees.items():
            for branch_key, entry in tree.items():
                upgrade_entry = UpgradeEntry(**entry)
                assert isinstance(upgrade_entry, UpgradeEntry)

    def test_prerequisite_chains_intact(self):
        upgrade_trees_path = CARDS_DIR / "upgrade-trees.json"
        with open(upgrade_trees_path) as f:
            upgrade_trees = json.load(f)
        for card_id, tree in upgrade_trees.items():
            for branch_key, entry in tree.items():
                if entry["prerequisite"] is not None:
                    assert entry["prerequisite"] in tree

    def test_economy_vs_damage_exclusionary_rule(self):
        upgrade_trees_path = CARDS_DIR / "upgrade-trees.json"
        with open(upgrade_trees_path) as f:
            upgrade_trees = json.load(f)
        violations = []
        for card_id, tree in upgrade_trees.items():
            tier_1_keys = [k for k, v in tree.items() if v["tier"] == 1]
            # Check all pairs of tier 1 branches, not just the first two
            for i in range(len(tier_1_keys)):
                for j in range(i + 1, len(tier_1_keys)):
                    a, b = tree[tier_1_keys[i]], tree[tier_1_keys[j]]
                    a_eco = any(e["stat"] == "Energy" for e in a["added_effects"])
                    b_dmg = any(e["stat"] == "HP" and e["operation"] == "FLAT_SUB" and e["target"].startswith("ENEMY") for e in b["added_effects"])
                    a_dmg = any(e["stat"] == "HP" and e["operation"] == "FLAT_SUB" and e["target"].startswith("ENEMY") for e in a["added_effects"])
                    b_eco = any(e["stat"] == "Energy" for e in b["added_effects"])
                    if a_eco and b_dmg:
                        violations.append(f"{card_id}: {tier_1_keys[i]} (economy) vs {tier_1_keys[j]} (damage)")
                    if a_dmg and b_eco:
                        violations.append(f"{card_id}: {tier_1_keys[i]} (damage) vs {tier_1_keys[j]} (economy)")
        if violations:
            pytest.fail("Economy vs damage violations detected: " + "; ".join(violations))


class TestHazardCardsData:
    def test_all_hazard_cards_valid(self):
        hazard_cards_path = CARDS_DIR / "hazard-cards.json"
        with open(hazard_cards_path) as f:
            hazard_cards = json.load(f)
        assert len(hazard_cards) >= 5
        for card_data in hazard_cards:
            card = Card(**card_data)
            assert card.energy_cost == 0

    def test_hazard_cards_include_gdd_examples(self):
        hazard_cards_path = CARDS_DIR / "hazard-cards.json"
        with open(hazard_cards_path) as f:
            hazard_cards = json.load(f)
        hazard_names = [card["name"] for card in hazard_cards]
        assert "Tripwire" in hazard_names
        assert "Miasma" in hazard_names


class TestCardCrossValidation:
    def test_upgrade_tree_ids_match_base_cards(self):
        base_cards_path = CARDS_DIR / "base-cards.json"
        upgrade_trees_path = CARDS_DIR / "upgrade-trees.json"
        with open(base_cards_path) as f:
            base_cards = json.load(f)
        with open(upgrade_trees_path) as f:
            upgrade_trees = json.load(f)
        base_ids = {c["id"] for c in base_cards}
        upgrade_ids = set(upgrade_trees.keys())
        assert upgrade_ids == base_ids, (
            f"Mismatch: cards without trees: {base_ids - upgrade_ids}, trees without cards: {upgrade_ids - base_ids}"
        )
