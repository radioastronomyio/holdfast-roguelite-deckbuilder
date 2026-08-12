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
export const RUNIC_ICON_MODES = Object.freeze({
  arcane_burst: "rune",
  barrier_spell: "barrier",
  black_bomb: "bomb",
  crescent_blade: "sword",
  fireball: "flame",
  frostbite: "frost",
  healing_light: "heart",
  health_potion: "potion",
  holy_ray: "sun",
  life_drain: "skull",
  mana_orb: "gem",
  poison_cloud: "poison",
  rage_surge: "claw",
  root_snare: "root",
  rune_hammer: "hammer",
  stone_spike: "earth",
  swift_boots: "boots",
  thunder_arc: "bolt",
  tidal_surge: "wave",
  tower_shield: "shield",
  warning: "warning",
  wind_cut: "wind",
} as const satisfies Readonly<Record<CardArtSymbol, string>>);
export type RunicIconMode = (typeof RUNIC_ICON_MODES)[CardArtSymbol];
export type CardIconFormat = "svg" | "png";
export type CardArtSource = "svg" | "image";
export const CARD_ART_GROUNDS = ["arcane", "ash", "ice", "marsh", "ruin", "stone", "thicket"] as const;
export type CardArtGround = (typeof CARD_ART_GROUNDS)[number];

export interface CardVisual {
  motif: CardArtSymbol;
  palette: CardAccent;
  ground: CardArtGround;
  artSource: CardArtSource;
}

type CardMotifPalette = Pick<CardVisual, "motif" | "palette"> &
  Partial<Pick<CardVisual, "artSource">>;

/** Select an icon only when its committed Runic mode matches the semantic role. */
function modeBackedIcon(mode: RunicIconMode, symbol: CardArtSymbol): CardArtSymbol {
  const actualMode = RUNIC_ICON_MODES[symbol];
  if (actualMode !== mode) {
    throw new Error(
      `Runic icon mode mismatch: symbol=${symbol} expected=${mode} actual=${actualMode}`,
    );
  }
  return symbol;
}

/**
 * The scene's lead motif and palette are deliberately card-specific rather
 * than a tag-only lookup. This keeps mechanically adjacent cards readable as
 * distinct objects while leaving gameplay definitions in data/ untouched.
 */
