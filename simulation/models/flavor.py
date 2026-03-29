from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Union, Literal
from .enums import Stat


class EpithetCondition1(BaseModel):
    type: Literal[1] = Field(..., description="Single stat threshold")
    stat: Stat
    op: str = Field(..., description="Operator: >=, <=, >, <, =, <>")
    value: int

    @field_validator("op")
    @classmethod
    def valid_operator(cls, v: str) -> str:
        valid_ops = {">=", "<=", ">", "<", "=", "<>"}
        if v not in valid_ops:
            raise ValueError(f"Invalid operator: {v}. Must be one of {valid_ops}")
        return v


class EpithetCondition2(BaseModel):
    type: Literal[2] = Field(..., description="Two-stat condition with logic")
    stat_a: Stat
    op_a: str
    value_a: int
    logic: Literal["AND", "OR", "XOR"]
    stat_b: Stat
    op_b: str
    value_b: int

    @field_validator("op_a", "op_b")
    @classmethod
    def valid_operator(cls, v: str) -> str:
        valid_ops = {">=", "<=", ">", "<", "=", "<>"}
        if v not in valid_ops:
            raise ValueError(f"Invalid operator: {v}. Must be one of {valid_ops}")
        return v


EpithetCondition = Union[EpithetCondition1, EpithetCondition2]


class EpithetEntry(BaseModel):
    epithet: str = Field(..., description="The epithet title")
    conditions: List[EpithetCondition] = Field(
        ..., description="Conditions for epithet eligibility"
    )
    pool: Literal["default", "rare"] = Field(..., description="Pool tier for weighting")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "epithet": "the Strong",
                    "conditions": [
                        {"type": 1, "stat": "power", "op": ">=", "value": 70}
                    ],
                    "pool": "default",
                },
                {
                    "epithet": "the Volatile",
                    "conditions": [
                        {
                            "type": 2,
                            "stat_a": "power",
                            "op_a": ">=",
                            "value_a": 75,
                            "logic": "XOR",
                            "stat_b": "defense",
                            "op_b": "<=",
                            "value_b": 25,
                        }
                    ],
                    "pool": "rare",
                },
            ]
        }
    )


class ElementStatMap(BaseModel):
    power: Dict[str, List[str]] = Field(..., description="Element pools for power stat")
    speed: Dict[str, List[str]] = Field(..., description="Element pools for speed stat")
    defense: Dict[str, List[str]] = Field(
        ..., description="Element pools for defense stat"
    )
    energy: Dict[str, List[str]] = Field(
        ..., description="Element pools for energy stat"
    )
    hp: Dict[str, List[str]] = Field(..., description="Element pools for hp stat")

    @field_validator("power", "speed", "defense", "energy", "hp")
    @classmethod
    def has_default_and_rare(cls, v: Dict[str, List[str]]) -> Dict[str, List[str]]:
        if "default" not in v or "rare" not in v:
            raise ValueError("Each stat must have 'default' and 'rare' element pools")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "power": {
                        "default": ["Magma", "Stone", "Thunder"],
                        "rare": ["Inferno"],
                    },
                    "speed": {
                        "default": ["Storm", "Wind", "Void"],
                        "rare": ["Phantom"],
                    },
                    "defense": {
                        "default": ["Iron", "Stone", "Earth"],
                        "rare": ["Bastion"],
                    },
                    "energy": {
                        "default": ["Arcane", "Ether", "Pulse"],
                        "rare": ["Nexus"],
                    },
                    "hp": {"default": ["Blood", "Bone", "Marrow"], "rare": ["Undying"]},
                }
            ]
        }
    )


class FlavorPools(BaseModel):
    given_names: List[str] = Field(..., min_length=1)
    archetypes: List[str] = Field(..., min_length=1)
    action_verbs: List[str] = Field(..., min_length=1)
    region_adjectives: List[str] = Field(..., min_length=1)
    region_nouns: List[str] = Field(..., min_length=1)
