import { describe, expect, it } from "vitest";
import baseCardsJson from "../../../../data/cards/base-cards.json";
import hazardCardsJson from "../../../../data/cards/hazard-cards.json";
import type { Card, Modifier } from "../../sim/types";
import {
  CARD_VISUAL_IDS,
  CARD_ART_SYMBOLS,
  resolveCardVisual,
  resolveEffectSymbol,
} from "./cardMap";

const cards = [
  ...(baseCardsJson as unknown as Card[]),
  ...(hazardCardsJson as unknown as Card[]),
];

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

  it("uses the card identity as a variety axis within one tag family", () => {
    expect(resolveCardVisual({ id: "sweeping_blade_01", tags: ["attack", "physical"] } as Card)).not.toEqual(
      resolveCardVisual({ id: "shield_bash_01", tags: ["attack", "physical", "control"] } as Card),
    );
  });
});
