import { describe, expect, it } from "vitest";
import baseCardsJson from "../../../../data/cards/base-cards.json";
import hazardCardsJson from "../../../../data/cards/hazard-cards.json";
import type { Card, Modifier } from "../../sim/types";
import {
  CARD_ART_SYMBOLS,
  resolveCardVisual,
  resolveEffectSymbol,
} from "./cardMap";

const cards = [
  ...(baseCardsJson as unknown as Card[]),
  ...(hazardCardsJson as unknown as Card[]),
];

describe("card visual mappings", () => {
  it("maps every base and hazard card to a curated motif and palette", () => {
    expect(cards).toHaveLength(21);
    for (const card of cards) {
      const visual = resolveCardVisual(card.tags);
      expect(CARD_ART_SYMBOLS, card.id).toContain(visual.motif);
      expect(visual.palette, card.id).toMatch(/^(primary|success|warning|danger|info|magic|pink)$/);
    }
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

  it("uses card tags as the visual discriminator", () => {
    expect(resolveCardVisual(["attack", "physical"])).not.toEqual(
      resolveCardVisual(["ice", "control"]),
    );
  });
});
