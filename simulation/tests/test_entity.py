import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from models.entity import Character, Enemy, CharacterGenerationBounds
from models.enums import Stat

FIXTURE_DIR = Path(__file__).parent / "fixtures"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
ENTITIES_DIR = DATA_DIR / "entities"


class TestCharacterGenerationBounds:
    def test_bounds_construction_valid(self):
        bounds = CharacterGenerationBounds(
            per_stat_min={"HP": 50, "Power": 8, "Speed": 60, "Defense": 3, "Energy": 2},
            per_stat_max={
                "HP": 150,
                "Power": 35,
                "Speed": 130,
                "Defense": 25,
                "Energy": 7,
            },
            total_budget_min=150,
            total_budget_max=350,
        )
        assert bounds.total_budget_min == 150
        assert bounds.total_budget_max == 350

    def test_all_stats_required(self):
        with pytest.raises(ValidationError):
            CharacterGenerationBounds(
                per_stat_min={"HP": 50, "Power": 8, "Speed": 60, "Defense": 3},
                per_stat_max={
                    "HP": 150,
                    "Power": 35,
                    "Speed": 130,
                    "Defense": 25,
                    "Energy": 7,
                },
                total_budget_min=150,
                total_budget_max=350,
            )


class TestCharacterModel:
    def test_character_construction_valid(self):
        character = Character(
            id="test_char",
            name="Test Character",
            base_stats={
                "HP": 100000,
                "Power": 15000,
                "Speed": 90000,
                "Defense": 10000,
                "Energy": 4000,
            },
            innate_passive={
                "stat": "Power",
                "operation": "PCT_ADD",
                "value": 10,
                "duration": -1,
                "target": "SELF",
                "stacking": "stack",
                "tags": ["passive"],
            },
            name_parts={"first_name": "Kael", "title": "Blade", "origin": "Forest"},
        )
        assert character.id == "test_char"
        assert character.innate_passive.duration == -1

    def test_all_stats_required(self):
        with pytest.raises(ValidationError):
            Character(
                id="test_char",
                name="Test Character",
                base_stats={
                    "HP": 100000,
                    "Power": 15000,
                    "Speed": 90000,
                    "Defense": 10000,
                },
                innate_passive={
                    "stat": "Power",
                    "operation": "PCT_ADD",
                    "value": 10,
                    "duration": -1,
                    "target": "SELF",
                    "stacking": "stack",
                    "tags": ["passive"],
                },
                name_parts={"first_name": "Kael", "title": "Blade", "origin": "Forest"},
            )

    def test_passive_must_be_permanent(self):
        with pytest.raises(ValidationError):
            Character(
                id="test_char",
                name="Test Character",
                base_stats={
                    "HP": 100000,
                    "Power": 15000,
                    "Speed": 90000,
                    "Defense": 10000,
                    "Energy": 4000,
                },
                innate_passive={
                    "stat": "Power",
                    "operation": "PCT_ADD",
                    "value": 10,
                    "duration": 3,
                    "target": "SELF",
                    "stacking": "stack",
                    "tags": ["passive"],
                },
                name_parts={"first_name": "Kael", "title": "Blade", "origin": "Forest"},
            )


class TestEnemyModel:
    def test_enemy_construction_valid(self):
        enemy = Enemy(
            id="test_enemy",
            name="Test Enemy",
            base_stats={
                "HP": 50000,
                "Power": 10000,
                "Speed": 60000,
                "Defense": 5000,
                "Energy": 3000,
            },
            card_pool=["arcane_strike_01"],
            ai_heuristic_tag="aggressive",
            is_elite=False,
        )
        assert enemy.id == "test_enemy"
        assert enemy.ai_heuristic_tag == "aggressive"

    def test_card_pool_non_empty(self):
        with pytest.raises(ValidationError):
            Enemy(
                id="test_enemy",
                name="Test Enemy",
                base_stats={
                    "HP": 50000,
                    "Power": 10000,
                    "Speed": 60000,
                    "Defense": 5000,
                    "Energy": 3000,
                },
                card_pool=[],
                ai_heuristic_tag="aggressive",
            )

    def test_all_stats_required(self):
        with pytest.raises(ValidationError):
            Enemy(
                id="test_enemy",
                name="Test Enemy",
                base_stats={
                    "HP": 50000,
                    "Power": 10000,
                    "Speed": 60000,
                    "Defense": 5000,
                },
                card_pool=["arcane_strike_01"],
                ai_heuristic_tag="aggressive",
            )

    def test_invalid_ai_heuristic_tag(self):
        with pytest.raises(ValidationError):
            Enemy(
                id="test_enemy",
                name="Test Enemy",
                base_stats={
                    "HP": 50000,
                    "Power": 10000,
                    "Speed": 60000,
                    "Defense": 5000,
                    "Energy": 3000,
                },
                card_pool=["arcane_strike_01"],
                ai_heuristic_tag="passive",
            )


