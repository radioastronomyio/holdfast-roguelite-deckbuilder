from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict
from .modifier import Modifier


class UpgradeEntry(BaseModel):
    added_effects: List[Modifier] = Field(..., description="Modifiers added at this upgrade tier")
    prerequisite: Optional[str] = Field(None, description="Prerequisite branch key, or None for tier 1")
    tier: int = Field(..., ge=1, le=3, description="Upgrade tier (1, 2, or 3)")
    exclusions: List[str] = Field(default_factory=list, description="Branch keys that become unavailable when this upgrade is chosen")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "added_effects": [
                        {
                            "stat": "Defense",
                            "operation": "PCT_SUB",
                            "value": 15,
                            "duration": 2,
                            "target": "ENEMY_SINGLE"
                        }
                    ],
                    "prerequisite": None,
                    "tier": 1,
                    "exclusions": []
                }
            ]
        }
    )


UpgradeTree = Dict[str, UpgradeEntry]


class Card(BaseModel):
    id: str = Field(..., description="Unique card identifier")
    name: str = Field(..., description="Card display name")
    energy_cost: int = Field(..., ge=0, description="Energy cost to play this card")
    effects: List[Modifier] = Field(..., description="Primary effects of the card")
    tags: List[str] = Field(default_factory=list, description="Card tags for keyword matching")
    deck_copies: int = Field(default=1, ge=1, le=5, description="Number of copies of this card in a starting deck")
    upgrade_tier: int = Field(default=0, ge=0, le=3, description="Current upgrade tier (0-3)")
    upgrade_paths: UpgradeTree = Field(default_factory=dict, description="Available upgrade branches keyed by branch ID")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": "strike_01",
                    "name": "Strike",
                    "energy_cost": 2,
                    "effects": [
                        {
                            "stat": "HP",
                            "operation": "FLAT_SUB",
                            "value": 12,
                            "duration": 0,
                            "target": "ENEMY_SINGLE"
                        }
                    ],
                    "tags": ["attack", "physical"],
                    "upgrade_tier": 0,
                    "upgrade_paths": {}
                }
            ],
            "description": "Card effects are modifier tuples. Power stat interaction: character Power adds to damage effects at resolution time (M2)."
        }
    )

    @field_validator("upgrade_paths")
    @classmethod
    def validate_upgrade_tree_prerequisites(cls, v: UpgradeTree) -> UpgradeTree:
        for branch_key, entry in v.items():
            if entry.tier == 1 and entry.prerequisite is not None:
                raise ValueError(f"Tier 1 upgrade {branch_key} must have prerequisite=None, got {entry.prerequisite}")
            if entry.tier >= 2 and entry.prerequisite is None:
                raise ValueError(f"Tier {entry.tier} upgrade {branch_key} must have a non-None prerequisite")
            if entry.prerequisite is not None and entry.prerequisite not in v:
                raise ValueError(f"Upgrade {branch_key} has prerequisite {entry.prerequisite} which does not exist in the tree")
        return v
