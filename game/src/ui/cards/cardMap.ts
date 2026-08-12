/** Data-to-visual mappings for card art motifs, palettes, and effect glyphs. */

import { Stat } from "../../sim/types";
import type { Modifier } from "../../sim/types";
import type { CardAccent } from "../gameui";
import type { Card } from "../../sim/types";

export const CARD_ART_SYMBOLS = [
  "acid-blob",
  "bleeding-eye",
  "bordered-shield",
  "crossed-swords",
  "crystal-ball",
  "dread-skull",
  "fast-arrow",
  "fireball",
  "focused-lightning",
  "heart-bottle",
  "ice-bolt",
  "magic-swirl",
  "mantrap",
  "pentarrows-tornado",
] as const;

export type CardArtSymbol = (typeof CARD_ART_SYMBOLS)[number];
export const CARD_ART_GROUNDS = ["arcane", "ash", "ice", "marsh", "ruin", "stone", "thicket"] as const;
export type CardArtGround = (typeof CARD_ART_GROUNDS)[number];

export interface CardVisual {
  motif: CardArtSymbol;
  palette: CardAccent;
  ground: CardArtGround;
}

type CardMotifPalette = Pick<CardVisual, "motif" | "palette">;

const CARD_TAG_VISUAL: ReadonlyArray<readonly [string, CardMotifPalette]> = [
  ["fire", { motif: "fireball", palette: "danger" }],
  ["lightning", { motif: "focused-lightning", palette: "warning" }],
  ["ice", { motif: "ice-bolt", palette: "info" }],
  ["cold", { motif: "ice-bolt", palette: "info" }],
  ["dark", { motif: "dread-skull", palette: "magic" }],
  ["lifesteal", { motif: "dread-skull", palette: "magic" }],
  ["poison", { motif: "acid-blob", palette: "success" }],
  ["shred", { motif: "acid-blob", palette: "success" }],
  ["blind", { motif: "bleeding-eye", palette: "warning" }],
  ["trap", { motif: "mantrap", palette: "warning" }],
  ["pressure", { motif: "mantrap", palette: "warning" }],
  ["hazard", { motif: "mantrap", palette: "warning" }],
  ["defense", { motif: "bordered-shield", palette: "info" }],
  ["heal", { motif: "heart-bottle", palette: "success" }],
  ["speed", { motif: "fast-arrow", palette: "warning" }],
  ["energy", { motif: "crystal-ball", palette: "magic" }],
  ["magic", { motif: "crystal-ball", palette: "magic" }],
  ["aoe", { motif: "pentarrows-tornado", palette: "danger" }],
  ["control", { motif: "magic-swirl", palette: "warning" }],
  ["debuff", { motif: "magic-swirl", palette: "warning" }],
  ["attack", { motif: "crossed-swords", palette: "danger" }],
  ["physical", { motif: "crossed-swords", palette: "danger" }],
  ["buff", { motif: "magic-swirl", palette: "success" }],
  ["utility", { motif: "crystal-ball", palette: "primary" }],
];

/**
 * The scene's lead motif and palette are deliberately card-specific rather
 * than a tag-only lookup. This keeps mechanically adjacent cards readable as
 * distinct objects while leaving gameplay definitions in data/ untouched.
 */
const CARD_VISUAL_ROWS: Readonly<Record<string, CardMotifPalette>> = {
  arcane_strike_01: { motif: "magic-swirl", palette: "magic" },
  immolate_01: { motif: "fireball", palette: "danger" },
  shield_bash_01: { motif: "bordered-shield", palette: "info" },
  sweeping_blade_01: { motif: "crossed-swords", palette: "danger" },
  phalanx_01: { motif: "bordered-shield", palette: "info" },
  adrenaline_01: { motif: "fast-arrow", palette: "warning" },
  cleanse_01: { motif: "heart-bottle", palette: "success" },
  deep_focus_01: { motif: "crystal-ball", palette: "magic" },
  acid_flask_01: { motif: "acid-blob", palette: "success" },
  frost_bolt_01: { motif: "ice-bolt", palette: "info" },
  power_surge_01: { motif: "focused-lightning", palette: "warning" },
  stone_wall_01: { motif: "bordered-shield", palette: "info" },
  lightning_chain_01: { motif: "focused-lightning", palette: "warning" },
  heal_potion_01: { motif: "heart-bottle", palette: "success" },
  drain_life_01: { motif: "dread-skull", palette: "magic" },
  tripwire_hazard_01: { motif: "mantrap", palette: "warning" },
  miasma_hazard_01: { motif: "acid-blob", palette: "success" },
  toxic_fumes_hazard_01: { motif: "acid-blob", palette: "success" },
  freezing_wind_hazard_01: { motif: "ice-bolt", palette: "info" },
  crushing_weight_hazard_01: { motif: "mantrap", palette: "warning" },
  blinding_light_hazard_01: { motif: "bleeding-eye", palette: "warning" },
};

