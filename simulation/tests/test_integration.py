import json
import pytest
from pathlib import Path

from models.card import Card, UpgradeEntry
from models.entity import Character, Enemy, CharacterGenerationBounds
from models.campaign import Region, WorldCard, OutpostUpgrade
from models.flavor import EpithetEntry, ElementStatMap

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ENTITIES_DIR = DATA_DIR / "entities"
CARDS_DIR = DATA_DIR / "cards"
CAMPAIGN_DIR = DATA_DIR / "campaign"
MODS_DIR = Path(__file__).parent.parent.parent / "mods"
FLAVOR_DIR = MODS_DIR / "default" / "flavor"


class TestIntegrationLoadAllDataFiles:
    def test_all_entity_files_load(self):
        with open(ENTITIES_DIR / "example-characters.json") as f:
            characters = json.load(f)
        for char_data in characters:
            Character(**char_data)

        with open(ENTITIES_DIR / "example-enemies.json") as f:
            enemies = json.load(f)
        for enemy_data in enemies:
            Enemy(**enemy_data)

        with open(ENTITIES_DIR / "generation-bounds.json") as f:
            bounds = CharacterGenerationBounds(**json.load(f))
            assert isinstance(bounds, CharacterGenerationBounds)

    def test_all_card_files_load(self):
        with open(CARDS_DIR / "base-cards.json") as f:
            cards = json.load(f)
        for card_data in cards:
            Card(**card_data)

        with open(CARDS_DIR / "upgrade-trees.json") as f:
            trees = json.load(f)
        for card_id, tree in trees.items():
            for branch_key, entry in tree.items():
                UpgradeEntry(**entry)

        with open(CARDS_DIR / "hazard-cards.json") as f:
            hazards = json.load(f)
        for card_data in hazards:
            Card(**card_data)

    def test_all_campaign_files_load(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        for region_data in regions:
            Region(**region_data)

        with open(CAMPAIGN_DIR / "world-deck.json") as f:
            world_cards = json.load(f)
        for card_data in world_cards:
            WorldCard(**card_data)

        with open(CAMPAIGN_DIR / "outpost-upgrades.json") as f:
            upgrades = json.load(f)
        for upgrade_data in upgrades:
            OutpostUpgrade(**upgrade_data)

    def test_all_flavor_files_load(self):
        with open(FLAVOR_DIR / "epithet-conditions.json") as f:
            epithets = json.load(f)
        for epithet_data in epithets:
            EpithetEntry(**epithet_data)

        with open(FLAVOR_DIR / "element-stat-map.json") as f:
            ElementStatMap(**json.load(f))


class TestCrossReferenceIntegrity:
    def test_enemy_card_pool_references_exist(self):
        with open(ENTITIES_DIR / "example-enemies.json") as f:
            enemies = json.load(f)
        with open(CARDS_DIR / "base-cards.json") as f:
            base_cards = json.load(f)
        card_ids = {c["id"] for c in base_cards}

        for enemy in enemies:
            for card_id in enemy["card_pool"]:
                assert card_id in card_ids, (
                    f"Enemy {enemy['name']} references non-existent card {card_id}"
                )

    def test_upgrade_tree_prerequisite_chains_valid(self):
        with open(CARDS_DIR / "upgrade-trees.json") as f:
            trees = json.load(f)

        for card_id, tree in trees.items():
            for branch_key, entry in tree.items():
                if entry["prerequisite"] is not None:
                    assert entry["prerequisite"] in tree, (
                        f"Card {card_id} branch {branch_key} has invalid prerequisite {entry['prerequisite']}"
                    )

    def test_region_encounter_enemy_references_exist(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        with open(ENTITIES_DIR / "example-enemies.json") as f:
            enemies = json.load(f)
        enemy_ids = {e["id"] for e in enemies}

        for region in regions:
            for encounter in region["encounters"]:
                if encounter["type"] == "combat":
                    for enemy_id in encounter["enemies"]:
                        assert enemy_id in enemy_ids, (
                            f"Region {region['name']} encounter references non-existent enemy {enemy_id}"
                        )


class TestFullIntegration:
    def test_all_data_files_validated(self):
        test = TestIntegrationLoadAllDataFiles()
        test.test_all_entity_files_load()
        test.test_all_card_files_load()
        test.test_all_campaign_files_load()
        test.test_all_flavor_files_load()

    def test_all_cross_references_valid(self):
        test = TestCrossReferenceIntegrity()
        test.test_enemy_card_pool_references_exist()
        test.test_upgrade_tree_prerequisite_chains_valid()
        test.test_region_encounter_enemy_references_exist()
