/**
 * DOM tests for the Holdfast card renderer factory.
 *
 * Covers the Deliverable 2 contract (energy badge, per-modifier effect rows,
 * operation-aware value formatting, accent precedence, tier pips, shine, and
 * selectable/disabled/onSelect pass-through) and the Deliverable 3 contract
 * (inspect opens a detail modal without toggling selection).
 *
 * @vitest-environment happy-dom
 *
 * @module ui/cards/holdfastCard.test
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import baseCardsJson from "../../../../data/cards/base-cards.json";
import upgradeTreesJson from "../../../../data/cards/upgrade-trees.json";
import type { Card, UpgradeTree } from "../../sim/types";
import { createHoldfastCard, formatEffectValue } from "./holdfastCard";

const baseCards = baseCardsJson as unknown as Card[];
const upgradeTrees = upgradeTreesJson as unknown as Record<string, UpgradeTree>;
const byId = (id: string): Card => {
  const card = baseCards.find((c) => c.id === id);
  if (!card) throw new Error(`missing test card ${id}`);
  return card;
};

function render(card: Card, opts?: Parameters<typeof createHoldfastCard>[1]) {
  const control = createHoldfastCard(card, opts);
  document.body.innerHTML = "";
  document.body.appendChild(control.el);
  return control;
}

describe("formatEffectValue (operation-aware, display scale)", () => {
  it("renders FLAT_SUB as a negative damage value at display scale", () => {
    expect(formatEffectValue({ stat: "HP", operation: "FLAT_SUB", value: 15 } as never)).toBe("-15");
  });
  it("renders FLAT_ADD positive", () => {
    expect(formatEffectValue({ stat: "HP", operation: "FLAT_ADD", value: 10 } as never)).toBe("+10");
  });
  it("renders PCT_SUB as a percentage, not a raw scaled integer", () => {
    expect(formatEffectValue({ stat: "Speed", operation: "PCT_SUB", value: 50 } as never)).toBe("-50%");
  });
  it("renders MULTIPLY as a multiplier", () => {
    expect(formatEffectValue({ stat: "Power", operation: "MULTIPLY", value: 2 } as never)).toBe("x2");
  });
});

describe("createHoldfastCard rendering", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("renders arcane_strike_01 with name, energy badge 2, and one effect row", () => {
    const control = render(byId("arcane_strike_01"));
    expect(control.el.querySelector(".gui-card__title")?.textContent).toBe("Arcane Strike");
    expect(control.el.querySelector(".gui-card__tag")?.textContent).toBe("2");
    expect(control.el.querySelectorAll(".hf-card__effect")).toHaveLength(1);
  });

  it("populates the six-region deckbuilder frame from card data", () => {
    const control = render(byId("arcane_strike_01"));

    expect(control.el.querySelector(".hf-card__cost")?.textContent).toBe("2");
    expect(control.el.querySelector(".hf-card__art")).not.toBeNull();
    expect(control.el.querySelector(".hf-card__type")?.textContent).toBe("Attack · Magic");
    expect(control.el.querySelector(".hf-card__rules")?.textContent).toContain("-15 HP");
    expect(control.el.querySelector(".hf-card__attack")?.textContent).toContain("15");
    expect(control.el.querySelector(".hf-card__guard")?.textContent).toContain("0");
  });

  it("shows FLAT_SUB HP as the display-scale damage value (15, not 15000)", () => {
    const control = render(byId("arcane_strike_01"));
    const value = control.el.querySelector(".hf-card__effect-value")?.textContent ?? "";
    expect(value).toContain("15");
    expect(value).not.toContain("15000");
    expect(value).not.toContain("0.015");
  });

  it("renders immolate_01 with energy badge 1 and one effect row", () => {
    const control = render(byId("immolate_01"));
    expect(control.el.querySelector(".gui-card__tag")?.textContent).toBe("1");
    expect(control.el.querySelectorAll(".hf-card__effect")).toHaveLength(1);
  });

  it("renders shield_bash_01 with energy badge 2, two effect rows, and danger accent", () => {
    const control = render(byId("shield_bash_01"));
    expect(control.el.querySelector(".gui-card__tag")?.textContent).toBe("2");
    expect(control.el.querySelectorAll(".hf-card__effect")).toHaveLength(2);
    // Multi-tag precedence: attack/physical/control -> attack -> danger.
    expect(control.el.classList.contains("hf-card--danger")).toBe(true);
  });

  it("renders the Shield Bash Speed effect as a percentage, not a raw integer", () => {
    const control = render(byId("shield_bash_01"));
    const values = Array.from(control.el.querySelectorAll(".hf-card__effect-value")).map((n) => n.textContent ?? "");
    expect(values.some((v) => v.includes("%"))).toBe(true);
    expect(values.join(" ")).not.toContain("50000");
  });

  it("resolves an inline currentColor SVG symbol for every effect row", () => {
    const control = render(byId("shield_bash_01"));
    const icons = Array.from(control.el.querySelectorAll<SVGSVGElement>(".hf-card__effect-icon"));
    expect(icons).toHaveLength(2);
    for (const icon of icons) {
      const symbol = icon.querySelector("use");
      expect(symbol?.getAttribute("href")).toMatch(
        /\/assets\/card-art-icons\/.+\.svg#icon$/,
      );
      expect(symbol?.getAttribute("fill")).toBe("currentColor");
    }
  });

  it("shows an upgrade gem + shine for an upgraded card and neither for a base card", () => {
    const base = render(byId("arcane_strike_01"));
    expect(base.el.querySelector(".hf-card-gem")?.getAttribute("data-upgrade-tier")).toBe("0");
    expect(base.el.classList.contains("hf-card--shine")).toBe(false);

    const upgradedCard: Card = { ...byId("arcane_strike_01"), upgrade_tier: 2 };
    const upgraded = render(upgradedCard);
    expect(upgraded.el.querySelector(".hf-card-gem")?.getAttribute("data-upgrade-tier")).toBe("2");
    expect(upgraded.el.classList.contains("hf-card--upgraded")).toBe(true);
    expect(upgraded.el.classList.contains("hf-card--shine")).toBe(true);
  });

  it("keeps the legacy rare option but reserves shine for upgraded cards", () => {
    const control = render(byId("arcane_strike_01"), { rare: true });
    expect(control.el.classList.contains("hf-card--rare")).toBe(true);
    expect(control.el.classList.contains("hf-card--shine")).toBe(false);
  });
});

describe("createHoldfastCard selection + energy pass-through", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("toggles .is-selected and fires onSelect for a selectable card", () => {
    const onSelect = vi.fn();
    const control = render(byId("arcane_strike_01"), { selectable: true, onSelect });
    control.el.click();
    expect(control.el.classList.contains("is-selected")).toBe(true);
    expect(onSelect).toHaveBeenCalledWith(true);
  });

  it("does not toggle selection when disabled (energy-unaffordable)", () => {
    const onSelect = vi.fn();
    const control = render(byId("arcane_strike_01"), {
      selectable: true,
      disabled: true,
      onSelect,
    });
    control.el.click();
    expect(control.el.classList.contains("is-selected")).toBe(false);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("maps setEnergyAffordable(false) to the disabled state", () => {
    const control = render(byId("arcane_strike_01"), { selectable: true });
    control.setEnergyAffordable(false);
    expect(control.el.classList.contains("is-disabled")).toBe(true);
    control.setEnergyAffordable(true);
    expect(control.el.classList.contains("is-disabled")).toBe(false);
  });
});

describe("createHoldfastCard inspect affordance", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
  });

  it("opens a modal with the full effect breakdown and tags", () => {
    const control = render(byId("shield_bash_01"));
    control.openInspect();
    const modal = document.querySelector(".gui-modal.is-open");
    expect(modal).not.toBeNull();
    const text = modal?.textContent ?? "";
    // Two effects -> two inspect rows, each carries the operation label.
    expect(document.querySelectorAll(".hf-inspect__row")).toHaveLength(2);
    expect(text).toContain("attack");
  });

  it("inspecting a selectable card does not toggle its selection", () => {
    const onSelect = vi.fn();
    const control = render(byId("arcane_strike_01"), { selectable: true, onSelect });
    const inspectBtn = control.el.querySelector<HTMLButtonElement>(".hf-card__inspect");
    inspectBtn?.click();
    expect(document.querySelector(".gui-modal.is-open")).not.toBeNull();
    expect(control.el.classList.contains("is-selected")).toBe(false);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("closes cleanly via the modal close button without console errors", () => {
    const control = render(byId("arcane_strike_01"));
    control.openInspect();
    const closeBtn = document.querySelector<HTMLButtonElement>(".gui-modal__close");
    expect(closeBtn).not.toBeNull();
    closeBtn!.click();
    expect(document.querySelector(".gui-modal.is-open")).toBeNull();
  });

  it("shows upgrade paths when the card has entries in upgrade-trees.json", () => {
    const card = byId("arcane_strike_01");
    const control = createHoldfastCard(card, { upgradeTree: upgradeTrees[card.id] });
    document.body.innerHTML = "";
    document.body.appendChild(control.el);
    control.openInspect();
    expect(document.querySelectorAll(".hf-inspect__path").length).toBeGreaterThan(0);
    expect(document.querySelector(".hf-inspect__heading")?.textContent).toContain("Upgrade Paths");
  });

  it("shows no upgrade paths when the card has no tree", () => {
    const control = render(byId("arcane_strike_01"));
    control.openInspect();
    expect(document.querySelector(".hf-inspect__path")).toBeNull();
    expect(document.querySelector(".hf-inspect__heading")).toBeNull();
  });
});
