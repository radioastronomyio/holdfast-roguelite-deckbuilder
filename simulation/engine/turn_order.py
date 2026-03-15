from __future__ import annotations

import math
from dataclasses import dataclass, field

from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, AiHeuristic
from engine.stats import calculate_stat

CT_THRESHOLD = 100 * STAT_SCALE  # 100000


@dataclass
class CombatEntity:
    id: str
    name: str
    base_stats: dict[Stat, int]
    active_modifiers: list[Modifier] = field(default_factory=list)
    ct: int = 0
    is_player: bool = True
    card_pool: list[str] = field(default_factory=list)
    ai_heuristic: AiHeuristic | None = None
    is_alive: bool = True
    current_energy: int = 0  # refreshed each turn start


def get_current_stat(entity: CombatEntity, stat: Stat) -> int:
    return calculate_stat(entity.base_stats[stat], entity.active_modifiers, stat)


def tick_until_next_turn(entities: list[CombatEntity]) -> CombatEntity:
    """
    Advance CT for all living entities until one reaches CT_THRESHOLD.
    Tie-break: highest CT overflow, then highest Speed, then list position.
    """
    living = [e for e in entities if e.is_alive]
    if not living:
        raise ValueError("No living entities to tick")

    # Calculate ticks needed for each entity to reach threshold
    min_ticks = None
    for e in living:
        speed = get_current_stat(e, Stat.Speed)
        if speed <= 0:
            continue
        needed = max(0, CT_THRESHOLD - e.ct)
        ticks = math.ceil(needed / speed) if needed > 0 else 0
        if min_ticks is None or ticks < min_ticks:
            min_ticks = ticks

    if min_ticks is None:
        min_ticks = 0

    # Advance all living entities
    for e in living:
        speed = get_current_stat(e, Stat.Speed)
        e.ct += min_ticks * speed

    # Find ready entities (CT >= threshold)
    ready = [e for e in living if e.ct >= CT_THRESHOLD]
    if not ready:
        raise RuntimeError("No entity reached CT threshold")

    # Sort: highest overflow first, then highest speed, then list order
    ready.sort(key=lambda e: (-e.ct, -get_current_stat(e, Stat.Speed), entities.index(e)))

    actor = ready[0]
    actor.ct -= CT_THRESHOLD
    return actor


def process_turn_start(entity: CombatEntity, encounter_turn: int = 0) -> list[str]:
    """
    Called when entity's turn begins:
    1. Tick down durations on active_modifiers (duration > 0)
    2. Remove expired modifiers (duration == 0 after decrement)
    3. Check for death from effective HP <= 0
    4. Refresh Energy to calculated base
    Returns list of log messages.
    """
    logs = []

    # 1. Decrement durations for modifiers with duration > 0
    new_mods = []
    for m in entity.active_modifiers:
        if m.duration > 0:
            new_mod = m.model_copy(update={"duration": m.duration - 1})
            new_mods.append(new_mod)
        else:
            new_mods.append(m)
    entity.active_modifiers = new_mods

    # 2. Remove expired modifiers (duration == 0 after decrement; duration=-1 permanent stays)
    expired = [m for m in entity.active_modifiers if m.duration == 0]
    entity.active_modifiers = [m for m in entity.active_modifiers if m.duration != 0]
    if expired:
        logs.append(f"{entity.name}: {len(expired)} modifier(s) expired")

    # 3. Check death from DoT (effective HP <= 0)
    if entity.is_alive and get_current_stat(entity, Stat.HP) <= 0:
        entity.is_alive = False
        logs.append(f"{entity.name} has died")

    # 4. Refresh Energy
    entity.current_energy = get_current_stat(entity, Stat.Energy)

    return logs
