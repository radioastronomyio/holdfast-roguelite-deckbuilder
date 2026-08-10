/**
 * Compile-time and runtime fixture for the frozen Holdfast card factory.
 *
 * @vitest-environment happy-dom
 */

import { describe, expect, it, vi } from "vitest";
import baseCardsJson from "../../../../data/cards/base-cards.json";
import upgradeTreesJson from "../../../../data/cards/upgrade-trees.json";
import type { Card, UpgradeTree } from "../../sim/types";
import type { CreateHoldfastCard, HoldfastCardControl, HoldfastCardOptions } from "./contract";
import { createHoldfastCard } from "./holdfastCard";

const card = (baseCardsJson as unknown as Card[])[0];
const trees = upgradeTreesJson as unknown as Record<string, UpgradeTree>;

const frozenFactory: CreateHoldfastCard = createHoldfastCard;

describe("createHoldfastCard frozen contract", () => {
  it("accepts every documented option and returns every documented control method", () => {
    const onClick = vi.fn();
    const onSelect = vi.fn();
    const options: HoldfastCardOptions = {
      rare: true,
      selectable: true,
      selected: true,
      disabled: false,
      onClick,
      onSelect,
      upgradeTree: trees[card.id],
    };

    const control: HoldfastCardControl = frozenFactory(card, options);
    document.body.replaceChildren(control.el);

    control.setSelected(false);
    expect(control.isSelected()).toBe(false);
    control.setDisabled(false);
    control.setTitle(card.name);
    control.setSubtitle("Contract fixture");
    control.setBody(document.createElement("div"));
    control.setTag({ label: String(card.energy_cost), accent: "danger" });
    control.onClick(onClick);
    control.onSelect(onSelect);
    control.setRare(false);
    control.setEnergyAffordable(true);
    control.openInspect();

    expect(control.el).toBeInstanceOf(HTMLElement);
    expect(document.querySelector(".gui-modal.is-open")).not.toBeNull();
  });
});
