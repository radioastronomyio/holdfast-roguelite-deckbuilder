import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import baseCardsJson from "../../../../data/cards/base-cards.json";
import hazardCardsJson from "../../../../data/cards/hazard-cards.json";
import type { Card, Modifier } from "../../sim/types";
import {
  CARD_VISUAL_IDS,
  CARD_ART_SYMBOLS,
  cardIconUrl,
  resolveCardVisual,
  resolveEffectSymbol,
} from "./cardMap";

const cards = [
  ...(baseCardsJson as unknown as Card[]),
  ...(hazardCardsJson as unknown as Card[]),
];

const expectedMotifs: Readonly<Record<string, string>> = {
  arcane_strike_01: "arcane_burst",
  immolate_01: "fireball",
  shield_bash_01: "tower_shield",
  sweeping_blade_01: "crescent_blade",
  phalanx_01: "barrier_spell",
  adrenaline_01: "swift_boots",
  cleanse_01: "holy_ray",
  deep_focus_01: "mana_orb",
  acid_flask_01: "black_bomb",
  frost_bolt_01: "frostbite",
  power_surge_01: "rage_surge",
  stone_wall_01: "stone_spike",
  lightning_chain_01: "thunder_arc",
  heal_potion_01: "health_potion",
  drain_life_01: "life_drain",
  tripwire_hazard_01: "root_snare",
  miasma_hazard_01: "tidal_surge",
  toxic_fumes_hazard_01: "poison_cloud",
  freezing_wind_hazard_01: "wind_cut",
  crushing_weight_hazard_01: "rune_hammer",
  blinding_light_hazard_01: "warning",
};

const expectedRunicIcons = [
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

describe("card visual mappings", () => {
  it("maps every base and hazard card to a curated motif, palette, and tag-derived ground", () => {
    expect(cards).toHaveLength(21);
    for (const card of cards) {
      const visual = resolveCardVisual(card);
      expect(CARD_ART_SYMBOLS, card.id).toContain(visual.motif);
      expect(visual.palette, card.id).toMatch(/^(primary|success|warning|danger|info|magic|pink)$/);
      expect(visual.ground, card.id).toMatch(/^(arcane|ash|ice|marsh|ruin|stone|thicket)$/);
    }
  });

  it("locks the visual rows to exactly the current JSON card IDs", () => {
    expect([...CARD_VISUAL_IDS].sort()).toEqual(cards.map((card) => card.id).sort());
  });

  it("maps every card identity to its literal Runic Relic-derived motif", () => {
    for (const card of cards) {
      expect(resolveCardVisual(card).motif, card.id).toBe(expectedMotifs[card.id]);
    }
  });

  it("fails loudly when a card ID has no explicit visual row", () => {
    expect(() => resolveCardVisual({ id: "unknown_card_01", tags: ["attack"] } as Card)).toThrow(
      /Unmapped card visual: id=unknown_card_01/,
    );
  });

  it("gives Arcane Strike, Immolate, and Shield Bash distinct scene axes", () => {
    const byId = Object.fromEntries(cards.map((card) => [card.id, card]));
    const arcaneStrike = resolveCardVisual(byId.arcane_strike_01!);
    const immolate = resolveCardVisual(byId.immolate_01!);
    const shieldBash = resolveCardVisual(byId.shield_bash_01!);

    expect(new Set([arcaneStrike.palette, immolate.palette, shieldBash.palette]).size).toBe(3);
    expect(new Set([arcaneStrike.ground, immolate.ground, shieldBash.ground]).size).toBe(3);
    expect(new Set([arcaneStrike.motif, immolate.motif, shieldBash.motif]).size).toBe(3);
  });

  it("maps every real modifier to a curated effect symbol", () => {
    for (const card of cards) {
      for (const effect of card.effects) {
        expect(CARD_ART_SYMBOLS, `${card.id}: ${effect.stat}`).toContain(
          resolveEffectSymbol(effect),
        );
      }
    }
  });

  it("fails loudly when neither effect tags nor stat have a symbol mapping", () => {
    const unmapped = {
      stat: "Fortune",
      operation: "FLAT_ADD",
      value: 1,
      duration: 0,
      target: "SELF",
      stacking: "stack",
      tags: ["unmapped"],
    } as unknown as Modifier;

    expect(() => resolveEffectSymbol(unmapped)).toThrow(/Unmapped card effect/);
  });

  it("rejects unknown non-empty effect tags even when the stat is known", () => {
    const unknownTaggedHp = {
      stat: "HP",
      operation: "FLAT_ADD",
      value: 1,
      duration: 0,
      target: "SELF",
      stacking: "stack",
      tags: ["unmapped"],
    } as unknown as Modifier;

    expect(() => resolveEffectSymbol(unknownTaggedHp)).toThrow(
      /Unmapped card effect: stat=HP tags=unmapped/,
    );
  });

  it("uses a stat fallback only for a tagless effect", () => {
    const taglessHp = {
      stat: "HP",
      operation: "FLAT_ADD",
      value: 1,
      duration: 0,
      target: "SELF",
      stacking: "stack",
      tags: [],
    } as unknown as Modifier;

    expect(resolveEffectSymbol(taglessHp)).toBe("healing_light");
  });

  it("builds stable SVG and future PNG URLs under the Runic card-icon path", () => {
    expect(cardIconUrl("arcane_burst", "svg")).toBe(
      "/assets/card-icons/arcane_burst.svg",
    );
    expect(cardIconUrl("arcane_burst", "png")).toBe(
      "/assets/card-icons/arcane_burst.png",
    );
  });

  it("ships the exact derived Runic vocabulary with provenance and license facts", () => {
    const assetRoot = resolve(process.cwd(), "assets/card-icons");
    expect([...CARD_ART_SYMBOLS].sort()).toEqual([...expectedRunicIcons].sort());
    for (const icon of expectedRunicIcons) {
      expect(existsSync(resolve(assetRoot, `${icon}.svg`)), icon).toBe(true);
    }

    const manifest = JSON.parse(readFileSync(resolve(assetRoot, "manifest.json"), "utf8")) as {
      assets: Array<{ id: string; mode: string; source: string; file: string }>;
    };
    expect(manifest.assets.map(({ id }) => id).sort()).toEqual([...expectedRunicIcons].sort());
    expect(manifest.assets.every(({ mode, source, file }) => (
      mode.length > 0 && source.startsWith("assets/svg/") && file.endsWith(".svg")
    ))).toBe(true);

    const notice = readFileSync(resolve(assetRoot, "NOTICE"), "utf8");
    expect(notice).toContain("Template Foundry");
    expect(notice).toContain("Runic Relic RPG Icons 144");
    expect(notice).toContain("Royalty-free asset license for the purchaser");
  });

  it("uses the card identity as a variety axis within one tag family", () => {
    expect(resolveCardVisual({ id: "sweeping_blade_01", tags: ["attack", "physical"] } as Card)).not.toEqual(
      resolveCardVisual({ id: "shield_bash_01", tags: ["attack", "physical", "control"] } as Card),
    );
  });
});
