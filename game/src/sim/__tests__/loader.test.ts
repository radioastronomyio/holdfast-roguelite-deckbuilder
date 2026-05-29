import { describe, expect, it } from "vitest";
import { loadGameDataFromPath } from "../loader.node";
import { loadGameDataFromRaw } from "../loader";
import { Operation, STAT_SCALE } from "../types";

describe("loader", () => {
  it("loads repo data and scales card flat effects", async () => {
    const data = await loadGameDataFromPath("../data");
    const card = data.cards_by_id.arcane_strike_01;
    const damage = card.effects.find((effect) => effect.operation === Operation.FLAT_SUB);
    expect(damage?.value).toBe(15 * STAT_SCALE);
  });

  it("raw and path loaders produce the same card ids", async () => {
    const data = await loadGameDataFromPath("../data");
    const raw = {
      base_cards: Object.values(data.cards_by_id).filter((card) => !card.tags.includes("hazard")),
      hazard_cards: Object.values(data.cards_by_id).filter((card) => card.tags.includes("hazard")),
      upgrade_trees: data.upgrade_trees,
      characters: data.characters,
      enemies: Object.values(data.enemies_by_id),
      generation_bounds: data.generation_bounds,
      regions: data.regions,
      world_deck: data.world_deck,
      outpost_upgrades: data.outpost_upgrades,
      flavor: data.flavor
    };
    const fromRaw = loadGameDataFromRaw(raw);
    expect(Object.keys(fromRaw.cards_by_id).sort()).toEqual(Object.keys(data.cards_by_id).sort());
  });
});
