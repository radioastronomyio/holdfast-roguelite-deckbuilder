/** Data-to-visual mappings for card art motifs, palettes, and effect glyphs. */

import { Stat } from "../../sim/types";
import type { Modifier } from "../../sim/types";
import type { CardAccent } from "../gameui";

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

export interface CardVisual {
  motif: CardArtSymbol;
  palette: CardAccent;
}

const CARD_TAG_VISUAL: ReadonlyArray<readonly [string, CardVisual]> = [
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

export function resolveCardVisual(tags: readonly string[]): CardVisual {
  for (const [tag, visual] of CARD_TAG_VISUAL) {
    if (tags.includes(tag)) return visual;
  }
  return { motif: "crystal-ball", palette: "primary" };
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
