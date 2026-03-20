"""Campaign state — mutable state container tracking all campaign progress."""

import random
from dataclasses import dataclass, field
from typing import List

from models.entity import Character
from models.modifier import Modifier
from models.campaign import Region, OutpostUpgrade


@dataclass
class RegionState:
    """Tracking state for a single region."""
    region: Region
    conquered: bool = False
    research_level: int = 0
    assigned_difficulty: int = 1


@dataclass
class CampaignState:
    """Full mutable campaign state."""
    seed: int
    rng: random.Random
    turn_number: int = 0
    resources: int = 0
    roster: list[Character] = field(default_factory=list)
    region_states: list[RegionState] = field(default_factory=list)
    skip_tokens: int = 0
    active_world_modifiers: list[Modifier] = field(default_factory=list)
    active_outpost_upgrades: list[OutpostUpgrade] = field(default_factory=list)
    card_upgrades_applied: dict[str, list[str]] = field(default_factory=dict)
    drafted_characters: list[str] = field(default_factory=list)
    game_over: bool = False
    victory: bool = False
    campaign_log: list[str] = field(default_factory=list)

    @property
    def party_size(self) -> int:
        """Base 3, +1 if War Room upgrade active."""
        base = 3
        for upgrade in self.active_outpost_upgrades:
            if upgrade.special_effect == "party_size+1":
                base += 1
        return min(base, len(self.roster))

    @property
    def conquered_count(self) -> int:
        return sum(1 for rs in self.region_states if rs.conquered)

    @property
    def unconquered_regions(self) -> list[RegionState]:
        return [rs for rs in self.region_states if not rs.conquered]
