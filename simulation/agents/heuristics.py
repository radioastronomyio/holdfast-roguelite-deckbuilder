"""Three AI heuristics: AggressiveAI, DefensiveAI, BalancedAI."""

from __future__ import annotations

from models.entity import Character
from models.card import Card, UpgradeEntry
from models.campaign import WorldCard, EventChoice
from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target
from engine.turn_order import CombatEntity, get_current_stat
from campaign.state import CampaignState, RegionState
from campaign.loader import GameData


def _damage_score(card: Card) -> int:
    """Score a card by raw damage output."""
    return sum(
        e.value for e in card.effects
        if e.stat == Stat.HP and e.operation == Operation.FLAT_SUB
    )


def _is_healing_card(card: Card) -> bool:
    return any(
        e.stat == Stat.HP and e.operation == Operation.FLAT_ADD
        for e in card.effects
    )


def _is_defense_card(card: Card) -> bool:
    return any(
        e.stat == Stat.Defense and e.operation in (Operation.FLAT_ADD, Operation.PCT_ADD)
        for e in card.effects
    )


def _is_aoe(card: Card) -> bool:
    return any(e.target == Target.ENEMY_ALL for e in card.effects)


def _is_buff(card: Card) -> bool:
    return any(
        e.operation in (Operation.FLAT_ADD, Operation.PCT_ADD)
        and e.target in (Target.SELF, Target.ALLY_SINGLE, Target.ALLY_ALL)
        for e in card.effects
    )


def _is_debuff(card: Card) -> bool:
    return any(
        e.operation in (Operation.FLAT_SUB, Operation.PCT_SUB)
        and e.target in (Target.ENEMY_SINGLE, Target.ENEMY_ALL)
        and e.stat != Stat.HP  # Not a damage card
        for e in card.effects
    )


def _net_modifier_impact(mods: list[Modifier]) -> int:
    total = 0
    for m in mods:
        if m.operation in (Operation.FLAT_ADD, Operation.PCT_ADD):
            total += m.value
        elif m.operation in (Operation.FLAT_SUB, Operation.PCT_SUB):
            total -= m.value
    return total


def _pick_greedy_upgrade(
    roster_cards: list[str],
    upgrade_trees: dict[str, dict[str, UpgradeEntry]],
    applied_upgrades: dict[str, list[str]],
    prefer_stat: Stat | None = None,
) -> tuple[str, str] | None:
    """Generic upgrade picker with optional stat preference."""
    best = None
    best_score = -1
    for card_id in roster_cards:
        tree = upgrade_trees.get(card_id, {})
        already = applied_upgrades.get(card_id, [])
        for branch_key, entry in tree.items():
            if branch_key in already:
                continue
            if entry.prerequisite and entry.prerequisite not in already:
                continue
            if any(ex in already for ex in entry.exclusions):
                continue
            score = entry.tier
            if prefer_stat and any(
                e.stat == prefer_stat for e in entry.added_effects
            ):
                score += 10
            if score > best_score:
                best_score = score
                best = (card_id, branch_key)
    return best


def _affordable_cards(caster: CombatEntity, cards: list[Card]) -> list[Card]:
    return [c for c in cards if c.energy_cost <= caster.current_energy]


def _lowest_hp_enemy(enemies: list[CombatEntity]) -> CombatEntity:
    living = [e for e in enemies if e.is_alive]
    return min(living, key=lambda e: get_current_stat(e, Stat.HP))


def _target_for_card(card: Card, enemies: list[CombatEntity]) -> list[CombatEntity]:
    living = [e for e in enemies if e.is_alive]
    if not living:
        return []
    if _is_aoe(card):
        return living
    return [_lowest_hp_enemy(enemies)]


