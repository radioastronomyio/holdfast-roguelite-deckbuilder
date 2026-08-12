/** Data-to-visual mappings for card art motifs, palettes, and effect glyphs. */

import { Stat } from "../../sim/types";
import type { Modifier } from "../../sim/types";
import type { CardAccent } from "../gameui";
import type { Card } from "../../sim/types";

export const CARD_ART_SYMBOLS = [
  "arcane_burst",
  "barrier_spell",
  "black_bomb",
  "crescent_blade",
  "fireball",
  "frostbite",
  "healing_light",
  "health_potion",
  "holy_ray",
  "life_drain",
  "mana_orb",
  "poison_cloud",
  "rage_surge",
  "root_snare",
  "rune_hammer",
  "stone_spike",
  "swift_boots",
  "thunder_arc",
  "tidal_surge",
  "tower_shield",
  "warning",
  "wind_cut",
] as const;

export type CardArtSymbol = (typeof CARD_ART_SYMBOLS)[number];
export type CardIconFormat = "svg" | "png";
export const CARD_ART_GROUNDS = ["arcane", "ash", "ice", "marsh", "ruin", "stone", "thicket"] as const;
export type CardArtGround = (typeof CARD_ART_GROUNDS)[number];

export interface CardVisual {
  motif: CardArtSymbol;
  palette: CardAccent;
  ground: CardArtGround;
}

type CardMotifPalette = Pick<CardVisual, "motif" | "palette">;

/**
 * The scene's lead motif and palette are deliberately card-specific rather
 * than a tag-only lookup. This keeps mechanically adjacent cards readable as
 * distinct objects while leaving gameplay definitions in data/ untouched.
 */
const CARD_VISUAL_ROWS: Readonly<Record<string, CardMotifPalette>> = {
  arcane_strike_01: { motif: "arcane_burst", palette: "magic" },
  immolate_01: { motif: "fireball", palette: "danger" },
  shield_bash_01: { motif: "tower_shield", palette: "info" },
  sweeping_blade_01: { motif: "crescent_blade", palette: "danger" },
  phalanx_01: { motif: "barrier_spell", palette: "info" },
  adrenaline_01: { motif: "swift_boots", palette: "warning" },
  cleanse_01: { motif: "holy_ray", palette: "success" },
  deep_focus_01: { motif: "mana_orb", palette: "magic" },
  acid_flask_01: { motif: "black_bomb", palette: "success" },
  frost_bolt_01: { motif: "frostbite", palette: "info" },
  power_surge_01: { motif: "rage_surge", palette: "warning" },
  stone_wall_01: { motif: "stone_spike", palette: "info" },
  lightning_chain_01: { motif: "thunder_arc", palette: "warning" },
  heal_potion_01: { motif: "health_potion", palette: "success" },
  drain_life_01: { motif: "life_drain", palette: "magic" },
  tripwire_hazard_01: { motif: "root_snare", palette: "warning" },
  miasma_hazard_01: { motif: "tidal_surge", palette: "success" },
  toxic_fumes_hazard_01: { motif: "poison_cloud", palette: "success" },
  freezing_wind_hazard_01: { motif: "wind_cut", palette: "info" },
  crushing_weight_hazard_01: { motif: "rune_hammer", palette: "warning" },
  blinding_light_hazard_01: { motif: "warning", palette: "warning" },
};

/** Stable public inventory used to ensure the explicit visual rows cover JSON exactly. */
export const CARD_VISUAL_IDS = Object.freeze(Object.keys(CARD_VISUAL_ROWS));

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
  ["dot", "fireball"],
  ["lightning", "thunder_arc"],
  ["ice", "frostbite"],
  ["cold", "frostbite"],
  ["poison", "poison_cloud"],
  ["shred", "poison_cloud"],
  ["blind", "holy_ray"],
  ["dark", "life_drain"],
  ["lifesteal", "life_drain"],
  ["slow", "swift_boots"],
  ["speed", "swift_boots"],
  ["heal", "healing_light"],
  ["defense", "barrier_spell"],
  ["energy", "mana_orb"],
  ["power", "rage_surge"],
  ["aoe", "tidal_surge"],
  ["trap", "root_snare"],
  ["pressure", "rune_hammer"],
  ["magic", "arcane_burst"],
  ["control", "root_snare"],
  ["attack", "crescent_blade"],
  ["physical", "crescent_blade"],
  ["hazard", "warning"],
  ["debuff", "warning"],
  ["buff", "arcane_burst"],
  ["utility", "mana_orb"],
];

const STAT_SYMBOL: Partial<Record<Stat, CardArtSymbol>> = {
  [Stat.HP]: "healing_light",
  [Stat.Power]: "rage_surge",
  [Stat.Speed]: "swift_boots",
  [Stat.Defense]: "barrier_spell",
  [Stat.Energy]: "mana_orb",
};

export function resolveCardVisual(card: Pick<Card, "id" | "tags">): CardVisual {
  const motifPalette = CARD_VISUAL_ROWS[card.id];
  if (!motifPalette) {
    throw new Error(`Unmapped card visual: id=${card.id}`);
  }
  return { ...motifPalette, ground: resolveGround(card.tags) };
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
  if (modifier.tags.length === 0) {
    const symbol = STAT_SYMBOL[modifier.stat];
    if (symbol) return symbol;
  }
  throw new Error(
    `Unmapped card effect: stat=${String(modifier.stat)} tags=${modifier.tags.join(",")}`,
  );
}

export function cardIconUrl(symbol: CardArtSymbol, format: CardIconFormat): string {
  return `${import.meta.env.BASE_URL}assets/card-icons/${symbol}.${format}`;
}
