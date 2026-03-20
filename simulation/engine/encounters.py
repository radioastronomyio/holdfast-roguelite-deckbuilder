from __future__ import annotations

from dataclasses import dataclass, field

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target
from models.card import Card
from models.campaign import EventChoice
from engine.turn_order import (
    CombatEntity,
    get_current_stat,
    tick_until_next_turn,
    process_turn_start,
    CT_THRESHOLD,
)
from engine.stats import calculate_stat, apply_stacking
from engine.enemy_ai import pick_enemy_action
from agents.enemy_ai_v2 import pick_enemy_action_v2

COMBAT_TURN_CAP = 200


@dataclass
class CombatResult:
    player_won: bool
    turns_taken: int
    survivors: list[str]
    combat_log: list[str]
    final_state: list[CombatEntity]


@dataclass
class HazardResult:
    survived: bool
    damage_taken: dict[str, int]
    combat_log: list[str]
    final_state: list[CombatEntity]


@dataclass
class EventResult:
    choice_index: int
    effects_applied: list[Modifier]
    costs_applied: list[Modifier]
    combat_log: list[str]
    final_state: list[CombatEntity]


def play_card(
    card: Card,
    caster: CombatEntity,
    targets: list[CombatEntity],
    all_entities: list[CombatEntity],
) -> list[str]:
    """
    Resolve a card being played.
    1. Deduct energy_cost from caster.current_energy
    2. For each effect: resolve targets relative to caster's side, apply damage/modifiers
    3. Return log messages
    """
    logs = []
    caster.current_energy -= card.energy_cost
    caster_power = get_current_stat(caster, Stat.Power)

    # Determine caster's allies and enemies
    caster_allies = [e for e in all_entities if e.is_player == caster.is_player and e.is_alive]
    caster_enemies = [e for e in all_entities if e.is_player != caster.is_player and e.is_alive]

    for effect in card.effects:
        # Resolve actual targets based on effect.target, relative to caster's side
        if effect.target == Target.SELF:
            effect_targets = [caster]
        elif effect.target == Target.ALLY_SINGLE:
            effect_targets = targets
        elif effect.target == Target.ALLY_ALL:
            effect_targets = caster_allies
        elif effect.target == Target.ENEMY_SINGLE:
            effect_targets = targets
        elif effect.target == Target.ENEMY_ALL:
            effect_targets = caster_enemies
        elif effect.target == Target.GLOBAL:
            effect_targets = [e for e in all_entities if e.is_alive]
        else:
            effect_targets = targets

        for target in effect_targets:
            if not target.is_alive:
                continue

            # Damage effects: FLAT_SUB HP → add Power, subtract Defense
            if effect.operation == Operation.FLAT_SUB and effect.stat == Stat.HP and effect.duration == 0:
                base_damage = effect.value + caster_power
                target_defense = get_current_stat(target, Stat.Defense)
                actual_damage = max(0, base_damage - target_defense)
                target.base_stats[Stat.HP] -= actual_damage
                logs.append(f"{caster.name} dealt {actual_damage // STAT_SCALE} HP damage to {target.name}")
                # Check death
                if target.base_stats[Stat.HP] <= 0:
                    target.is_alive = False
                    logs.append(f"{target.name} has died")
            elif effect.duration == 0:
                # Instant non-damage effect: apply directly to base_stats
                if effect.operation == Operation.FLAT_ADD:
                    target.base_stats[effect.stat] += effect.value
                elif effect.operation == Operation.FLAT_SUB:
                    target.base_stats[effect.stat] -= effect.value
                    if effect.stat != Stat.HP:
                        target.base_stats[effect.stat] = max(0, target.base_stats[effect.stat])
                logs.append(f"{effect.stat} modified on {target.name}")
            else:
                # Duration > 0 or -1: add to active_modifiers (with stacking)
                new_mods = target.active_modifiers + [effect]
                target.active_modifiers = apply_stacking(new_mods)
                logs.append(f"Applied {effect.stat} {effect.operation} to {target.name}")

    return logs


def _player_pick_card(
    caster: CombatEntity,
    available_cards: list[Card],
    enemies: list[CombatEntity],
) -> tuple[Card, list[CombatEntity]] | None:
    """Placeholder player strategy: lowest cost card targeting lowest HP enemy."""
    living_enemies = [e for e in enemies if e.is_alive]
    if not living_enemies:
        return None
    affordable = [c for c in available_cards if c.energy_cost <= caster.current_energy]
    if not affordable:
        return None
    card = min(affordable, key=lambda c: c.energy_cost)
    # Determine targets
    is_aoe = any(e.target == Target.ENEMY_ALL for e in card.effects)
    if is_aoe:
        targets = living_enemies
    else:
        targets = [min(living_enemies, key=lambda e: get_current_stat(e, Stat.HP))]
    return (card, targets)