class AggressiveAI:
    """Aggressive strategy — maximize damage output, rush through campaign."""

    def select_region(self, state: CampaignState, game_data: GameData) -> RegionState:
        return min(state.unconquered_regions, key=lambda rs: rs.assigned_difficulty)

    def select_party(self, state: CampaignState, game_data: GameData, region: RegionState) -> list[Character]:
        sorted_roster = sorted(state.roster, key=lambda c: c.base_stats[Stat.Power], reverse=True)
        return sorted_roster[:state.party_size]

    def select_card(
        self,
        caster: CombatEntity,
        available_cards: list[Card],
        allies: list[CombatEntity],
        enemies: list[CombatEntity],
    ) -> tuple[Card, list[CombatEntity]] | None:
        living_enemies = [e for e in enemies if e.is_alive]
        if not living_enemies:
            return None
        affordable = _affordable_cards(caster, available_cards)
        if not affordable:
            return None
        best = max(affordable, key=_damage_score)
        return (best, _target_for_card(best, enemies))

    def evaluate_world_card(self, card: WorldCard, state: CampaignState, game_data: GameData) -> bool:
        # Reject if any modifier has a catastrophic ally FLAT_SUB (>= 50 display scale)
        ally_targets = (Target.SELF, Target.ALLY_SINGLE, Target.ALLY_ALL)
        for mod in card.upside + card.downside:
            if (
                mod.operation == Operation.FLAT_SUB
                and mod.value >= 50 * STAT_SCALE
                and mod.target in ally_targets
            ):
                return False
        # Accept if there's a beneficial Power or Speed mod targeting allies
        for mod in card.upside + card.downside:
            if (
                mod.stat in (Stat.Power, Stat.Speed)
                and mod.operation in (Operation.FLAT_ADD, Operation.PCT_ADD)
                and mod.target in ally_targets
            ):
                return True
        return False

    def select_event_choice(self, choices: list[EventChoice], state: CampaignState) -> int:
        # Pick choice with most offensive effect
        best_idx = 0
        best_score = -999999
        for i, choice in enumerate(choices):
            score = sum(
                e.value for e in choice.effects
                if e.stat == Stat.HP and e.operation == Operation.FLAT_SUB
            ) + sum(
                e.value for e in choice.effects
                if e.stat == Stat.Power and e.operation in (Operation.PCT_ADD, Operation.FLAT_ADD)
            )
            if score > best_score:
                best_score = score
                best_idx = i
        return best_idx

    def select_card_upgrade(
        self,
        roster_cards: list[str],
        upgrade_trees: dict[str, dict[str, UpgradeEntry]],
        applied_upgrades: dict[str, list[str]],
        state: CampaignState,
    ) -> tuple[str, str] | None:
        return _pick_greedy_upgrade(roster_cards, upgrade_trees, applied_upgrades, Stat.Power)

    def select_research(self, state: CampaignState, game_data: GameData) -> RegionState | None:
        return None  # Never research

    def select_drafted_character(self, candidates: list[Character], state: CampaignState) -> Character:
        return max(candidates, key=lambda c: c.base_stats[Stat.Power])


