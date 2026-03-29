from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List
from .enums import Stat, Operation, Target, Stacking

STAT_SCALE = 1000


class Modifier(BaseModel):
    stat: Stat
    operation: Operation
    value: int = Field(..., description="Integer value only - no floats")
    duration: int = Field(..., ge=-1, description="Duration in turns (0=instant, -1=permanent, >0=turn-based)")
    target: Target
    stacking: Stacking = Field(default="replace", description="Stacking behavior: stack, replace, or max")
    tags: List[str] = Field(default_factory=list, description="Optional tags for future condition evaluation - no v1 logic")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "stat": "HP",
                    "operation": "FLAT_SUB",
                    "value": 15,
                    "duration": 0,
                    "target": "ENEMY_SINGLE",
                    "stacking": "replace",
                    "tags": ["attack", "physical"]
                }
            ]
        }
    )
