from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

from models.modifier import Modifier

if TYPE_CHECKING:
    from engine.turn_order import CombatEntity

SPECIAL_TAG_SET = {"no_refresh_turn_2", "status_duration_multiply_2", "delayed_start_turn_2"}


@dataclass
class SpecialHandlerContext:
    entity: CombatEntity
    encounter_turn: int                       # 1-indexed turn number
    incoming_modifier: Modifier | None = None
    # Results written by handlers:
    suppress_energy_refresh: bool = False
    modified_incoming: Modifier | None = None
    modifiers_to_exclude: list[Modifier] = field(default_factory=list)
    modifiers_to_skip_decrement: list[Modifier] = field(default_factory=list)


def handle_no_refresh(ctx: SpecialHandlerContext) -> None:
    """
    no_refresh_turn_2: Energy does not refresh on Turn 2.
    - Turn 1: exclude modifier from energy calc (modifier hasn't fully kicked in), duration still decrements
    - Turn 2: suppress energy refresh (modifier fully active, Energy stays zeroed)
    - Turn 3+: modifier expired, no effect
    """
    no_refresh_mods = [m for m in ctx.entity.active_modifiers if "no_refresh_turn_2" in m.tags]
    if ctx.encounter_turn == 1:
        ctx.modifiers_to_exclude.extend(no_refresh_mods)
        # Duration still decrements — intentional so it expires after turn 2
    elif ctx.encounter_turn == 2:
        ctx.suppress_energy_refresh = True


def handle_duration_multiply(ctx: SpecialHandlerContext) -> None:
    """
    status_duration_multiply_2: When a new modifier is applied to this entity,
    double the incoming modifier's duration if duration > 0.
    Duration -1 (permanent) and 0 (instant) are unaffected.
    """
    if ctx.incoming_modifier is None:
        return
    m = ctx.incoming_modifier
    if m.duration > 0:
        ctx.modified_incoming = m.model_copy(update={"duration": m.duration * 2})
    else:
        ctx.modified_incoming = m


def handle_delayed_start(ctx: SpecialHandlerContext) -> None:
    """
    delayed_start_turn_2: Modifier (e.g. -50% Speed) is delayed until Turn 2.
    - Turn 1: exclude modifier from stat calc AND skip duration decrement
    - Turn 2+: modifier active, duration counts down normally
    """
    delayed_mods = [m for m in ctx.entity.active_modifiers if "delayed_start_turn_2" in m.tags]
    if ctx.encounter_turn == 1:
        ctx.modifiers_to_exclude.extend(delayed_mods)
        ctx.modifiers_to_skip_decrement.extend(delayed_mods)


SPECIAL_HANDLERS: dict[str, Callable] = {
    "no_refresh_turn_2": handle_no_refresh,
    "status_duration_multiply_2": handle_duration_multiply,
    "delayed_start_turn_2": handle_delayed_start,
}


def check_special_tags(modifier: Modifier) -> str | None:
    """Return the first resolver_special-associated tag found, or None."""
    for tag in modifier.tags:
        if tag in SPECIAL_TAG_SET:
            return tag
    return None


def apply_special_handler(tag: str, context: SpecialHandlerContext) -> None:
    """Look up and call the handler for a given tag."""
    handler = SPECIAL_HANDLERS.get(tag)
    if handler is not None:
        handler(context)
