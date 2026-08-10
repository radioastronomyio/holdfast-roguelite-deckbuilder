/**
 * Inline SVG badge and upgrade-gem contract.
 *
 * @vitest-environment happy-dom
 */

import { describe, expect, it } from "vitest";
import baseCardsJson from "../../../../data/cards/base-cards.json";
import type { Card } from "../../sim/types";
import { createCostBadge, createUpgradeGem } from "./cardBadges";
import { createHoldfastCard } from "./holdfastCard";

const baseCards = baseCardsJson as unknown as Card[];

describe("card SVG badges", () => {
  it.each([0, 1, 2, 3, 4])("renders energy cost %i as SVG text", (cost) => {
    const badge = createCostBadge(cost);

    expect(badge.tagName.toLowerCase()).toBe("svg");
    expect(badge.dataset.cost).toBe(String(cost));
    expect(badge.querySelector("text")?.textContent).toBe(String(cost));
    expect(badge.classList.contains("hf-card-badge--cost")).toBe(true);
  });

  it.each([0, 1, 2, 3])("renders upgrade tier %i as an SVG gem state", (tier) => {
    const gem = createUpgradeGem(tier);

    expect(gem.tagName.toLowerCase()).toBe("svg");
    expect(gem.dataset.upgradeTier).toBe(String(tier));
    expect(gem.classList.contains(`hf-card-gem--tier-${tier}`)).toBe(true);
    expect(gem.querySelector("polygon")).not.toBeNull();
  });

  it("uses currentColor so badge and gem inherit the card accent token", () => {
    const badge = createCostBadge(2);
    const gem = createUpgradeGem(2);

    expect(badge.querySelector("circle")?.getAttribute("stroke")).toBe("currentColor");
    expect(gem.querySelector("polygon")?.getAttribute("stroke")).toBe("currentColor");
  });
});

describe("badge integration", () => {
  it("renders energy_cost 3 in the composed card badge", () => {
    const card = baseCards.find(({ id }) => id === "sweeping_blade_01");
    if (!card) throw new Error("missing sweeping_blade_01 fixture");

    const control = createHoldfastCard(card);
    expect(control.el.querySelector(".hf-card-badge--cost text")?.textContent).toBe("3");
  });
});