class DefensiveAI:
    """Defensive strategy — survive through attrition, maximize information."""

    def select_region(self, state: CampaignState, game_data: GameData) -> RegionState:
        unconquered = state.unconquered_regions
        # Always prefer lowest difficulty — research level breaks ties (more intel = better)
        # Bug fix: research level must not override difficulty ordering; free intel can point
        # to a high-difficulty region which would otherwise be assaulted first.
        return min(unconquered, key=lambda rs: (rs.assigned_difficulty, -rs.research_level))

    def select_party(self, state: CampaignState, game_data: GameData, region: RegionState) -> list[Character]:
        sorted_roster = sorted(
            state.roster,
            key=lambda c: c.base_stats[Stat.HP] + c.base_stats[Stat.Defense] * 5,
            reverse=True,
        )
        return sorted_roster[:state.party_size]

    def select_card(
        self,
        caster: CombatEntity,
        available_cards: list[Card],
        allies: list[CombatEntity],
        enemies: list[CombatEntity],
    ) -> tuple[Card, list[CombatEntity]] | None:
        living_enemies = [e for e in enemies if e.is_alive]
        living_allies = [a for a in allies if a.is_alive]
        if not living_enemies:
            return None
        affordable = _affordable_cards(caster, available_cards)
        if not affordable:
            return None

        # Heal only when critically low (< 30% HP) — healing above this is usually counterproductive
        current_hp = get_current_stat(caster, Stat.HP)
        max_hp = caster.base_stats.get(Stat.HP, current_hp)
        hp_ratio = current_hp * 100 // max_hp if max_hp > 0 else 100

        if hp_ratio < 30:
            heal_cards = [c for c in affordable if _is_healing_card(c)]
            if heal_cards:
                best_heal = max(heal_cards, key=lambda c: sum(
                    e.value for e in c.effects
                    if e.stat == Stat.HP and e.operation == Operation.FLAT_ADD
                ))
                lowest_ally = min(living_allies, key=lambda a: get_current_stat(a, Stat.HP))
                return (best_heal, [lowest_ally])

        # Attack the highest-Power enemy to eliminate the biggest damage threat first
        # This is the defensive goal: reduce incoming damage as fast as possible
        damage_cards = [c for c in affordable if _damage_score(c) > 0]
        if damage_cards:
            best = max(damage_cards, key=_damage_score)
            if _is_aoe(best):
                return (best, living_enemies)
            # Target highest Power enemy (most dangerous), not lowest HP
            highest_threat = max(living_enemies, key=lambda e: e.base_stats.get(Stat.Power, 0))
            return (best, [highest_threat])
        # No damage cards — apply support to self
        best = affordable[0]
        return (best, [caster])

    def evaluate_world_card(self, card: WorldCard, state: CampaignState, game_data: GameData) -> bool:
        # Reject if any modifier has a catastrophic ally FLAT_SUB (>= 50 display scale)
        ally_targets = (Target.SELF, Target.ALLY_SINGLE, Target.ALLY_ALL)
        for mod in card.upside + card.downside:
            if (
                mod.operation == Operation.FLAT_SUB
                and mod.value >= 50 * STAT_SCALE
                and mod.target in ally_targets
            ):
                return False
        # Accept if there's a beneficial HP or Defense mod targeting allies
        for mod in card.upside + card.downside:
            if (
                mod.stat in (Stat.HP, Stat.Defense)
                and mod.operation in (Operation.FLAT_ADD, Operation.PCT_ADD)
                and mod.target in ally_targets
            ):
                return True
        return False

    def select_event_choice(self, choices: list[EventChoice], state: CampaignState) -> int:
        # Lowest cost option
        best_idx = 0
        best_cost = 999999
        for i, choice in enumerate(choices):
            cost = sum(abs(m.value) for m in choice.cost)
            if cost < best_cost:
                best_cost = cost
                best_idx = i
        return best_idx

    def select_card_upgrade(
        self,
        roster_cards: list[str],
        upgrade_trees: dict[str, dict[str, UpgradeEntry]],
        applied_upgrades: dict[str, list[str]],
        state: CampaignState,
    ) -> tuple[str, str] | None:
        return _pick_greedy_upgrade(roster_cards, upgrade_trees, applied_upgrades, Stat.Defense)

    def select_research(self, state: CampaignState, game_data: GameData) -> RegionState | None:
        # Always research if resources available, cheapest layer first
        best = None
        best_cost = None
        for rs in state.region_states:
            if rs.research_level >= 4 or rs.conquered:
                continue
            layer = rs.region.research_layers[rs.research_level]
            if state.resources >= layer.cost:
                if best_cost is None or layer.cost < best_cost:
                    best_cost = layer.cost
                    best = rs
        return best

    def select_drafted_character(self, candidates: list[Character], state: CampaignState) -> Character:
        return max(candidates, key=lambda c: c.base_stats[Stat.HP])


