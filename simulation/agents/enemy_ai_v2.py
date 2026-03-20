"""Enhanced enemy AI with context-aware behavior based on ai_heuristic tag."""

from models.card import Card
from models.enums import Operation, Stat, Target, AiHeuristic
from engine.turn_order import CombatEntity, get_current_stat


def _is_buff_card(card: Card) -> bool:
    return any(
        e.operation in (Operation.FLAT_ADD, Operation.PCT_ADD)
        and e.target in (Target.SELF, Target.ALLY_SINGLE, Target.ALLY_ALL)
        for e in card.effects
    )


def _is_heal_card(card: Card) -> bool:
    return any(
        e.stat == Stat.HP and e.operation == Operation.FLAT_ADD
        for e in card.effects
    )


def _is_defense_buff(card: Card) -> bool:
    return any(
        e.stat == Stat.Defense and e.operation in (Operation.FLAT_ADD, Operation.PCT_ADD)
        for e in card.effects
    )


def _is_aoe_debuff(card: Card) -> bool:
    return any(
        e.target == Target.ENEMY_ALL
        and e.operation in (Operation.FLAT_SUB, Operation.PCT_SUB)
        and e.stat != Stat.HP
        for e in card.effects
    )


def _is_aoe_damage(card: Card) -> bool:
    return any(e.target == Target.ENEMY_ALL for e in card.effects)


def _damage_score(card: Card) -> int:
    return sum(
        e.value for e in card.effects
        if e.stat == Stat.HP and e.operation == Operation.FLAT_SUB
    )


def _affordable(enemy: CombatEntity, cards: list[Card]) -> list[Card]:
    return [c for c in cards if c.energy_cost <= enemy.current_energy]


def _greedy_pick(
    enemy: CombatEntity,
    affordable: list[Card],
    party: list[CombatEntity],
) -> tuple[Card, list[CombatEntity]] | None:
    """Fallback greedy: highest damage, lowest HP target."""
    living = [p for p in party if p.is_alive]
    if not living or not affordable:
        return None
    best = max(affordable, key=_damage_score)
    if _is_aoe_damage(best):
        return (best, living)
    target = min(living, key=lambda p: get_current_stat(p, Stat.HP))
    return (best, [target])


def pick_enemy_action_v2(
    enemy: CombatEntity,
    available_cards: list[Card],
    party: list[CombatEntity],
    allies: list[CombatEntity] | None = None,
    turn_number: int = 0,
) -> tuple[Card, list[CombatEntity]] | None:
    """Enhanced enemy AI with behavior modes based on ai_heuristic."""
    living_party = [p for p in party if p.is_alive]
    if not living_party:
        return None

    affordable = _affordable(enemy, available_cards)
    if not affordable:
        return None

    heuristic = enemy.ai_heuristic or AiHeuristic.aggressive

    if heuristic == AiHeuristic.aggressive:
        # Turn 1: play buff if available (setup combo)
        if turn_number <= 1:
            buffs = [c for c in affordable if _is_buff_card(c)]
            if buffs:
                return (buffs[0], [enemy])

        # Otherwise: highest damage, lowest HP target
        return _greedy_pick(enemy, affordable, party)

    elif heuristic == AiHeuristic.defensive:
        # If low HP, heal/defend
        current_hp = get_current_stat(enemy, Stat.HP)
        max_hp = enemy.base_stats.get(Stat.HP, current_hp)
        hp_pct = current_hp * 100 // max_hp if max_hp > 0 else 100

        if hp_pct < 50:
            heals = [c for c in affordable if _is_heal_card(c) or _is_defense_buff(c)]
            if heals:
                return (heals[0], [enemy])

        # Prefer defense buffs when outnumbered
        living_allies = [a for a in (allies or []) if a.is_alive]
        if len(living_party) > len(living_allies) + 1:
            def_cards = [c for c in affordable if _is_defense_buff(c)]
            if def_cards:
                return (def_cards[0], [enemy])

        return _greedy_pick(enemy, affordable, party)

    elif heuristic == AiHeuristic.balanced:
        # Turn 1: play buff/debuff if available
        if turn_number <= 1:
            setup = [c for c in affordable if _is_buff_card(c) or _is_aoe_debuff(c)]
            if setup:
                card = setup[0]
                if _is_buff_card(card):
                    return (card, [enemy])
                else:
                    return (card, living_party)

        # AoE debuff if 2+ targets alive
        if len(living_party) >= 2:
            aoe_debuffs = [c for c in affordable if _is_aoe_debuff(c)]
            if aoe_debuffs:
                return (aoe_debuffs[0], living_party)

        # AoE damage if 2+ targets
        if len(living_party) >= 2:
            aoe = [c for c in affordable if _is_aoe_damage(c)]
            if aoe:
                best = max(aoe, key=_damage_score)
                return (best, living_party)

        # Focus fire: target highest-Power low-HP party member
        for p in living_party:
            p_hp = get_current_stat(p, Stat.HP)
            p_max = p.base_stats.get(Stat.HP, p_hp)
            p_power = get_current_stat(p, Stat.Power)
            if p_max > 0 and p_hp * 100 // p_max < 60:
                # This is a wounded carry — focus it
                highest_power_wounded = max(
                    [pp for pp in living_party
                     if pp.base_stats.get(Stat.HP, 1) > 0
                     and get_current_stat(pp, Stat.HP) * 100 // pp.base_stats.get(Stat.HP, 1) < 60],
                    key=lambda pp: get_current_stat(pp, Stat.Power),
                    default=None,
                )
                if highest_power_wounded:
                    best = max(affordable, key=_damage_score)
                    return (best, [highest_power_wounded])
                break

        return _greedy_pick(enemy, affordable, party)

    # Fallback
    return _greedy_pick(enemy, affordable, party)