class TestCharacterFixtures:
    def test_valid_characters_load(self):
        fixture_path = FIXTURE_DIR / "valid" / "characters.json"
        with open(fixture_path) as f:
            characters_data = json.load(f)
        for character_data in characters_data:
            character = Character(**character_data)
            assert isinstance(character, Character)

    def test_invalid_characters_reject(self):
        fixture_path = FIXTURE_DIR / "invalid" / "characters.json"
        with open(fixture_path) as f:
            characters_data = json.load(f)
        for character_data in characters_data:
            data_without_comment = {
                k: v for k, v in character_data.items() if k != "comment"
            }
            with pytest.raises(ValidationError):
                Character(**data_without_comment)


class TestEnemyFixtures:
    def test_valid_enemies_load(self):
        fixture_path = FIXTURE_DIR / "valid" / "enemies.json"
        with open(fixture_path) as f:
            enemies_data = json.load(f)
        for enemy_data in enemies_data:
            enemy = Enemy(**enemy_data)
            assert isinstance(enemy, Enemy)

    def test_invalid_enemies_reject(self):
        fixture_path = FIXTURE_DIR / "invalid" / "enemies.json"
        with open(fixture_path) as f:
            enemies_data = json.load(f)
        for enemy_data in enemies_data:
            data_without_comment = {
                k: v for k, v in enemy_data.items() if k != "comment"
            }
            with pytest.raises(ValidationError):
                Enemy(**data_without_comment)


class TestExampleCharactersData:
    def test_all_example_characters_valid(self):
        example_characters_path = ENTITIES_DIR / "example-characters.json"
        with open(example_characters_path) as f:
            example_characters = json.load(f)
        for character_data in example_characters:
            character = Character(**character_data)
            assert isinstance(character, Character)

    def test_gdd_characters_present(self):
        example_characters_path = ENTITIES_DIR / "example-characters.json"
        with open(example_characters_path) as f:
            example_characters = json.load(f)
        character_names = [c["name"] for c in example_characters]
        required = ["Vanguard Sentinel", "Ember Mage", "Field Tactician"]
        for r in required:
            assert r in character_names

    def test_gdd_characters_have_correct_stats(self):
        example_characters_path = ENTITIES_DIR / "example-characters.json"
        with open(example_characters_path) as f:
            example_characters = json.load(f)

        vanguard = next(
            c for c in example_characters if c["name"] == "Vanguard Sentinel"
        )
        assert vanguard["base_stats"]["HP"] == 140000
        assert vanguard["base_stats"]["Power"] == 12000
        assert vanguard["base_stats"]["Speed"] == 80000
        assert vanguard["base_stats"]["Defense"] == 20000
        assert vanguard["base_stats"]["Energy"] == 3000

        ember_mage = next(c for c in example_characters if c["name"] == "Ember Mage")
        assert ember_mage["base_stats"]["HP"] == 65000
        assert ember_mage["base_stats"]["Power"] == 28000
        assert ember_mage["base_stats"]["Speed"] == 115000

    def test_ember_mage_has_conditional_tag(self):
        example_characters_path = ENTITIES_DIR / "example-characters.json"
        with open(example_characters_path) as f:
            example_characters = json.load(f)
        ember_mage = next(c for c in example_characters if c["name"] == "Ember Mage")
        assert "conditional_hp_threshold_50" in ember_mage["innate_passive"]["tags"]


class TestExampleEnemiesData:
    def test_all_example_enemies_valid(self):
        example_enemies_path = ENTITIES_DIR / "example-enemies.json"
        with open(example_enemies_path) as f:
            example_enemies = json.load(f)
        for enemy_data in example_enemies:
            enemy = Enemy(**enemy_data)
            assert isinstance(enemy, Enemy)

    def test_gdd_enemies_present(self):
        example_enemies_path = ENTITIES_DIR / "example-enemies.json"
        with open(example_enemies_path) as f:
            example_enemies = json.load(f)
        enemy_names = [e["name"] for e in example_enemies]
        assert "Scavenger Patrol" in enemy_names
        assert "Warlord Vanguard" in enemy_names
        assert "Fungal Behemoth" in enemy_names


class TestGenerationBoundsData:
    def test_generation_bounds_valid(self):
        bounds_path = ENTITIES_DIR / "generation-bounds.json"
        with open(bounds_path) as f:
            bounds_data = json.load(f)
        bounds = CharacterGenerationBounds(**bounds_data)
        assert isinstance(bounds, CharacterGenerationBounds)

    def test_gdd_examples_within_bounds(self):
        bounds_path = ENTITIES_DIR / "generation-bounds.json"
        example_characters_path = ENTITIES_DIR / "example-characters.json"

        with open(bounds_path) as f:
            bounds_data = json.load(f)
        bounds = CharacterGenerationBounds(**bounds_data)

        with open(example_characters_path) as f:
            example_characters = json.load(f)

        for character_data in example_characters:
            for stat, value in character_data["base_stats"].items():
                unscaled_value = value // 1000
                assert (
                    bounds.per_stat_min[stat]
                    <= unscaled_value
                    <= bounds.per_stat_max[stat]
                ), (
                    f"Character {character_data['name']} stat {stat}={unscaled_value} outside bounds"
                )

            total = sum(v // 1000 for v in character_data["base_stats"].values())
            assert bounds.total_budget_min <= total <= bounds.total_budget_max, (
                f"Character {character_data['name']} total={total} outside budget bounds"
            )
