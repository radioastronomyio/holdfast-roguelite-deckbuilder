"""Encounter generation — pure functions producing Encounters from RNG + position + difficulty."""

import random
from typing import List

from models.campaign import (
    CombatEncounter,
    HazardEncounter,
    EventEncounter,
    EventChoice,
    Encounter,
)
from models.modifier import Modifier, STAT_SCALE
from models.enums import (
    Stat,
    Operation,
    Target,
    Stacking,
    NarrativePosition,
    EncounterType,
)
from generation.characters import FlavorData
from generation.enemies import generate_enemy


def generate_event_choices(
    rng: random.Random,
    difficulty: int,
    num_choices: int = 2,
) -> List[EventChoice]:
    """
    Generate trade-off event choices.
    Each choice has effects (upside) and cost (downside).
    Higher difficulty = larger values on both sides.
    """
    all_stats = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy]
    choices = []
    for _ in range(num_choices):
        # Upside: 1-2 beneficial modifiers
        num_effects = rng.randint(1, 2)
        effects = []
        for _ in range(num_effects):
            stat = rng.choice(all_stats)
            op = rng.choice([Operation.PCT_ADD, Operation.FLAT_ADD])
            if op == Operation.PCT_ADD:
                value = rng.randint(5, 10) + difficulty * 2
            else:
                value = (rng.randint(1, 3) + difficulty) * STAT_SCALE
            effects.append(Modifier(
                stat=stat,
                operation=op,
                value=value,
                duration=rng.randint(2, 5),
                target=Target.SELF,
                stacking=Stacking.stack,
            ))

        # Downside: 1-2 harmful modifiers
        num_costs = rng.randint(1, 2)
        costs = []
        for _ in range(num_costs):
            stat = rng.choice(all_stats)
            op = rng.choice([Operation.PCT_SUB, Operation.FLAT_SUB])
            if op == Operation.PCT_SUB:
                value = rng.randint(3, 8) + difficulty
            else:
                value = (rng.randint(1, 2) + difficulty) * STAT_SCALE
            costs.append(Modifier(
                stat=stat,
                operation=op,
                value=value,
                duration=rng.randint(2, 5),
                target=Target.SELF,
                stacking=Stacking.stack,
            ))

        choices.append(EventChoice(
            description=f"A difficult choice at difficulty {difficulty}",
            effects=effects,
            cost=costs,
        ))
    return choices


def _generate_hazard(
    rng: random.Random,
    position: NarrativePosition,
    difficulty: int,
    flavor: FlavorData,
) -> HazardEncounter:
    """Generate a hazard encounter."""
    all_stats = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy]
    hazard_ops = [Operation.FLAT_SUB, Operation.PCT_SUB]

    num_modifiers = rng.randint(1, 3)
    modifiers = []
    for _ in range(num_modifiers):
        stat = rng.choice(all_stats)
        op = rng.choice(hazard_ops)
        if op == Operation.FLAT_SUB:
            value = (rng.randint(1, 3) + difficulty) * STAT_SCALE
        else:
            value = rng.randint(10, 25) + difficulty * 3
        modifiers.append(Modifier(
            stat=stat,
            operation=op,
            value=value,
            duration=-1,
            target=Target.ALLY_ALL,
            stacking=Stacking.stack,
        ))

    duration = rng.randint(2, 5)

    adj = rng.choice(flavor.region_nouns) if flavor.region_nouns else "Unknown"
    name = f"Hazardous {adj}"

    return HazardEncounter(
        narrative_position=position,
        name=name,
        description=f"A {name.lower()} blocks the path ahead.",
        hazard_modifiers=modifiers,
        hazard_duration=duration,
    )


def _generate_event(
    rng: random.Random,
    position: NarrativePosition,
    difficulty: int,
    flavor: FlavorData,
) -> EventEncounter:
    """Generate an event encounter."""
    num_choices = rng.randint(2, 3)
    choices = generate_event_choices(rng, difficulty, num_choices)

    noun = rng.choice(flavor.region_nouns) if flavor.region_nouns else "Place"
    name = f"Crossroads of {noun}"

    return EventEncounter(
        narrative_position=position,
        name=name,
        description=f"A strange encounter at the {name.lower()}.",
        choices=choices,
    )


def _generate_combat(
    rng: random.Random,
    position: NarrativePosition,
    difficulty: int,
    available_card_ids: list[str],
    flavor: FlavorData,
    force_elite: bool = False,
    enemy_registry: dict | None = None,
    cards_by_id: dict | None = None,
) -> CombatEncounter:
    """Generate a combat encounter. If enemy_registry is provided, generated Enemy objects are stored there."""
    from models.entity import Enemy as EnemyModel
    enemy_ids = []
    enemy_cards: list[str] = []

    def _add(e: EnemyModel) -> None:
        enemy_ids.append(e.id)
        enemy_cards.extend(e.card_pool)
        if enemy_registry is not None:
            enemy_registry[e.id] = e

    if force_elite:
        # Stronghold: 1 elite + 0-2 adds
        _add(generate_enemy(rng, difficulty, available_card_ids, is_elite=True, flavor=flavor, cards_by_id=cards_by_id))
        for _ in range(rng.randint(0, 2)):
            _add(generate_enemy(rng, difficulty, available_card_ids, is_elite=False, flavor=flavor, cards_by_id=cards_by_id))
    else:
        # Settlement: 1-3 non-elite
        for _ in range(rng.randint(1, 3)):
            _add(generate_enemy(rng, difficulty, available_card_ids, is_elite=False, flavor=flavor, cards_by_id=cards_by_id))

    # Deduplicate enemy_cards while preserving order
    seen: set[str] = set()
    unique_cards = [c for c in enemy_cards if not (c in seen or seen.add(c))]  # type: ignore[func-returns-value]

    noun = rng.choice(flavor.region_nouns) if flavor.region_nouns else "Ground"
    name = f"Battle at {noun}"

    return CombatEncounter(
        narrative_position=position,
        name=name,
        description=f"Enemies await at the {name.lower()}.",
        enemies=enemy_ids,
        enemy_cards=unique_cards,
    )


def generate_encounter(
    rng: random.Random,
    position: NarrativePosition,
    difficulty: int,
    available_card_ids: list[str],
    flavor: FlavorData,
    enemy_registry: dict | None = None,
    cards_by_id: dict | None = None,
) -> Encounter:
    """Generate a single encounter based on narrative position."""
    if position == NarrativePosition.approach:
        roll = rng.random()
        if roll < 0.6:
            return _generate_hazard(rng, position, difficulty, flavor)
        else:
            return _generate_event(rng, position, difficulty, flavor)

    elif position == NarrativePosition.settlement:
        roll = rng.random()
        if roll < 0.7:
            return _generate_combat(rng, position, difficulty, available_card_ids, flavor, enemy_registry=enemy_registry, cards_by_id=cards_by_id)
        else:
            return _generate_event(rng, position, difficulty, flavor)

    elif position == NarrativePosition.stronghold:
        return _generate_combat(rng, position, difficulty, available_card_ids, flavor, force_elite=True, enemy_registry=enemy_registry, cards_by_id=cards_by_id)

    raise ValueError(f"Unknown narrative position: {position}")
