/**
 * RETIRED BY SPEC 06: preserved for provenance; no longer imported or built.
 *
 * Tag/stat → icon and card-tag → accent resolution maps.
 *
 * The card renderer is data-driven: every modifier resolves to one icon and
 * every card resolves to one accent through these maps, so adding a card to the
 * JSON is the only step required to render it. Two concerns are separated here:
 *
 *   1. `resolveEffectIcon(modifier)` — a per-effect-row icon, keyed by the
 *      modifier's tags (in a fixed precedence order) with a fallback to the
 *      modified stat, then a documented default.
 *   2. `accentForCard(tags)` — a per-card accent role, keyed by the card's type
 *      tags (in a fixed precedence order) with a documented default.
 *
 * Icon filenames are the clean kebab names produced by prepare-public.mjs; the
 * icon pack's source quirks (doubled `.png.png`, the `ui-watrer-drop` typo) are
 * normalized away at staging time, so lookups here are always deterministic.
 *
 * Card JSON effect values are at display scale; this module deals only in
 * labels and asset paths, never in scaled numerics.
 *
 * @module ui/cards/iconMap
 */

import { Stat } from "../../sim/types";
import type { CardAccent } from "../gameui";
import type { Modifier } from "../../sim/types";

/** Base URL prefix for staged card icons (relative to the document). */
export const ICON_BASE = `${import.meta.env.BASE_URL}assets/icons/`;

/** Icon returned when no tag or stat matches. */
export const FALLBACK_ICON = "icon-unknown.png";

/**
 * Effect-tag → icon filename. A modifier may carry several tags; the first tag
 * (in TAG_ICON_PRECEDENCE order) present on the modifier wins, so the most
 * visually distinctive tag determines the row icon (e.g. a `slow` effect shows
 * the snowflake even when also tagged `debuff`).
 */
const TAG_ICON: Record<string, string> = {
  fire: "icon-fire.png",
  lightning: "icon-lightning.png",
  ice: "icon-snowflake.png",
  cold: "icon-snowflake.png",
  poison: "icon-poison.png",
  bleed: "icon-bleed.png",
  lifesteal: "icon-heal.png",
  stun: "icon-stun.png",
  slow: "icon-snowflake.png",
  shred: "icon-shred.png",
  dot: "icon-dot.png",
  aoe: "icon-aoe.png",
  heal: "icon-heal.png",
  regen: "icon-heal.png",
  buff: "icon-buff.png",
  attack: "icon-attack.png",
  physical: "icon-physical.png",
  defense: "icon-defense.png",
  magic: "icon-magic.png",
  dark: "icon-dark.png",
  control: "icon-control.png",
  weaken: "icon-weaken.png",
  debuff: "icon-weaken.png",
  blind: "icon-blind.png",
  energy: "icon-energy.png",
  power: "icon-lightning.png",
  speed: "icon-speed.png",
  utility: "icon-utility.png",
  hazard: "icon-hazard.png",
  trap: "icon-hazard.png",
  pressure: "icon-control.png",
  party: "icon-party.png",
};

/**
 * Order in which an effect's tags are considered for icon resolution, most
 * distinctive first. Tags not listed here never win (they fall through to the
 * stat fallback), which keeps incidental tags from overriding the icon.
 */
const TAG_ICON_PRECEDENCE = [
  "fire", "lightning", "ice", "cold", "poison", "bleed", "lifesteal", "stun",
  "slow", "shred", "dot", "aoe", "heal", "regen", "buff", "attack", "physical",
  "defense", "magic", "dark", "control", "weaken", "debuff", "blind", "energy",
  "power", "speed", "utility", "hazard", "trap", "pressure", "party",
];

/** Fallback icon when no effect tag matches, keyed by the modified stat. */
const STAT_ICON: Record<Stat, string> = {
  [Stat.HP]: "icon-heal.png",
  [Stat.Power]: "icon-lightning.png",
  [Stat.Speed]: "icon-speed.png",
  [Stat.Defense]: "icon-defense.png",
  [Stat.Energy]: "icon-energy.png",
};

/**
 * Resolve the icon filename (bare name, no path) for a single modifier: the
 * highest-precedence mapped tag wins, else the stat fallback, else the default.
 */
export function resolveEffectIcon(modifier: Modifier): string {
  for (const tag of modifier.tags) {
    if (TAG_ICON_PRECEDENCE.includes(tag) && TAG_ICON[tag]) {
      return TAG_ICON[tag];
    }
  }
  return STAT_ICON[modifier.stat] ?? FALLBACK_ICON;
}

/** Full URL for an icon filename, for use in `<img src>`. */
export function iconUrl(filename: string): string {
  return `${ICON_BASE}${filename}`;
}

/**
 * Card-level type-tag → accent role. The accent tints the whole card frame and
 * energy badge; it is the single signal for a card's role (attack, defense,
 * support, magic, disruption). Only these seven roles are mapped; everything
 * else falls back to the default accent.
 */
const TAG_ACCENT: Record<string, CardAccent> = {
  attack: "danger",
  defense: "info",
  buff: "success",
  heal: "success",
  magic: "magic",
  control: "warning",
  debuff: "warning",
};

/** Default accent when no mapped type tag is present on a card. */
export const DEFAULT_ACCENT: CardAccent = "primary";

/**
 * Precedence order for multi-tag accent resolution (highest first). A card that
 * carries both `attack` and `control` (e.g. Shield Bash) resolves to the
 * `attack` accent; a card that carries `buff` and `defense` (e.g. Phalanx)
 * resolves to the `defense` accent. Tags not in the accent map are ignored.
 */
const TAG_ACCENT_PRECEDENCE = [
  "attack", "magic", "control", "debuff", "defense", "heal", "buff",
];

/**
 * Resolve a card's accent from its type tags. The highest-precedence mapped tag
 * wins; if none of the card's tags are in the accent map, the default accent is
 * returned.
 */
export function accentForCard(tags: string[]): CardAccent {
  for (const tag of TAG_ACCENT_PRECEDENCE) {
    if (tags.includes(tag)) return TAG_ACCENT[tag];
  }
  return DEFAULT_ACCENT;
}
