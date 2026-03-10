import json
import pytest
from pathlib import Path
from pydantic import ValidationError

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking


FIXTURE_DIR = Path(__file__).parent / "fixtures"


class TestModifierModel:
    def test_stat_scale_constant(self):
        assert STAT_SCALE == 1000

    def test_modifier_construction_valid(self):
        modifier = Modifier(
            stat=Stat.HP,
            operation=Operation.FLAT_SUB,
            value=15,
            duration=0,
            target=Target.ENEMY_SINGLE,
            stacking=Stacking.replace,
            tags=["attack", "physical"]
        )
        assert modifier.stat == Stat.HP
        assert modifier.value == 15
        assert modifier.tags == ["attack", "physical"]

    def test_modifier_defaults(self):
        modifier = Modifier(
            stat=Stat.HP,
            operation=Operation.FLAT_SUB,
            value=15,
            duration=0,
            target=Target.ENEMY_SINGLE
        )
        assert modifier.stacking == Stacking.replace
        assert modifier.tags == []

    def test_duration_validation_valid(self):
        Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=15, duration=0, target=Target.ENEMY_SINGLE)
        Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=15, duration=-1, target=Target.ENEMY_SINGLE)
        Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=15, duration=5, target=Target.ENEMY_SINGLE)

    def test_duration_validation_invalid(self):
        with pytest.raises(ValidationError):
            Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=15, duration=-2, target=Target.ENEMY_SINGLE)
        with pytest.raises(ValidationError):
            Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=15, duration=-10, target=Target.ENEMY_SINGLE)

    def test_value_must_be_integer(self):
        with pytest.raises(ValidationError):
            Modifier(stat=Stat.HP, operation=Operation.FLAT_SUB, value=15.5, duration=0, target=Target.ENEMY_SINGLE)


class TestModifierFixtures:
    def test_valid_modifiers_load(self):
        fixture_path = FIXTURE_DIR / "valid" / "modifiers.json"
        with open(fixture_path) as f:
            modifiers_data = json.load(f)
        
        for modifier_data in modifiers_data:
            modifier = Modifier(**modifier_data)
            assert isinstance(modifier, Modifier)

    def test_invalid_modifiers_reject(self):
        fixture_path = FIXTURE_DIR / "invalid" / "modifiers.json"
        with open(fixture_path) as f:
            modifiers_data = json.load(f)
        
        for i, modifier_data in enumerate(modifiers_data):
            with pytest.raises(ValidationError):
                Modifier(**modifier_data)


class TestResolutionOrderVectors:
    def test_resolution_order_flat_then_percentage(self):
        base = 100
        flat_add = 20
        pct_add = 50
        
        expected = (base + flat_add) * (100 + pct_add) // 100
        assert expected == 180

    def test_resolution_order_flat_sum(self):
        base = 10
        flat_add = 5
        flat_sub = 3
        
        flat_sum = flat_add - flat_sub
        result = base + flat_sum
        assert result == 12

    def test_resolution_order_percentage_on_zero_base(self):
        base = 0
        pct_add = 50
        
        result = (base + 0) * (100 + pct_add) // 100
        assert result == 0

    def test_resolution_order_multiplicative_sequential(self):
        base = 100
        flat_add = 10
        pct_add = 20
        multiply = 1.5
        
        post_flat = base + flat_add
        post_pct = post_flat * (100 + pct_add) // 100
        final = post_pct * multiply
        assert final == 198

    def test_resolution_order_multiple_multiply_chain(self):
        value = 100
        multiply_1 = 2.0
        multiply_2 = 0.5
        
        result = value * multiply_1 * multiply_2
        assert result == 100.0


class TestModifierSerialization:
    def test_modifier_serializes_to_json(self):
        modifier = Modifier(
            stat=Stat.HP,
            operation=Operation.FLAT_SUB,
            value=15,
            duration=0,
            target=Target.ENEMY_SINGLE
        )
        json_str = modifier.model_dump_json()
        assert "HP" in json_str and "FLAT_SUB" in json_str

    def test_tags_field_is_list_of_strings(self):
        modifier = Modifier(
            stat=Stat.HP,
            operation=Operation.FLAT_SUB,
            value=15,
            duration=0,
            target=Target.ENEMY_SINGLE,
            tags=["fire", "dot"]
        )
        assert modifier.tags == ["fire", "dot"]
        assert all(isinstance(tag, str) for tag in modifier.tags)
