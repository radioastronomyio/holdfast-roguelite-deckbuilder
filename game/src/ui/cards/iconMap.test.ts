/**
 * Coverage test for the frozen card-tag accent map.
 *
 * Effect, mixed-source motif, and provenance coverage lives in cardMap.test.ts.
 * These checks retain the frame-accent precedence that downstream
 * card consumers already depend on.
 *
 * @module ui/cards/iconMap.test
 */

import { describe, expect, it } from "vitest";
import baseCards from "../../../../data/cards/base-cards.json";
import hazardCards from "../../../../data/cards/hazard-cards.json";
import type { Card } from "../../sim/types";
import type { CardAccent } from "../gameui";
import { accentForCard, DEFAULT_ACCENT } from "./iconMap";

const VALID_ACCENTS: CardAccent[] = [
  "primary", "success", "warning", "danger", "info", "magic", "pink",
];

const cards: Card[] = [...baseCards, ...hazardCards] as unknown as Card[];

describe("card accent resolution coverage", () => {
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
