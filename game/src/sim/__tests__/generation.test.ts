import { describe, expect, it } from "vitest";
import { loadGameDataFromPath } from "../loader.node";
import { SeededRng } from "../rng";
import { NarrativePosition } from "../types";
import { generateCharacter, generateEnemy, generateEncounter, generateRegion } from "../generation";

describe("procedural generation parity", () => {
  it("generates the Python seed 100 character", async () => {
    const data = await loadGameDataFromPath("../data");
    const character = generateCharacter(new SeededRng(100), data.generation_bounds, data.flavor);
    expect(character).toMatchObject({
      id: "nyra_brawler",
      name: "Nyra, the Unyielding Brawler from the Shelf",
      base_stats: { HP: 54_000, Power: 31_000, Speed: 74_000, Defense: 24_000, Energy: 4_000 },
      innate_passive: { stat: "Speed", operation: "PCT_ADD", value: 16, duration: -1, target: "SELF", stacking: "stack", tags: ["passive"] }
    });
  });

  it("generates the Python seed 200 enemy", async () => {
    const data = await loadGameDataFromPath("../data");
    const cardIds = Object.keys(data.cards_by_id).filter((id) => !data.cards_by_id[id].tags.includes("hazard"));
    const enemy = generateEnemy(new SeededRng(200), 3, cardIds, { flavor: data.flavor, cardsById: data.cards_by_id });
    expect(enemy).toEqual({
      id: "sentinel_spire_1265",
      name: "Sentinel Spire",
      base_stats: { HP: 53_000, Power: 60_000, Speed: 37_000, Defense: 25_000, Energy: 4_000 },
      card_pool: ["stone_wall_01", "deep_focus_01"],
      ai_heuristic_tag: "aggressive",
      is_elite: false
    });
  });

  it("generates Python seed 300 encounter types and stronghold enemy", async () => {
    const data = await loadGameDataFromPath("../data");
    const cardIds = Object.keys(data.cards_by_id).filter((id) => !data.cards_by_id[id].tags.includes("hazard"));
    const enemyRegistry = new Map();
    expect(generateEncounter(new SeededRng(300), NarrativePosition.approach, 2, cardIds, data.flavor, { enemyRegistry, cardsById: data.cards_by_id }).type).toBe("hazard");
    expect(generateEncounter(new SeededRng(300), NarrativePosition.settlement, 2, cardIds, data.flavor, { enemyRegistry, cardsById: data.cards_by_id }).type).toBe("combat");
    const stronghold = generateEncounter(new SeededRng(300), NarrativePosition.stronghold, 2, cardIds, data.flavor, { enemyRegistry, cardsById: data.cards_by_id });
    expect(stronghold).toMatchObject({ type: "combat", enemies: ["oracle_summit_3649"] });
  });

  it("generates the Python seed 400 region structure", async () => {
    const data = await loadGameDataFromPath("../data");
    const cardIds = Object.keys(data.cards_by_id).filter((id) => !data.cards_by_id[id].tags.includes("hazard"));
    const enemyRegistry = new Map();
    const region = generateRegion(new SeededRng(400), 2, cardIds, data.flavor, { enemyRegistry, cardsById: data.cards_by_id });
    expect(region).toMatchObject({
      id: "corroded_barrens",
      name: "Corroded Barrens",
      modifier_stack: [
        { stat: "HP", operation: "FLAT_SUB", value: 7_000, target: "ENEMY_ALL" },
        { stat: "Energy", operation: "FLAT_SUB", value: 7_000, target: "ALLY_ALL" }
      ],
      meta_reward: { stat: "HP", operation: "FLAT_ADD", value: 1_000 }
    });
    expect(region.encounters.map((encounter) => encounter.type)).toEqual(["event", "combat", "combat"]);
    expect([...enemyRegistry.keys()].sort()).toEqual(["channeler_caverns_9951", "knight_wastes_1431", "knight_wilds_9380"]);
  });
});
