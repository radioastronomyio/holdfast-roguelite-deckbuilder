import { describe, expect, it } from "vitest";
import rngFixture from "../__fixtures__/rng_sequence.json";
import statFixture from "../__fixtures__/stat_calculations.json";
import combatFixture from "../__fixtures__/combat_seed_42.json";
import campaignFixture from "../__fixtures__/campaign_seed_42.json";
import { SeededRng } from "../rng";
import { calculateStat } from "../stats";
import { loadGameDataFromPath } from "../loader.node";
import { characterToCombatEntity, enemyDataToCombatEntity, runCampaign } from "../campaign";
import { resolveCombat } from "../encounters";
import { AiHeuristic, Stat, type Modifier } from "../types";

describe("Python parity fixtures", () => {
  it("matches CPython RNG sequences", () => {
    let rng = new SeededRng(rngFixture.seed);
    expect(Array.from({ length: 1000 }, () => rng.random())).toEqual(rngFixture.random);
    rng = new SeededRng(rngFixture.seed);
    expect(Array.from({ length: 1000 }, () => rng.getrandbits(32))).toEqual(rngFixture.getrandbits32);
    rng = new SeededRng(rngFixture.seed);
    expect(Array.from({ length: 1000 }, () => rng.randBelow(100))).toEqual(rngFixture.randbelow100);
    rng = new SeededRng(rngFixture.seed);
    expect(Array.from({ length: 1000 }, () => rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]))).toEqual(rngFixture.choice10);
    rng = new SeededRng(rngFixture.seed);
    expect(Array.from({ length: 1000 }, () => {
      const values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
      rng.shuffle(values);
      return values;
    })).toEqual(rngFixture.shuffle10);
    rng = new SeededRng(rngFixture.randint_seed);
    expect(Array.from({ length: 500 }, () => rng.randint(1, 100))).toEqual(rngFixture.randint_1_100);
  });

  it("matches Python stat calculations", () => {
    for (const entry of statFixture) {
      const result = calculateStat(entry.base, entry.modifiers as Modifier[], entry.stat as Stat);
      expect(Number.isSafeInteger(result)).toBe(true);
      expect(result, entry.name).toBe(entry.result);
    }
  });

  it("matches Python combat seed 42 summary", async () => {
    const data = await loadGameDataFromPath("../data");
    const party = [characterToCombatEntity(data.characters[0], [], [])];
    const enemy = { ...data.enemies_by_id.scavenger_patrol, card_pool: ["guard_up_01"] };
    party[0].card_pool = ["arcane_strike_01"];
    const enemies = [enemyDataToCombatEntity(enemy)];
    const result = resolveCombat(party, enemies, data.cards_by_id, { rng: new SeededRng(42) });
    expect({
      player_won: result.player_won,
      turns_taken: result.turns_taken,
      final_hp: result.final_hp,
      survivors: result.survivors
    }).toEqual(combatFixture);
  });

  it("matches Python campaign seed 42 aggressive summary", async () => {
    const data = await loadGameDataFromPath("../data");
    const result = runCampaign(42, data, AiHeuristic.aggressive);
    expect(result.victory).toBe(campaignFixture.victory);
    expect(result.regions_cleared).toBe(campaignFixture.regions_cleared);
    expect(result.region_order).toEqual(campaignFixture.region_order);
    expect(result.total_turns).toBe(campaignFixture.total_turns);
    expect(result.world_cards_accepted_ids).toEqual(campaignFixture.world_cards_accepted_ids);
    expect(result.world_cards_skipped_ids).toEqual(campaignFixture.world_cards_skipped_ids);
    expect(result.upgrade_branches_chosen).toEqual(campaignFixture.upgrade_branches_chosen);
  });
});