class BalancedAI:
    """Balanced strategy — context-dependent scoring, moderate planning."""

    def select_region(self, state: CampaignState, game_data: GameData) -> RegionState:
        unconquered = state.unconquered_regions
        # Prefer regions researched to at least level 2
        well_researched = [rs for rs in unconquered if rs.research_level >= 2]
        if well_researched:
            return min(well_researched, key=lambda rs: rs.assigned_difficulty)
        return min(unconquered, key=lambda rs: rs.assigned_difficulty)

    def select_party(self, state: CampaignState, game_data: GameData, region: RegionState) -> list[Character]:
        # Score characters against region modifiers
        def score(c: Character) -> int:
            total = sum(c.base_stats.values())
            # Bonus for Defense in regions with FLAT_SUB or PCT_SUB modifiers
            for mod in region.region.modifier_stack:
                if mod.operation in (Operation.FLAT_SUB, Operation.PCT_SUB):
                    total += c.base_stats.get(Stat.Defense, 0)
            return total

        sorted_roster = sorted(state.roster, key=score, reverse=True)
        return sorted_roster[:state.party_size]

    def select_card(
        self,
        caster: CombatEntity,
        available_cards: list[Card],
        allies: list[CombatEntity],
        enemies: list[CombatEntity],
    ) -> tuple[Card, list[CombatEntity]] | None:
        living_enemies = [e for e in enemies if e.is_alive]
        living_allies = [a for a in allies if a.is_alive]
        if not living_enemies:
            return None
        affordable = _affordable_cards(caster, available_cards)
        if not affordable:
            return None

        # Score each card by situation
        def card_score(card: Card) -> int:
            score = _damage_score(card)
            energy = max(1, card.energy_cost)
            dpe = score // energy if score > 0 else 0

            # Low HP ally? Strongly weight healing cards
            for ally in living_allies:
                ally_hp = get_current_stat(ally, Stat.HP)
                ally_max = ally.base_stats.get(Stat.HP, ally_hp)
                if ally_max > 0 and ally_hp * 100 // ally_max < 40:
                    if _is_healing_card(card):
                        return 999999  # Always prioritize healing when ally critical
                    break

            # Multi-enemy? Weight AoE
            if len(living_enemies) > 2 and _is_aoe(card):
                return score * 2 + dpe

            # Single enemy (boss)? Weight high single-target
            if len(living_enemies) == 1 and not _is_aoe(card):
                return score * 2 + dpe

            return score + dpe

        best = max(affordable, key=card_score)

        # Targeting
        if _is_healing_card(best):
            lowest_ally = min(living_allies, key=lambda a: get_current_stat(a, Stat.HP))
            return (best, [lowest_ally])

        return (best, _target_for_card(best, enemies))

    def evaluate_world_card(self, card: WorldCard, state: CampaignState, game_data: GameData) -> bool:
        upside_score = _net_modifier_impact(card.upside)
        downside_score = _net_modifier_impact(card.downside)
        net = upside_score + downside_score
        # Accept if net positive by > 20% margin
        threshold = abs(upside_score) * 20 // 100 if upside_score > 0 else 0
        return net > threshold

    def select_event_choice(self, choices: list[EventChoice], state: CampaignState) -> int:
        # Score each choice by net modifier impact
        best_idx = 0
        best_score = -999999
        for i, choice in enumerate(choices):
            score = _net_modifier_impact(choice.effects) + _net_modifier_impact(choice.cost)
            if score > best_score:
                best_score = score
                best_idx = i
        return best_idx

    def select_card_upgrade(
        self,
        roster_cards: list[str],
        upgrade_trees: dict[str, dict[str, UpgradeEntry]],
        applied_upgrades: dict[str, list[str]],
        state: CampaignState,
    ) -> tuple[str, str] | None:
        # Alternate between offense and defense
        prefer = Stat.Power if state.turn_number % 2 == 0 else Stat.Defense
        return _pick_greedy_upgrade(roster_cards, upgrade_trees, applied_upgrades, prefer)

    def select_research(self, state: CampaignState, game_data: GameData) -> RegionState | None:
        # Research to level 2 before assault, cheapest first
        best = None
        best_cost = None
        for rs in state.region_states:
            if rs.research_level >= 2 or rs.conquered:
                continue
            layer = rs.region.research_layers[rs.research_level]
            if state.resources >= layer.cost:
                if best_cost is None or layer.cost < best_cost:
                    best_cost = layer.cost
                    best = rs
        return best

    def select_drafted_character(self, candidates: list[Character], state: CampaignState) -> Character:
        # Pick character whose highest stat fills a gap
        roster_stats = {}
        for stat in Stat:
            roster_stats[stat] = sum(c.base_stats[stat] for c in state.roster)
        weakest_stat = min(roster_stats, key=roster_stats.get)

        return max(candidates, key=lambda c: c.base_stats[weakest_stat])
