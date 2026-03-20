"""Player strategy Protocol — structural subtyping interface for campaign AI."""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from models.entity import Character
    from models.card import Card, UpgradeEntry
    from models.campaign import WorldCard, EventChoice
    from engine.turn_order import CombatEntity
    from campaign.state import CampaignState, RegionState
    from campaign.loader import GameData


class PlayerStrategy(Protocol):
    """Interface for player campaign AI."""

    def select_region(
        self,
        state: CampaignState,
        game_data: GameData,
    ) -> RegionState:
        """Choose which region to assault next."""
        ...

    def select_party(
        self,
        state: CampaignState,
        game_data: GameData,
        region: RegionState,
    ) -> list[Character]:
        """Choose which characters to bring (up to party_size)."""
        ...

    def select_card(
        self,
        caster: CombatEntity,
        available_cards: list[Card],
        allies: list[CombatEntity],
        enemies: list[CombatEntity],
    ) -> tuple[Card, list[CombatEntity]] | None:
        """Choose a card to play during combat."""
        ...

    def evaluate_world_card(
        self,
        card: WorldCard,
        state: CampaignState,
        game_data: GameData,
    ) -> bool:
        """Accept (True) or skip (False) a world card."""
        ...

    def select_event_choice(
        self,
        choices: list[EventChoice],
        state: CampaignState,
    ) -> int:
        """Choose which event option to take (returns index)."""
        ...

    def select_card_upgrade(
        self,
        roster_cards: list[str],
        upgrade_trees: dict[str, dict[str, UpgradeEntry]],
        applied_upgrades: dict[str, list[str]],
        state: CampaignState,
    ) -> tuple[str, str] | None:
        """Choose a card upgrade. Returns (card_id, branch_key) or None."""
        ...

    def select_research(
        self,
        state: CampaignState,
        game_data: GameData,
    ) -> RegionState | None:
        """Choose a region to research (or None to skip)."""
        ...

    def select_drafted_character(
        self,
        candidates: list[Character],
        state: CampaignState,
    ) -> Character:
        """Pick one character from the draft pool."""
        ...