const CARD_VISUAL_ROWS: Readonly<Record<string, CardMotifPalette>> = {
  arcane_strike_01: { motif: modeBackedIcon("rune", "arcane_burst"), palette: "magic" },
  immolate_01: {
    motif: modeBackedIcon("flame", "fireball"),
    palette: "danger",
    artSource: "image",
  },
  shield_bash_01: { motif: modeBackedIcon("shield", "tower_shield"), palette: "info" },
  sweeping_blade_01: { motif: modeBackedIcon("sword", "crescent_blade"), palette: "danger" },
  phalanx_01: { motif: modeBackedIcon("barrier", "barrier_spell"), palette: "info" },
  adrenaline_01: { motif: modeBackedIcon("boots", "swift_boots"), palette: "warning" },
  cleanse_01: { motif: modeBackedIcon("sun", "holy_ray"), palette: "success" },
  deep_focus_01: { motif: modeBackedIcon("gem", "mana_orb"), palette: "magic" },
  acid_flask_01: { motif: modeBackedIcon("bomb", "black_bomb"), palette: "success" },
  frost_bolt_01: { motif: modeBackedIcon("frost", "frostbite"), palette: "info" },
  power_surge_01: { motif: modeBackedIcon("claw", "rage_surge"), palette: "warning" },
  stone_wall_01: { motif: modeBackedIcon("earth", "stone_spike"), palette: "info" },
  lightning_chain_01: { motif: modeBackedIcon("bolt", "thunder_arc"), palette: "warning" },
  heal_potion_01: { motif: modeBackedIcon("potion", "health_potion"), palette: "success" },
  drain_life_01: { motif: modeBackedIcon("skull", "life_drain"), palette: "magic" },
  tripwire_hazard_01: { motif: modeBackedIcon("root", "root_snare"), palette: "warning" },
  miasma_hazard_01: { motif: modeBackedIcon("wave", "tidal_surge"), palette: "success" },
  toxic_fumes_hazard_01: { motif: modeBackedIcon("poison", "poison_cloud"), palette: "success" },
  freezing_wind_hazard_01: { motif: modeBackedIcon("wind", "wind_cut"), palette: "info" },
  crushing_weight_hazard_01: { motif: modeBackedIcon("hammer", "rune_hammer"), palette: "warning" },
  blinding_light_hazard_01: { motif: modeBackedIcon("warning", "warning"), palette: "warning" },
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
  ["fire", modeBackedIcon("flame", "fireball")],
  ["dot", modeBackedIcon("flame", "fireball")],
  ["lightning", modeBackedIcon("bolt", "thunder_arc")],
  ["ice", modeBackedIcon("frost", "frostbite")],
  ["cold", modeBackedIcon("frost", "frostbite")],
  ["poison", modeBackedIcon("poison", "poison_cloud")],
  ["shred", modeBackedIcon("poison", "poison_cloud")],
  ["blind", modeBackedIcon("sun", "holy_ray")],
  ["dark", modeBackedIcon("skull", "life_drain")],
  ["lifesteal", modeBackedIcon("skull", "life_drain")],
  ["bleed", modeBackedIcon("claw", "rage_surge")],
  ["slow", modeBackedIcon("boots", "swift_boots")],
  ["speed", modeBackedIcon("boots", "swift_boots")],
  ["heal", modeBackedIcon("heart", "healing_light")],
  ["regen", modeBackedIcon("heart", "healing_light")],
  ["defense", modeBackedIcon("barrier", "barrier_spell")],
  ["party", modeBackedIcon("barrier", "barrier_spell")],
  ["energy", modeBackedIcon("gem", "mana_orb")],
  ["power", modeBackedIcon("claw", "rage_surge")],
  ["aoe", modeBackedIcon("wave", "tidal_surge")],
  ["trap", modeBackedIcon("root", "root_snare")],
  ["stun", modeBackedIcon("root", "root_snare")],
  ["pressure", modeBackedIcon("hammer", "rune_hammer")],
  ["magic", modeBackedIcon("rune", "arcane_burst")],
  ["control", modeBackedIcon("root", "root_snare")],
  ["attack", modeBackedIcon("sword", "crescent_blade")],
  ["physical", modeBackedIcon("sword", "crescent_blade")],
  ["hazard", modeBackedIcon("warning", "warning")],
  ["debuff", modeBackedIcon("warning", "warning")],
  ["weaken", modeBackedIcon("warning", "warning")],
  ["buff", modeBackedIcon("rune", "arcane_burst")],
  ["utility", modeBackedIcon("gem", "mana_orb")],
];

const STAT_SYMBOL: Partial<Record<Stat, CardArtSymbol>> = {
  [Stat.HP]: modeBackedIcon("heart", "healing_light"),
  [Stat.Power]: modeBackedIcon("claw", "rage_surge"),
  [Stat.Speed]: modeBackedIcon("boots", "swift_boots"),
  [Stat.Defense]: modeBackedIcon("barrier", "barrier_spell"),
  [Stat.Energy]: modeBackedIcon("gem", "mana_orb"),
};

export function resolveCardVisual(card: Pick<Card, "id" | "tags">): CardVisual {
  const motifPalette = CARD_VISUAL_ROWS[card.id];
  if (!motifPalette) {
    throw new Error(`Unmapped card visual: id=${card.id}`);
  }
  return {
    ...motifPalette,
    artSource: motifPalette.artSource ?? "svg",
    ground: resolveGround(card.tags),
  };
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

/** Presentation-owned raster motifs. Add an entry before opting a card into image art. */
const CARD_IMAGE_ART_ASSET: Partial<Record<CardArtSymbol, string>> = {
  fireball: "immolate-fireball",
};

/** Resolve the motif URL selected by the presentation map, never card JSON or factory options. */
export function cardArtUrl(motif: CardArtSymbol, artSource: CardArtSource): string {
  if (artSource === "svg") return cardIconUrl(motif, "svg");

  const asset = CARD_IMAGE_ART_ASSET[motif];
  if (!asset) throw new Error(`Unmapped raster card art: motif=${motif}`);
  return `${import.meta.env.BASE_URL}assets/card-icons/${asset}.png`;
}
