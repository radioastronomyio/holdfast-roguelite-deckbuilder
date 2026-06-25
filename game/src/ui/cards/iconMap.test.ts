/**
 * Coverage test for the icon + accent resolution maps.
 *
 * Asserts that every modifier across the base and hazard card sets resolves to
 * a real icon (never the fallback, never undefined) and every card resolves to
 * a defined accent. This is the Deliverable 1 "no effect or card resolves to
 * undefined" contract: adding a card or tag to the data without a mapping
 * fails this test.
 *
 * @module ui/cards/iconMap.test
 */

import { describe, expect, it } from "vitest";
import baseCards from "../../../../data/cards/base-cards.json";
import hazardCards from "../../../../data/cards/hazard-cards.json";
import type { Card, Modifier } from "../../sim/types";
import type { CardAccent } from "../gameui";
import { accentForCard, DEFAULT_ACCENT, FALLBACK_ICON, resolveEffectIcon } from "./iconMap";

const VALID_ACCENTS: CardAccent[] = [
  "primary", "success", "warning", "danger", "info", "magic", "pink",
];

const cards: Card[] = [...baseCards, ...hazardCards] as unknown as Card[];

describe("iconMap resolution coverage", () => {
  it("resolves a non-fallback icon for every effect in the card data", () => {
    const effects: Modifier[] = cards.flatMap((card) => card.effects);
    expect(effects.length).toBeGreaterThan(0);
    for (const effect of effects) {
      const icon = resolveEffectIcon(effect);
      expect(icon, `${effect.stat} ${effect.operation} tags=${effect.tags.join(",")}`).toBeTruthy();
      expect(icon).not.toBe(FALLBACK_ICON);
    }
  });

  it("resolves a defined accent for every card in the card data", () => {
    expect(cards.length).toBeGreaterThan(0);
    for (const card of cards) {
      const accent = accentForCard(card.tags);
      expect(VALID_ACCENTS, `${card.id} tags=${card.tags.join(",")}`).toContain(accent);
    }
  });

  it("resolves the documented default accent when no type tag maps", () => {
    expect(accentForCard(["hazard", "trap"])).toBe(DEFAULT_ACCENT);
  });

  it("applies the documented multi-tag precedence (Shield Bash -> attack/danger)", () => {
    expect(accentForCard(["attack", "physical", "control"])).toBe("danger");
  });
});
