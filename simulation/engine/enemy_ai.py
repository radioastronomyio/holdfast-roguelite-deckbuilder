from models.card import Card
from models.enums import Operation, Stat, Target
from engine.turn_order import CombatEntity, get_current_stat


def pick_enemy_action(
    enemy: CombatEntity,
    available_cards: list[Card],
    party: list[CombatEntity],
) -> tuple[Card, list[CombatEntity]] | None:
    """
    Greedy enemy AI. Picks highest-damage affordable card,
    targets lowest-HP party member (or all party for AoE).
    """
    living_party = [p for p in party if p.is_alive]
    if not living_party:
        return None

    # Filter affordable cards
    affordable = [c for c in available_cards if c.energy_cost <= enemy.current_energy]
    if not affordable:
        return None

    # Score each card: sum of FLAT_SUB HP values
    def score(card: Card) -> int:
        return sum(
            e.value
            for e in card.effects
            if e.stat == Stat.HP and e.operation == Operation.FLAT_SUB
        )

    best_card = max(affordable, key=score)

    # Target selection: AoE vs single
    is_aoe = any(e.target == Target.ENEMY_ALL for e in best_card.effects)
    if is_aoe:
        targets = living_party
    else:
        targets = [min(living_party, key=lambda p: get_current_stat(p, Stat.HP))]

    return (best_card, targets)