/** Ground silhouettes are category-level scenery derived only from card tags. */
const CARD_TAG_GROUND: ReadonlyArray<readonly [string, CardArtGround]> = [
  ["fire", "ash"],
  ["ice", "ice"],
  ["cold", "ice"],
  ["poison", "marsh"],
  ["shred", "marsh"],
  ["magic", "arcane"],
  ["dark", "ruin"],
  ["lifesteal", "ruin"],
  ["defense", "stone"],
  ["physical", "stone"],
  ["trap", "thicket"],
  ["pressure", "stone"],
  ["blind", "ruin"],
  ["speed", "thicket"],
  ["heal", "thicket"],
  ["hazard", "ruin"],
];

const EFFECT_TAG_SYMBOL: ReadonlyArray<readonly [string, CardArtSymbol]> = [
  ["fire", "fireball"],
  ["lightning", "focused-lightning"],
  ["ice", "ice-bolt"],
  ["cold", "ice-bolt"],
  ["poison", "acid-blob"],
  ["shred", "acid-blob"],
  ["blind", "bleeding-eye"],
  ["dark", "dread-skull"],
  ["lifesteal", "dread-skull"],
  ["slow", "fast-arrow"],
  ["speed", "fast-arrow"],
  ["heal", "heart-bottle"],
  ["defense", "bordered-shield"],
  ["energy", "crystal-ball"],
  ["power", "focused-lightning"],
  ["aoe", "pentarrows-tornado"],
  ["trap", "mantrap"],
  ["pressure", "mantrap"],
  ["hazard", "mantrap"],
  ["control", "magic-swirl"],
  ["debuff", "magic-swirl"],
  ["attack", "crossed-swords"],
  ["physical", "crossed-swords"],
  ["buff", "magic-swirl"],
  ["utility", "crystal-ball"],
];

const STAT_SYMBOL: Partial<Record<Stat, CardArtSymbol>> = {
  [Stat.HP]: "heart-bottle",
  [Stat.Power]: "focused-lightning",
  [Stat.Speed]: "fast-arrow",
  [Stat.Defense]: "bordered-shield",
  [Stat.Energy]: "crystal-ball",
};

export function resolveCardVisual(card: Pick<Card, "id" | "tags">): CardVisual {
  const motifPalette = CARD_VISUAL_ROWS[card.id] ?? resolveTagVisual(card.tags);
  return { ...motifPalette, ground: resolveGround(card.tags) };
}

function resolveTagVisual(tags: readonly string[]): CardMotifPalette {
  for (const [tag, visual] of CARD_TAG_VISUAL) {
    if (tags.includes(tag)) return visual;
  }
  return { motif: "crystal-ball", palette: "primary" };
}

function resolveGround(tags: readonly string[]): CardArtGround {
  for (const [tag, ground] of CARD_TAG_GROUND) {
    if (tags.includes(tag)) return ground;
  }
  return "ruin";
}

export function resolveEffectSymbol(modifier: Modifier): CardArtSymbol {
  for (const [tag, symbol] of EFFECT_TAG_SYMBOL) {
    if (modifier.tags.includes(tag)) return symbol;
  }
  const symbol = STAT_SYMBOL[modifier.stat];
  if (symbol) return symbol;
  throw new Error(
    `Unmapped card effect: stat=${String(modifier.stat)} tags=${modifier.tags.join(",")}`,
  );
}

export function cardArtIconUrl(symbol: CardArtSymbol): string {
  return `${import.meta.env.BASE_URL}assets/card-art-icons/${symbol}.svg#icon`;
}
