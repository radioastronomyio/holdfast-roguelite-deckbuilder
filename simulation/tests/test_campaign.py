import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from models.campaign import (
    CombatEncounter,
    HazardEncounter,
    EventEncounter,
    Region,
    WorldCard,
    OutpostUpgrade,
)
from models.enums import NarrativePosition

FIXTURE_DIR = Path(__file__).parent / "fixtures"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CAMPAIGN_DIR = DATA_DIR / "campaign"


class TestCampaignDataFiles:
    def test_example_regions_valid(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        for region_data in regions:
            region = Region(**region_data)
            assert isinstance(region, Region)

    def test_gdd_regions_present(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        region_names = [r["name"] for r in regions]
        assert "The Ashen Wastes" in region_names
        assert "Whispering Thicket" in region_names

    def test_world_deck_valid(self):
        with open(CAMPAIGN_DIR / "world-deck.json") as f:
            world_cards = json.load(f)
        for card_data in world_cards:
            card = WorldCard(**card_data)
            assert isinstance(card, WorldCard)

    def test_all_20_gdd_world_cards_present(self):
        with open(CAMPAIGN_DIR / "world-deck.json") as f:
            world_cards = json.load(f)
        card_names = [c["name"] for c in world_cards]
        required = [
            "Forced March",
            "Rations Cut",
            "Reckless Assault",
            "Heavy Armor",
            "Blood Magic",
            "Fog of War",
            "Overclocked",
            "Vampiric Contract",
            "Scavenger's Greed",
            "Hyper-Metabolism",
            "Glass Cannon",
            "Pacifism Protocol",
            "Leyline Tap",
            "Tunnel Vision",
            "Unstable Mutagen",
            "Barricaded",
            "Cursed Relic",
            "Martyrdom",
            "Temporal Shift",
            "Echo Chamber",
        ]
        for r in required:
            assert r in card_names, f"Missing GDD world card: {r}"

    def test_outpost_upgrades_valid(self):
        with open(CAMPAIGN_DIR / "outpost-upgrades.json") as f:
            upgrades = json.load(f)
        for upgrade_data in upgrades:
            upgrade = OutpostUpgrade(**upgrade_data)
            assert isinstance(upgrade, OutpostUpgrade)

    def test_gdd_upgrades_present(self):
        with open(CAMPAIGN_DIR / "outpost-upgrades.json") as f:
            upgrades = json.load(f)
        upgrade_names = [u["name"] for u in upgrades]
        required = ["Forge", "Watchtower", "Infirmary", "War Room", "Library"]
        for r in required:
            assert r in upgrade_names, f"Missing GDD outpost upgrade: {r}"


class TestRegionConstraints:
    def test_exactly_three_encounters(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        for region_data in regions:
            assert len(region_data["encounters"]) == 3

    def test_narrative_positions_valid(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        for region_data in regions:
            positions = [e["narrative_position"] for e in region_data["encounters"]]
            expected = ["approach", "settlement", "stronghold"]
            assert positions == expected

    def test_stronghold_must_be_combat(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        for region_data in regions:
            assert region_data["encounters"][2]["type"] == "combat"

    def test_exactly_four_research_layers(self):
        with open(CAMPAIGN_DIR / "example-regions.json") as f:
            regions = json.load(f)
        for region_data in regions:
            assert len(region_data["research_layers"]) == 4


class TestWorldCardConstraints:
    def test_upside_non_empty(self):
        with open(CAMPAIGN_DIR / "world-deck.json") as f:
            world_cards = json.load(f)
        for card_data in world_cards:
            assert len(card_data["upside"]) > 0

    def test_downside_non_empty(self):
        with open(CAMPAIGN_DIR / "world-deck.json") as f:
            world_cards = json.load(f)
        for card_data in world_cards:
            assert len(card_data["downside"]) > 0


class TestOutpostUpgradeConstraints:
    def test_all_effects_permanent(self):
        with open(CAMPAIGN_DIR / "outpost-upgrades.json") as f:
            upgrades = json.load(f)
        for upgrade_data in upgrades:
            for effect in upgrade_data.get("effects", []):
                assert effect["duration"] == -1


class TestEncounterTypes:
    def test_combat_encounter_valid(self):
        combat = CombatEncounter(
            type="combat",
            narrative_position="stronghold",
            name="Boss Fight",
            description="A tough boss",
            enemies=["warlord_vanguard"],
            enemy_cards=["arcane_strike_01"],
        )
        assert combat.type == "combat"

    def test_hazard_encounter_valid(self):
        hazard = HazardEncounter(
            type="hazard",
            narrative_position="approach",
            name="Ash Storm",
            description="Hot ash swirls",
            hazard_modifiers=[
                {
                    "stat": "Speed",
                    "operation": "PCT_SUB",
                    "value": 15,
                    "duration": -1,
                    "target": "ALLY_ALL",
                }
            ],
            hazard_duration=3,
        )
        assert hazard.type == "hazard"

    def test_event_encounter_valid(self):
        event = EventEncounter(
            type="event",
            narrative_position="settlement",
            name="Merchant",
            description="A traveling merchant",
            choices=[
                {"description": "Buy", "effects": [], "cost": []},
                {"description": "Leave", "effects": [], "cost": []},
            ],
        )
        assert event.type == "event"
        assert len(event.choices) >= 2


class TestRegionValidation:
    def test_region_with_invalid_encounter_count_rejected(self):
        with pytest.raises(ValidationError):
            Region(
                id="test",
                name="Test Region",
                region_type="Test",
                modifier_stack=[],
                encounters=[],
                meta_reward={
                    "stat": "Power",
                    "operation": "FLAT_ADD",
                    "value": 1000,
                    "duration": -1,
                    "target": "SELF",
                },
                research_layers=[],
            )

    def test_region_with_non_combat_stronghold_rejected(self):
        with pytest.raises(ValidationError):
            Region(
                id="test",
                name="Test Region",
                region_type="Test",
                modifier_stack=[],
                encounters=[
                    {
                        "type": "combat",
                        "narrative_position": "approach",
                        "name": "E1",
                        "description": "D1",
                        "enemies": ["e1"],
                        "enemy_cards": [],
                    },
                    {
                        "type": "combat",
                        "narrative_position": "settlement",
                        "name": "E2",
                        "description": "D2",
                        "enemies": ["e1"],
                        "enemy_cards": [],
                    },
                    {
                        "type": "hazard",
                        "narrative_position": "stronghold",
                        "name": "E3",
                        "description": "D3",
                        "hazard_modifiers": [],
                        "hazard_duration": 3,
                    },
                ],
                meta_reward={
                    "stat": "Power",
                    "operation": "FLAT_ADD",
                    "value": 1000,
                    "duration": -1,
                    "target": "SELF",
                },
                research_layers=[],
            )

    def test_world_card_with_empty_upside_rejected(self):
        with pytest.raises(ValidationError):
            WorldCard(
                id="test",
                name="Test Card",
                upside=[],
                downside=[
                    {
                        "stat": "HP",
                        "operation": "PCT_SUB",
                        "value": 10,
                        "duration": -1,
                        "target": "SELF",
                    }
                ],
                description="Test",
            )

    def test_outpost_upgrade_with_non_permanent_effect_rejected(self):
        with pytest.raises(ValidationError):
            OutpostUpgrade(
                id="test",
                name="Test Upgrade",
                description="Test",
                effects=[
                    {
                        "stat": "Power",
                        "operation": "FLAT_ADD",
                        "value": 1000,
                        "duration": 3,
                        "target": "SELF",
                    }
                ],
                cost=50,
            )
