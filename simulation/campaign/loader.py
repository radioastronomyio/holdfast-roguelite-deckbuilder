"""Data loader — loads all JSON data files and normalizes values for engine consumption."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from models.card import Card, UpgradeEntry
from models.entity import Character, Enemy, CharacterGenerationBounds
from models.campaign import Region, WorldCard, OutpostUpgrade
from models.modifier import Modifier, STAT_SCALE
from models.enums import Operation
from generation.characters import FlavorData, load_flavor_data


@dataclass
class GameData:
    """All game data loaded and normalized for engine consumption."""
    cards_by_id: dict[str, Card]
    upgrade_trees: dict[str, dict[str, UpgradeEntry]]
    characters: list[Character]
    enemies_by_id: dict[str, Enemy]
    generation_bounds: CharacterGenerationBounds
    regions: list[Region]
    world_deck: list[WorldCard]
    outpost_upgrades: list[OutpostUpgrade]
    flavor: FlavorData


def scale_modifier(mod: Modifier) -> Modifier:
    """Scale a single modifier's value if it's a FLAT operation."""
    if mod.operation in (Operation.FLAT_ADD, Operation.FLAT_SUB):
        return mod.model_copy(update={"value": mod.value * STAT_SCALE})
    return mod


def _scale_card(card_data: dict) -> dict:
    """Scale FLAT effect values in a card dict before constructing the model."""
    if "effects" in card_data:
        scaled_effects = []
        for eff in card_data["effects"]:
            mod = Modifier(**eff)
            scaled = scale_modifier(mod)
            scaled_effects.append(scaled.model_dump())
        card_data = {**card_data, "effects": scaled_effects}

    if "upgrade_paths" in card_data:
        scaled_paths = {}
        for branch_key, entry_data in card_data["upgrade_paths"].items():
            if "added_effects" in entry_data:
                scaled_added = []
                for eff in entry_data["added_effects"]:
                    mod = Modifier(**eff)
                    scaled = scale_modifier(mod)
                    scaled_added.append(scaled.model_dump())
                entry_data = {**entry_data, "added_effects": scaled_added}
            scaled_paths[branch_key] = entry_data
        card_data = {**card_data, "upgrade_paths": scaled_paths}

    return card_data


def load_game_data(
    data_path: Path = Path("data"),
    mods_path: Path = Path("mods/default/flavor"),
) -> GameData:
    """Load all JSON data files and normalize values."""

    # Load cards (display scale → STAT_SCALE for FLAT ops)
    with open(data_path / "cards" / "base-cards.json") as f:
        raw_cards = json.load(f)
    with open(data_path / "cards" / "hazard-cards.json") as f:
        raw_hazards = json.load(f)

    cards_by_id: dict[str, Card] = {}
    upgrade_trees: dict[str, dict[str, UpgradeEntry]] = {}

    for raw in raw_cards + raw_hazards:
        scaled = _scale_card(raw)
        card = Card(**scaled)
        cards_by_id[card.id] = card
        if card.upgrade_paths:
            upgrade_trees[card.id] = card.upgrade_paths

    # Load characters (base_stats already at STAT_SCALE — do NOT double-scale)
    with open(data_path / "entities" / "example-characters.json") as f:
        raw_chars = json.load(f)
    characters = [Character(**c) for c in raw_chars]

    # Load enemies (base_stats already at STAT_SCALE)
    with open(data_path / "entities" / "example-enemies.json") as f:
        raw_enemies = json.load(f)
    enemies_by_id = {e["id"]: Enemy(**e) for e in raw_enemies}

    # Load generation bounds (display scale — generators handle their own scaling)
    with open(data_path / "entities" / "generation-bounds.json") as f:
        generation_bounds = CharacterGenerationBounds(**json.load(f))

    # Load regions (values already at STAT_SCALE in JSON)
    with open(data_path / "campaign" / "example-regions.json") as f:
        raw_regions = json.load(f)
    regions = [Region(**r) for r in raw_regions]

    # Load world deck (values already at STAT_SCALE in JSON)
    with open(data_path / "campaign" / "world-deck.json") as f:
        raw_world = json.load(f)
    world_deck = [WorldCard(**w) for w in raw_world]

    # Load outpost upgrades (values already at STAT_SCALE in JSON)
    with open(data_path / "campaign" / "outpost-upgrades.json") as f:
        raw_outpost = json.load(f)
    outpost_upgrades = [OutpostUpgrade(**o) for o in raw_outpost]

    # Load flavor data
    flavor = load_flavor_data(mods_path)

    return GameData(
        cards_by_id=cards_by_id,
        upgrade_trees=upgrade_trees,
        characters=characters,
        enemies_by_id=enemies_by_id,
        generation_bounds=generation_bounds,
        regions=regions,
        world_deck=world_deck,
        outpost_upgrades=outpost_upgrades,
        flavor=flavor,
    )
