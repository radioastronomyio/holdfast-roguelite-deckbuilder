import json
import pytest
from pathlib import Path

from models.flavor import (
    EpithetCondition1,
    EpithetCondition2,
    EpithetEntry,
    ElementStatMap,
    FlavorPools,
)
from models.enums import Stat

FIXTURE_DIR = Path(__file__).parent / "fixtures"
MODS_DIR = Path(__file__).parent.parent.parent / "mods"
FLAVOR_DIR = MODS_DIR / "default" / "flavor"


class TestFlavorDataFiles:
    def test_given_names_minimum_count(self):
        with open(FLAVOR_DIR / "given_names.json") as f:
            names = json.load(f)
        assert len(names) >= 60, (
            f"given_names.json must have at least 60 entries, got {len(names)}"
        )

    def test_archetypes_minimum_count(self):
        with open(FLAVOR_DIR / "archetypes.json") as f:
            archetypes = json.load(f)
        assert len(archetypes) >= 20, (
            f"archetypes.json must have at least 20 entries, got {len(archetypes)}"
        )

    def test_action_verbs_minimum_count(self):
        with open(FLAVOR_DIR / "action_verbs.json") as f:
            verbs = json.load(f)
        assert len(verbs) >= 30, (
            f"action_verbs.json must have at least 30 entries, got {len(verbs)}"
        )

    def test_region_adjectives_minimum_count(self):
        with open(FLAVOR_DIR / "region_adjectives.json") as f:
            adjectives = json.load(f)
        assert len(adjectives) >= 30, (
            f"region_adjectives.json must have at least 30 entries, got {len(adjectives)}"
        )

    def test_region_nouns_minimum_count(self):
        with open(FLAVOR_DIR / "region_nouns.json") as f:
            nouns = json.load(f)
        assert len(nouns) >= 30, (
            f"region_nouns.json must have at least 30 entries, got {len(nouns)}"
        )

    def test_epithet_conditions_minimum_count(self):
        with open(FLAVOR_DIR / "epithet-conditions.json") as f:
            epithets = json.load(f)
        assert len(epithets) >= 20, (
            f"epithet-conditions.json must have at least 20 entries, got {len(epithets)}"
        )


class TestElementStatMap:
    def test_element_stat_map_valid(self):
        with open(FLAVOR_DIR / "element-stat-map.json") as f:
            map_data = json.load(f)
        element_map = ElementStatMap(**map_data)
        assert isinstance(element_map, ElementStatMap)

    def test_all_stats_present(self):
        with open(FLAVOR_DIR / "element-stat-map.json") as f:
            map_data = json.load(f)
        required_stats = {"power", "speed", "defense", "energy", "hp"}
        assert set(map_data.keys()) == required_stats

    def test_each_stat_has_default_and_rare(self):
        with open(FLAVOR_DIR / "element-stat-map.json") as f:
            map_data = json.load(f)
        for stat, pools in map_data.items():
            assert "default" in pools, f"{stat} missing 'default' pool"
            assert "rare" in pools, f"{stat} missing 'rare' pool"


class TestEpithetConditions:
    def test_all_epithet_conditions_valid(self):
        with open(FLAVOR_DIR / "epithet-conditions.json") as f:
            epithets = json.load(f)
        for epithet_data in epithets:
            epithet = EpithetEntry(**epithet_data)
            assert isinstance(epithet, EpithetEntry)

    def test_gdd_examples_present(self):
        with open(FLAVOR_DIR / "epithet-conditions.json") as f:
            epithets = json.load(f)
        epithet_names = [e["epithet"] for e in epithets]
        required = ["the Strong", "the Swift", "the Ghost", "the Volatile"]
        for r in required:
            assert r in epithet_names, f"Missing GDD epithet: {r}"

    def test_all_stats_covered(self):
        with open(FLAVOR_DIR / "epithet-conditions.json") as f:
            epithets = json.load(f)
        covered_stats = set()
        for epithet_data in epithets:
            for cond in epithet_data["conditions"]:
                if cond["type"] == 1:
                    covered_stats.add(cond["stat"])
                elif cond["type"] == 2:
                    covered_stats.add(cond["stat_a"])
                    covered_stats.add(cond["stat_b"])
        required_stats = {"HP", "Power", "Speed", "Defense", "Energy"}
        assert covered_stats == required_stats, (
            f"Not all stats covered: {covered_stats}"
        )

    def test_type_1_condition_valid(self):
        cond = EpithetCondition1(type=1, stat="Power", op=">=", value=70)
        assert cond.type == 1
        assert cond.stat == Stat.Power

    def test_type_2_condition_valid(self):
        cond = EpithetCondition2(
            type=2,
            stat_a="Power",
            op_a=">=",
            value_a=75,
            logic="XOR",
            stat_b="Defense",
            op_b="<=",
            value_b=25,
        )
        assert cond.type == 2
        assert cond.logic == "XOR"

    def test_invalid_operator_rejected(self):
        with pytest.raises(ValueError):
            EpithetCondition1(type=1, stat="Power", op="invalid", value=70)

    def test_invalid_logic_rejected(self):
        with pytest.raises(ValueError):
            EpithetCondition2(
                type=2,
                stat_a="Power",
                op_a=">=",
                value_a=75,
                logic="INVALID",
                stat_b="Defense",
                op_b="<=",
                value_b=25,
            )


class TestFlavorPools:
    def test_flavor_pools_valid(self):
        pools_data = {
            "given_names": ["Mira", "Kael", "Dusk"],
            "archetypes": ["Mage", "Blade", "Warden"],
            "action_verbs": ["Surge", "Lash", "Strike"],
            "region_adjectives": ["Ashen", "Blighted", "Volcanic"],
            "region_nouns": ["Wastes", "Plains", "Reach"],
        }
        pools = FlavorPools(**pools_data)
        assert isinstance(pools, FlavorPools)
        assert len(pools.given_names) == 3
        assert len(pools.archetypes) == 3
