from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, List, Optional
from .modifier import Modifier, STAT_SCALE
from .enums import Stat, AiHeuristic


class CharacterGenerationBounds(BaseModel):
    per_stat_min: Dict[Stat, int] = Field(
        ..., description="Minimum value for each stat"
    )
    per_stat_max: Dict[Stat, int] = Field(
        ..., description="Maximum value for each stat"
    )
    total_budget_min: int = Field(..., description="Minimum sum of all stats")
    total_budget_max: int = Field(..., description="Maximum sum of all stats")

    @field_validator("per_stat_min", "per_stat_max")
    @classmethod
    def all_stats_present(cls, v: Dict[Stat, int]) -> Dict[Stat, int]:
        required_stats = {Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy}
        if set(v.keys()) != required_stats:
            raise ValueError(f"All 5 stats required, got: {set(v.keys())}")
        return v

    @field_validator("per_stat_min")
    @classmethod
    def min_within_bounds(cls, v: Dict[Stat, int]) -> Dict[Stat, int]:
        for stat, value in v.items():
            if value < 0:
                raise ValueError(f"per_stat_min[{stat}] cannot be negative: {value}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "per_stat_min": {
                        "HP": 50,
                        "Power": 8,
                        "Speed": 60,
                        "Defense": 3,
                        "Energy": 2,
                    },
                    "per_stat_max": {
                        "HP": 150,
                        "Power": 35,
                        "Speed": 130,
                        "Defense": 25,
                        "Energy": 7,
                    },
                    "total_budget_min": 150,
                    "total_budget_max": 350,
                }
            ]
        }
    )


class Character(BaseModel):
    id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., description="Character display name")
    base_stats: Dict[Stat, int] = Field(
        ..., description="Base stats (pre-scaled by STAT_SCALE), all 5 required"
    )
    innate_passive: Modifier = Field(..., description="Permanent passive ability")
    name_parts: Dict[str, str] = Field(
        ..., description="Name components: first_name, title, origin"
    )

    @field_validator("base_stats")
    @classmethod
    def all_stats_present(cls, v: Dict[Stat, int]) -> Dict[Stat, int]:
        required_stats = {Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy}
        if set(v.keys()) != required_stats:
            raise ValueError(f"All 5 stats required, got: {set(v.keys())}")
        for stat, value in v.items():
            if value < 0:
                raise ValueError(f"base_stats[{stat}] cannot be negative: {value}")
        return v

    @field_validator("innate_passive")
    @classmethod
    def passive_must_be_permanent(cls, v: Modifier) -> Modifier:
        if v.duration != -1:
            raise ValueError(
                f"Innate passive must have duration=-1 (permanent), got duration={v.duration}"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "vanguard_sentinel",
                    "name": "Vanguard Sentinel",
                    "base_stats": {
                        "HP": 140000,
                        "Power": 12000,
                        "Speed": 80000,
                        "Defense": 20000,
                        "Energy": 3000,
                    },
                    "innate_passive": {
                        "stat": "Defense",
                        "operation": "PCT_ADD",
                        "value": 15,
                        "duration": -1,
                        "target": "SELF",
                        "stacking": "stack",
                        "tags": ["passive"],
                    },
                    "name_parts": {
                        "first_name": "Alvino",
                        "title": "Vanguard Sentinel",
                        "origin": "Mountains of Kud",
                    },
                }
            ]
        }
    )


class Enemy(BaseModel):
    id: str = Field(..., description="Unique enemy identifier")
    name: str = Field(..., description="Enemy display name")
    base_stats: Dict[Stat, int] = Field(
        ..., description="Base stats (pre-scaled by STAT_SCALE), all 5 required"
    )
    card_pool: List[str] = Field(
        ..., description="Card IDs this enemy can play", min_length=1
    )
    ai_heuristic_tag: AiHeuristic = Field(..., description="AI behavior tag")
    is_elite: bool = Field(
        default=False, description="Elite enemies have enhanced stats and rewards"
    )

    @field_validator("base_stats")
    @classmethod
    def all_stats_present(cls, v: Dict[Stat, int]) -> Dict[Stat, int]:
        required_stats = {Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy}
        if set(v.keys()) != required_stats:
            raise ValueError(f"All 5 stats required, got: {set(v.keys())}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "scavenger_patrol",
                    "name": "Scavenger Patrol",
                    "base_stats": {
                        "HP": 60000,
                        "Power": 10000,
                        "Speed": 70000,
                        "Defense": 5000,
                        "Energy": 3000,
                    },
                    "card_pool": ["arcane_strike_01", "sweeping_blade_01"],
                    "ai_heuristic_tag": "aggressive",
                    "is_elite": False,
                }
            ]
        }
    )
