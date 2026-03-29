from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Dict, Literal, Union
from .modifier import Modifier
from .enums import NarrativePosition


class ResearchLayer(BaseModel):
    level: int = Field(..., ge=1, le=4, description="Research level (1-4)")
    reveal_type: str = Field(..., description="Type of information revealed")
    cost: int = Field(..., ge=0, description="Cost to unlock this layer")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"level": 1, "reveal_type": "region_type", "cost": 10},
                {"level": 2, "reveal_type": "primary_modifier", "cost": 25},
                {"level": 3, "reveal_type": "encounter_details", "cost": 50},
                {"level": 4, "reveal_type": "boss_mechanics", "cost": 100},
            ]
        }
    )


class CombatEncounter(BaseModel):
    type: Literal["combat"] = Field(default="combat")
    narrative_position: NarrativePosition = Field(
        ..., description="Position in narrative arc"
    )
    name: str = Field(..., description="Encounter name")
    description: str = Field(..., description="Encounter description")
    enemies: List[str] = Field(..., min_length=1, description="Enemy IDs")
    enemy_cards: List[str] = Field(..., description="Card IDs enemies can play")


class HazardEncounter(BaseModel):
    type: Literal["hazard"] = Field(default="hazard")
    narrative_position: NarrativePosition = Field(
        ..., description="Position in narrative arc"
    )
    name: str = Field(..., description="Encounter name")
    description: str = Field(..., description="Encounter description")
    hazard_modifiers: List[Modifier] = Field(
        ..., min_length=1, description="Hazard effects"
    )
    hazard_duration: int = Field(..., gt=0, description="Duration in turns")


class EventChoice(BaseModel):
    description: str = Field(..., description="Choice description")
    effects: List[Modifier] = Field(..., description="Modifiers applied when chosen")
    cost: List[Modifier] = Field(
        default_factory=list, description="Optional cost modifiers"
    )


class EventEncounter(BaseModel):
    type: Literal["event"] = Field(default="event")
    narrative_position: NarrativePosition = Field(
        ..., description="Position in narrative arc"
    )
    name: str = Field(..., description="Encounter name")
    description: str = Field(..., description="Encounter description")
    choices: List[EventChoice] = Field(
        ..., min_length=2, description="Event choices (min 2)"
    )


Encounter = Union[CombatEncounter, HazardEncounter, EventEncounter]


class Region(BaseModel):
    id: str = Field(..., description="Unique region identifier")
    name: str = Field(..., description="Region display name")
    region_type: str = Field(..., description="Flavor category (e.g., Ashen Wastes)")
    modifier_stack: List[Modifier] = Field(
        ..., description="Active modifiers during region"
    )
    encounters: List[Encounter] = Field(
        ..., description="3 encounters in narrative order"
    )
    meta_reward: Modifier = Field(
        ..., description="Reward granted to participants on conquest"
    )
    research_layers: List[ResearchLayer] = Field(..., description="4 research layers")

    @field_validator("encounters")
    @classmethod
    def exactly_three_encounters(cls, v: List[Encounter]) -> List[Encounter]:
        if len(v) != 3:
            raise ValueError(f"Region must have exactly 3 encounters, got {len(v)}")
        return v

    @field_validator("encounters")
    @classmethod
    def narrative_positions_valid(cls, v: List[Encounter]) -> List[Encounter]:
        positions = [e.narrative_position for e in v]
        expected = [
            NarrativePosition.approach,
            NarrativePosition.settlement,
            NarrativePosition.stronghold,
        ]
        if positions != expected:
            raise ValueError(
                f"Encounters must follow approach/settlement/stronghold order, got {positions}"
            )
        return v

    @field_validator("encounters")
    @classmethod
    def stronghold_must_be_combat(cls, v: List[Encounter]) -> List[Encounter]:
        if len(v) < 3:
            return v
        if v[2].type != "combat":
            raise ValueError("Stronghold encounter (position 2) must be combat type")
        return v

    @field_validator("research_layers")
    @classmethod
    def exactly_four_layers(cls, v: List[ResearchLayer]) -> List[ResearchLayer]:
        if len(v) != 4:
            raise ValueError(
                f"Region must have exactly 4 research layers, got {len(v)}"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "ashen_wastes",
                    "name": "The Ashen Wastes",
                    "region_type": "Ashen",
                    "modifier_stack": [
                        {
                            "stat": "Speed",
                            "operation": "PCT_SUB",
                            "value": 15,
                            "duration": -1,
                            "target": "ALLY_ALL",
                        }
                    ],
                    "encounters": [],
                    "meta_reward": {
                        "stat": "Defense",
                        "operation": "FLAT_ADD",
                        "value": 2000,
                        "duration": -1,
                        "target": "SELF",
                    },
                    "research_layers": [],
                }
            ]
        }
    )


class WorldCard(BaseModel):
    id: str = Field(..., description="Unique card identifier")
    name: str = Field(..., description="Card display name")
    upside: List[Modifier] = Field(
        ..., min_length=1, description="Beneficial modifiers"
    )
    downside: List[Modifier] = Field(..., min_length=1, description="Cost modifiers")
    description: str = Field(..., description="Trade-off description")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "forced_march",
                    "name": "Forced March",
                    "upside": [
                        {
                            "stat": "Speed",
                            "operation": "PCT_ADD",
                            "value": 30,
                            "duration": -1,
                            "target": "ALLY_ALL",
                        }
                    ],
                    "downside": [
                        {
                            "stat": "HP",
                            "operation": "PCT_SUB",
                            "value": 20,
                            "duration": -1,
                            "target": "ALLY_ALL",
                        }
                    ],
                    "description": "Speed up at the cost of HP",
                }
            ]
        }
    )


class OutpostUpgrade(BaseModel):
    id: str = Field(..., description="Unique upgrade identifier")
    name: str = Field(..., description="Upgrade display name")
    description: str = Field(..., description="Upgrade description")
    effects: List[Modifier] = Field(..., description="Stat modifiers (all permanent)")
    cost: int = Field(..., ge=0, description="Upgrade cost")
    special_effect: str = Field(
        default="", description="Special effect for non-stat mechanics"
    )

    @field_validator("effects")
    @classmethod
    def all_effects_permanent(cls, v: List[Modifier]) -> List[Modifier]:
        for effect in v:
            if effect.duration != -1:
                raise ValueError(
                    f"Outpost upgrade effects must have duration=-1 (permanent), got {effect.duration}"
                )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "forge",
                    "name": "Forge",
                    "description": "Forges weapons for the party",
                    "effects": [
                        {
                            "stat": "Power",
                            "operation": "FLAT_ADD",
                            "value": 2000,
                            "duration": -1,
                            "target": "SELF",
                        }
                    ],
                    "cost": 50,
                    "special_effect": "",
                },
                {
                    "id": "war_room",
                    "name": "War Room",
                    "description": "Increases party size",
                    "effects": [],
                    "cost": 100,
                    "special_effect": "party_size+1",
                },
            ]
        }
    )