def resolve_combat(
    party: list[CombatEntity],
    enemies: list[CombatEntity],
    cards_by_id: dict[str, Card] | None = None,
    region_modifiers: list[Modifier] | None = None,
    world_modifiers: list[Modifier] | None = None,
    player_strategy=None,
) -> CombatResult:
    """Execute a full combat encounter."""
    logs = []

    # Apply region and world modifiers
    all_entities = party + enemies
    for mod in (region_modifiers or []):
        living_allies = [e for e in all_entities if e.is_player]
        living_enemies = [e for e in all_entities if not e.is_player]
        if mod.target in (Target.ALLY_ALL, Target.GLOBAL):
            for e in living_allies:
                e.active_modifiers = apply_stacking(e.active_modifiers + [mod])
        if mod.target in (Target.ENEMY_ALL, Target.GLOBAL):
            for e in living_enemies:
                e.active_modifiers = apply_stacking(e.active_modifiers + [mod])
    for mod in (world_modifiers or []):
        for e in all_entities:
            e.active_modifiers = apply_stacking(e.active_modifiers + [mod])

    # Initialize current energy
    for e in all_entities:
        e.current_energy = get_current_stat(e, Stat.Energy)

    turns_taken = 0

    while True:
        # Check win/loss conditions
        living_party = [e for e in party if e.is_alive]
        living_enemies = [e for e in enemies if e.is_alive]

        if not living_enemies:
            return CombatResult(
                player_won=True,
                turns_taken=turns_taken,
                survivors=[e.id for e in living_party],
                combat_log=logs,
                final_state=all_entities,
            )
        if not living_party:
            return CombatResult(
                player_won=False,
                turns_taken=turns_taken,
                survivors=[],
                combat_log=logs,
                final_state=all_entities,
            )
        if turns_taken >= COMBAT_TURN_CAP:
            return CombatResult(
                player_won=False,
                turns_taken=turns_taken,
                survivors=[e.id for e in living_party],
                combat_log=logs,
                final_state=all_entities,
            )

        # Get next actor
        actor = tick_until_next_turn(all_entities)
        turn_logs = process_turn_start(actor)
        logs.extend(turn_logs)
        turns_taken += 1

        if not actor.is_alive:
            continue

        # Execute turn
        if actor.is_player:
            player_cards = []
            if cards_by_id and actor.card_pool:
                player_cards = [cards_by_id[cid] for cid in actor.card_pool if cid in cards_by_id]
            if player_strategy:
                living_allies = [e for e in party if e.is_alive]
                living_enemies_list = [e for e in enemies if e.is_alive]
                action = player_strategy.select_card(actor, player_cards, living_allies, living_enemies_list)
            else:
                action = _player_pick_card(actor, player_cards, enemies)
            if action:
                card, targets = action
                turn_logs = play_card(card, actor, targets, all_entities)
                logs.extend(turn_logs)
        else:
            # Enemy AI
            enemy_cards = []
            if cards_by_id and actor.card_pool:
                enemy_cards = [cards_by_id[cid] for cid in actor.card_pool if cid in cards_by_id]
            # Use enhanced enemy AI (v2) which falls back to greedy
            enemy_allies = [e for e in enemies if e.is_alive and e is not actor]
            action = pick_enemy_action_v2(actor, enemy_cards, party, enemy_allies, turns_taken)
            if action:
                card, targets = action
                turn_logs = play_card(card, actor, targets, all_entities)
                logs.extend(turn_logs)


def resolve_hazard(
    party: list[CombatEntity],
    hazard_modifiers: list[Modifier],
    hazard_duration: int,
    region_modifiers: list[Modifier] | None = None,
    world_modifiers: list[Modifier] | None = None,
) -> HazardResult:
    """Execute a hazard encounter."""
    logs = []
    damage_taken: dict[str, int] = {e.id: 0 for e in party}

    # Apply region/world modifiers
    for mod in (region_modifiers or []) + (world_modifiers or []):
        for e in party:
            e.active_modifiers = apply_stacking(e.active_modifiers + [mod])

    # Apply hazard for duration turns
    for turn in range(hazard_duration):
        for e in party:
            if not e.is_alive:
                continue
            for mod in hazard_modifiers:
                if mod.stat == Stat.HP and mod.operation == Operation.FLAT_SUB:
                    defense = get_current_stat(e, Stat.Defense)
                    damage = max(0, mod.value - defense)
                    e.base_stats[Stat.HP] -= damage
                    damage_taken[e.id] += damage
                    if e.base_stats[Stat.HP] <= 0:
                        e.is_alive = False
                        logs.append(f"{e.name} died to hazard")

    survived = any(e.is_alive for e in party)
    return HazardResult(
        survived=survived,
        damage_taken=damage_taken,
        combat_log=logs,
        final_state=party,
    )


def resolve_event(
    party: list[CombatEntity],
    choices: list[EventChoice],
    choice_index: int,
    region_modifiers: list[Modifier] | None = None,
    world_modifiers: list[Modifier] | None = None,
) -> EventResult:
    """Execute an event encounter."""
    logs = []
    choice = choices[choice_index]

    effects_applied = []
    costs_applied = []

    # Apply choice effects to party
    for mod in choice.effects:
        for e in party:
            e.active_modifiers = apply_stacking(e.active_modifiers + [mod])
        effects_applied.append(mod)

    # Apply costs to party
    for mod in choice.cost:
        if mod.stat == Stat.HP and mod.operation == Operation.FLAT_SUB:
            for e in party:
                e.base_stats[Stat.HP] -= mod.value
        else:
            for e in party:
                e.active_modifiers = apply_stacking(e.active_modifiers + [mod])
        costs_applied.append(mod)

    logs.append(f"Event choice {choice_index} applied: {choice.description}")

    return EventResult(
        choice_index=choice_index,
        effects_applied=effects_applied,
        costs_applied=costs_applied,
        combat_log=logs,
        final_state=party,
    )
