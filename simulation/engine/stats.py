from collections import defaultdict

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Stacking


def apply_stacking(modifiers: list[Modifier]) -> list[Modifier]:
    """Collapse modifier list per stacking rules, grouped by (stat, operation)."""
    groups: dict[tuple, list[Modifier]] = defaultdict(list)
    for m in modifiers:
        groups[(m.stat, m.operation)].append(m)

    result = []
    for (stat, op), group in groups.items():
        stacking = group[-1].stacking  # use the last one's stacking rule
        if stacking == Stacking.stack:
            result.extend(group)
        elif stacking == Stacking.replace:
            result.append(group[-1])
        elif stacking == Stacking.max:
            result.append(max(group, key=lambda m: m.value))
    return result


def calculate_stat(base: int, modifiers: list[Modifier], stat: Stat = Stat.HP) -> int:
    """
    Resolve a single stat value from base + active modifiers.
    stat param: used to filter modifiers and determine floor-at-0 rule.
    Resolution: (base + flat_sum) * (100 + pct_sum) // 100, then sequential MULTIPLY.
    """
    # 1. Filter to matching stat
    stat_mods = [m for m in modifiers if m.stat == stat]

    # 2. Apply stacking rules
    stat_mods = apply_stacking(stat_mods)

    # 3. Sum FLAT_ADD and FLAT_SUB
    flat_sum = sum(m.value for m in stat_mods if m.operation == Operation.FLAT_ADD)
    flat_sum -= sum(m.value for m in stat_mods if m.operation == Operation.FLAT_SUB)

    # 4. Sum PCT_ADD and PCT_SUB
    pct_sum = sum(m.value for m in stat_mods if m.operation == Operation.PCT_ADD)
    pct_sum -= sum(m.value for m in stat_mods if m.operation == Operation.PCT_SUB)

    # 5. Apply flat+pct formula
    result = (base + flat_sum) * (100 + pct_sum) // 100

    # 6. Apply MULTIPLY modifiers sequentially
    for m in stat_mods:
        if m.operation == Operation.MULTIPLY:
            result = result * m.value // 1000

    # 7. Floor at 0 for non-HP stats (HP can be negative for death signal)
    if stat != Stat.HP:
        result = max(0, result)

    return result
