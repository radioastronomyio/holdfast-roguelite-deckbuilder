import type { CombatEntity, Modifier } from "./types";

export const SPECIAL_TAG_SET = new Set(["no_refresh_turn_2", "status_duration_multiply_2", "delayed_start_turn_2"]);

export interface SpecialHandlerContext {
  entity: CombatEntity;
  encounter_turn: number;
  incoming_modifier?: Modifier | null;
  suppress_energy_refresh: boolean;
  modified_incoming?: Modifier | null;
  modifiers_to_exclude: Modifier[];
  modifiers_to_skip_decrement: Modifier[];
}

export function createSpecialHandlerContext(entity: CombatEntity, encounterTurn: number, incomingModifier?: Modifier): SpecialHandlerContext {
  return {
    entity,
    encounter_turn: encounterTurn,
    incoming_modifier: incomingModifier ?? null,
    suppress_energy_refresh: false,
    modified_incoming: null,
    modifiers_to_exclude: [],
    modifiers_to_skip_decrement: []
  };
}

export function handleNoRefresh(ctx: SpecialHandlerContext): void {
  const mods = ctx.entity.active_modifiers.filter((modifier) => modifier.tags.includes("no_refresh_turn_2"));
  if (ctx.encounter_turn === 1) {
    ctx.modifiers_to_exclude.push(...mods);
  } else if (ctx.encounter_turn === 2) {
    ctx.suppress_energy_refresh = true;
  }
}

export function handleDurationMultiply(ctx: SpecialHandlerContext): void {
  if (!ctx.incoming_modifier) return;
  ctx.modified_incoming = ctx.incoming_modifier.duration > 0
    ? { ...ctx.incoming_modifier, duration: ctx.incoming_modifier.duration * 2 }
    : { ...ctx.incoming_modifier };
}

export function handleDelayedStart(ctx: SpecialHandlerContext): void {
  const mods = ctx.entity.active_modifiers.filter((modifier) => modifier.tags.includes("delayed_start_turn_2"));
  if (ctx.encounter_turn === 1) {
    ctx.modifiers_to_exclude.push(...mods);
    ctx.modifiers_to_skip_decrement.push(...mods);
  }
}

export function checkSpecialTags(modifier: Modifier): string | null {
  // Python parity: the resolver dispatches the first special tag only.
  return modifier.tags.find((tag) => SPECIAL_TAG_SET.has(tag)) ?? null;
}

export function applySpecialHandler(tag: string, context: SpecialHandlerContext): void {
  if (tag === "no_refresh_turn_2") handleNoRefresh(context);
  if (tag === "status_duration_multiply_2") handleDurationMultiply(context);
  if (tag === "delayed_start_turn_2") handleDelayedStart(context);
}
