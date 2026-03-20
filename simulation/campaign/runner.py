"""Campaign runner — executes a full campaign from seed to result."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Union

from models.entity import Character, Enemy
from models.modifier import Modifier, STAT_SCALE
from models.card import Card, UpgradeEntry
from models.campaign import (
    CombatEncounter,
    HazardEncounter,
    EventEncounter,
    Region,
    OutpostUpgrade,
)
from models.enums import Stat, Operation, Target, Stacking, AiHeuristic
from engine.turn_order import CombatEntity
from engine.encounters import (
    resolve_combat,
    resolve_hazard,
    resolve_event,
    CombatResult,
    HazardResult,
    EventResult,
)
from engine.stats import apply_stacking
from generation.characters import generate_character, FlavorData
from generation.regions import generate_region, _load_region_adjectives
from campaign.loader import GameData
from campaign.state import CampaignState, RegionState


@dataclass
class CampaignResult:
    """Output of a complete campaign run."""
    seed: int
    victory: bool
    regions_cleared: int
    total_turns: int
    final_roster: list[Character]
    world_cards_drawn: int
    world_cards_skipped: int
    resources_spent_on_research: int
    campaign_log: list[str]
    encounter_results: list[Union[CombatResult, HazardResult, EventResult]]


def character_to_combat_entity(
    character: Character,
    active_world_mods: list[Modifier],
    active_outpost_mods: list[Modifier],
) -> CombatEntity:
    """Convert a Character to a CombatEntity for combat resolution."""
    mods = [character.innate_passive] + list(active_world_mods) + list(active_outpost_mods)
    return CombatEntity(
        id=character.id,
        name=character.name,
        base_stats=dict(character.base_stats),
        active_modifiers=list(mods),
        is_player=True,
        card_pool=[],
    )


def enemy_data_to_combat_entity(
    enemy: Enemy,
    region_difficulty: int,
) -> CombatEntity:
    """Convert an Enemy to a CombatEntity for combat resolution."""
    return CombatEntity(
        id=enemy.id,
        name=enemy.name,
        base_stats=dict(enemy.base_stats),
        is_player=False,
        card_pool=list(enemy.card_pool),
        ai_heuristic=enemy.ai_heuristic_tag,
    )


def apply_card_upgrade(
    card: Card,
    branch_key: str,
    upgrade_trees: dict[str, dict[str, UpgradeEntry]],
) -> Card:
    """Apply an upgrade branch to a card. Returns new Card instance."""
    tree = upgrade_trees.get(card.id, {})
    entry = tree.get(branch_key)
    if entry is None:
        return card
    new_effects = list(card.effects) + list(entry.added_effects)
    return card.model_copy(update={
        "effects": new_effects,
        "upgrade_tier": card.upgrade_tier + 1,
    })


def pick_greedy_upgrade(
    roster_cards: list[str],
    upgrade_trees: dict[str, dict[str, UpgradeEntry]],
    applied_upgrades: dict[str, list[str]],
) -> tuple[str, str] | None:
    """Placeholder greedy upgrade selection."""
    best = None
    best_tier = -1
    for card_id in roster_cards:
        tree = upgrade_trees.get(card_id, {})
        already = applied_upgrades.get(card_id, [])
        for branch_key, entry in tree.items():
            if branch_key in already:
                continue
            # Check prerequisite
            if entry.prerequisite and entry.prerequisite not in already:
                continue
            # Check exclusions
            if any(ex in already for ex in entry.exclusions):
                continue
            if entry.tier > best_tier:
                best_tier = entry.tier
                best = (card_id, branch_key)
    return best


def _evaluate_world_card_net_impact(card_mods: list[Modifier]) -> int:
    """Placeholder: estimate net stat impact of modifiers. Positive = beneficial."""
    total = 0
    for mod in card_mods:
        if mod.operation in (Operation.FLAT_ADD, Operation.PCT_ADD):
            total += mod.value
        elif mod.operation in (Operation.FLAT_SUB, Operation.PCT_SUB):
            total -= mod.value
    return total


def run_campaign(seed: int, game_data: GameData, strategy=None) -> CampaignResult:
    """
    Execute one full campaign.
    If strategy is None, use placeholder heuristics (backward compatible with M2c).
    """
    rng = random.Random(seed)
    state = CampaignState(seed=seed, rng=rng)

    encounter_results: list[Union[CombatResult, HazardResult, EventResult]] = []
    total_turns = 0
    world_cards_drawn = 0
    world_cards_skipped = 0
    resources_spent = 0

    # Remaining world deck cards for this campaign
    remaining_world_deck = list(game_data.world_deck)

    # Region adjectives for generation
    region_adjectives = _load_region_adjectives()

    # Local copy of cards — avoids mutating game_data when upgrades are applied
    local_cards = dict(game_data.cards_by_id)

    # All base card IDs for player card pools
    all_card_ids = list(local_cards.keys())

    # Registry for generated enemies — populated during region generation
    enemy_registry: dict = {}

    # --- INIT ---
    # Generate 6 regions at difficulties 1-6
    for diff in range(1, 7):
        region = generate_region(rng, diff, all_card_ids, game_data.flavor, region_adjectives, enemy_registry, cards_by_id=local_cards)
        state.region_states.append(RegionState(
            region=region,
            assigned_difficulty=diff,
        ))

    # Start with 3 generated characters, pick the best (highest total stats)
    candidates = [generate_character(rng, game_data.generation_bounds, game_data.flavor) for _ in range(3)]
    best = max(candidates, key=lambda c: sum(c.base_stats.values()))
    state.roster.append(best)
    state.campaign_log.append(f"Starting character: {best.name}")

    # Reveal 1 random region at research level 1
    unrevealed = [rs for rs in state.region_states if rs.research_level == 0]
    if unrevealed:
        reveal = rng.choice(unrevealed)
        reveal.research_level = 1
        state.campaign_log.append(f"Free intel: {reveal.region.name} revealed to level 1")

    # --- MAIN LOOP ---
    while not state.game_over and not state.victory:
        # RESEARCH PHASE
        if strategy:
            while True:
                research_target = strategy.select_research(state, game_data)
                if research_target is None:
                    break
                if research_target.research_level >= 4:
                    break
                layer = research_target.region.research_layers[research_target.research_level]
                if state.resources < layer.cost:
                    break
                state.resources -= layer.cost
                resources_spent += layer.cost
                research_target.research_level += 1
                state.campaign_log.append(
                    f"Researched {research_target.region.name} to level {research_target.research_level} (cost {layer.cost})"
                )
        else:
            while True:
                best_research = None
                best_cost = None
                for rs in state.region_states:
                    if rs.research_level >= 4:
                        continue
                    next_layer = rs.region.research_layers[rs.research_level]
                    if state.resources >= next_layer.cost:
                        if best_cost is None or next_layer.cost < best_cost:
                            best_cost = next_layer.cost
                            best_research = rs
                if best_research is None:
                    break
                layer = best_research.region.research_layers[best_research.research_level]
                state.resources -= layer.cost
                resources_spent += layer.cost
                best_research.research_level += 1
                state.campaign_log.append(
                    f"Researched {best_research.region.name} to level {best_research.research_level} (cost {layer.cost})"
                )

        # REGION SELECTION
        unconquered = state.unconquered_regions
        if not unconquered:
            state.victory = True
            state.campaign_log.append("Victory! All 6 regions conquered.")
            break

        if strategy:
            target_rs = strategy.select_region(state, game_data)
        else:
            target_rs = min(unconquered, key=lambda rs: rs.assigned_difficulty)
        state.campaign_log.append(f"Assaulting {target_rs.region.name} (difficulty {target_rs.assigned_difficulty})")

        # Select party
        if strategy:
            party_chars = strategy.select_party(state, game_data, target_rs)
        else:
            party_chars = state.roster[:state.party_size]

        # Collect outpost modifier effects
        outpost_mods: list[Modifier] = []
        for upgrade in state.active_outpost_upgrades:
            outpost_mods.extend(upgrade.effects)

        # Create combat entities from party characters
        party_entities = [
            character_to_combat_entity(c, state.active_world_modifiers, outpost_mods)
            for c in party_chars
        ]
        # Set card pools to all base card IDs
        for pe in party_entities:
            pe.card_pool = all_card_ids

        region_wiped = False

        # ASSAULT: 3 encounters
        for enc in target_rs.region.encounters:
            if region_wiped:
                break

            if isinstance(enc, CombatEncounter):
                # Build enemy combat entities
                combat_enemies = []
                for enemy_id in enc.enemies:
                    if enemy_id in enemy_registry:
                        enemy = enemy_registry[enemy_id]
                    elif enemy_id in game_data.enemies_by_id:
                        enemy = game_data.enemies_by_id[enemy_id]
                    else:
                        enemy = Enemy(
                            id=enemy_id,
                            name=enemy_id.replace("_", " ").title(),
                            base_stats={s: 50 * STAT_SCALE for s in Stat},
                            card_pool=enc.enemy_cards[:2] if enc.enemy_cards else all_card_ids[:2],
                            ai_heuristic_tag=AiHeuristic.balanced,
                        )
                    combat_enemies.append(enemy_data_to_combat_entity(enemy, target_rs.assigned_difficulty))

                result = resolve_combat(
                    party=party_entities,
                    enemies=combat_enemies,
                    cards_by_id=local_cards,
                    region_modifiers=target_rs.region.modifier_stack,
                    player_strategy=strategy,
                )
                encounter_results.append(result)
                total_turns += result.turns_taken

                if not result.player_won:
                    state.game_over = True
                    region_wiped = True
                    state.campaign_log.append(f"Party wiped in combat at {enc.name}!")

                party_entities = [e for e in result.final_state if e.is_player and e.is_alive]
                if not party_entities:
                    state.game_over = True
                    region_wiped = True

            elif isinstance(enc, HazardEncounter):
                result = resolve_hazard(
                    party=party_entities,
                    hazard_modifiers=enc.hazard_modifiers,
                    hazard_duration=enc.hazard_duration,
                    region_modifiers=target_rs.region.modifier_stack,
                )
                encounter_results.append(result)

                if not result.survived:
                    state.game_over = True
                    region_wiped = True
                    state.campaign_log.append(f"Party wiped in hazard at {enc.name}!")

                party_entities = [e for e in result.final_state if e.is_alive]
                if not party_entities:
                    state.game_over = True
                    region_wiped = True

            elif isinstance(enc, EventEncounter):
                if strategy:
                    choice_idx = strategy.select_event_choice(enc.choices, state)
                else:
                    choice_idx = 0
                result = resolve_event(
                    party=party_entities,
                    choices=enc.choices,
                    choice_index=choice_idx,
                    region_modifiers=target_rs.region.modifier_stack,
                )
                encounter_results.append(result)
                party_entities = [e for e in result.final_state if e.is_alive]
                if not party_entities:
                    state.game_over = True
                    region_wiped = True

        if region_wiped:
            state.campaign_log.append("Campaign lost.")
            break

        # POST-CONQUEST
        target_rs.conquered = True
        state.turn_number += 1
        state.campaign_log.append(f"Conquered {target_rs.region.name}!")

        # Apply meta_reward directly to participating characters' base_stats
        meta = target_rs.region.meta_reward
        for char in party_chars:
            if meta.operation == Operation.FLAT_ADD:
                char.base_stats[meta.stat] = char.base_stats.get(meta.stat, 0) + meta.value
            elif meta.operation == Operation.FLAT_SUB:
                char.base_stats[meta.stat] = max(0, char.base_stats.get(meta.stat, 0) - meta.value)
            elif meta.operation == Operation.PCT_ADD:
                char.base_stats[meta.stat] = char.base_stats.get(meta.stat, 0) * (100 + meta.value) // 100
            elif meta.operation == Operation.PCT_SUB:
                char.base_stats[meta.stat] = char.base_stats.get(meta.stat, 0) * max(0, 100 - meta.value) // 100

        # Earn resources and skip tokens
        state.skip_tokens += 1
        state.resources += 50

        # Card upgrades
        for _ in range(state.party_size):
            if strategy:
                upgrade = strategy.select_card_upgrade(
                    all_card_ids, game_data.upgrade_trees, state.card_upgrades_applied, state
                )
            else:
                upgrade = pick_greedy_upgrade(all_card_ids, game_data.upgrade_trees, state.card_upgrades_applied)
            if upgrade:
                card_id, branch_key = upgrade
                if card_id not in state.card_upgrades_applied:
                    state.card_upgrades_applied[card_id] = []
                state.card_upgrades_applied[card_id].append(branch_key)
                if card_id in local_cards:
                    local_cards[card_id] = apply_card_upgrade(
                        local_cards[card_id], branch_key, game_data.upgrade_trees
                    )
                state.campaign_log.append(f"Applied upgrade {branch_key} to {card_id}")

        # Character draft
        draft_candidates = [
            generate_character(rng, game_data.generation_bounds, game_data.flavor)
            for _ in range(3)
        ]
        if strategy:
            drafted = strategy.select_drafted_character(draft_candidates, state)
        else:
            drafted = max(draft_candidates, key=lambda c: sum(c.base_stats.values()))
        state.roster.append(drafted)
        state.drafted_characters.append(drafted.id)
        state.campaign_log.append(f"Drafted: {drafted.name}")

        # WORLD PHASE: draw 3 cards
        rng.shuffle(remaining_world_deck)
        num_draw = min(3, len(remaining_world_deck))
        drawn = remaining_world_deck[:num_draw]
        remaining_world_deck = remaining_world_deck[num_draw:]

        for wc in drawn:
            world_cards_drawn += 1

            if strategy:
                accept = strategy.evaluate_world_card(wc, state, game_data)
            else:
                upside_impact = _evaluate_world_card_net_impact(wc.upside)
                downside_impact = _evaluate_world_card_net_impact(wc.downside)
                accept = (upside_impact + downside_impact) >= 0

            if accept:
                for mod in wc.upside + wc.downside:
                    state.active_world_modifiers.append(mod)
                state.campaign_log.append(f"Accepted world card: {wc.name}")
            else:
                if state.skip_tokens > 0:
                    state.skip_tokens -= 1
                    world_cards_skipped += 1
                    state.campaign_log.append(f"Skipped world card: {wc.name}")
                else:
                    for mod in wc.upside + wc.downside:
                        state.active_world_modifiers.append(mod)
                    state.campaign_log.append(f"Forced to accept world card: {wc.name}")

    return CampaignResult(
        seed=seed,
        victory=state.victory,
        regions_cleared=state.conquered_count,
        total_turns=total_turns,
        final_roster=state.roster,
        world_cards_drawn=world_cards_drawn,
        world_cards_skipped=world_cards_skipped,
        resources_spent_on_research=resources_spent,
        campaign_log=state.campaign_log,
        encounter_results=encounter_results,
    )
