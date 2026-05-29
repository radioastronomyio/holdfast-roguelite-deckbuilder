import { describe, expect, it } from "vitest";
import { playCard, resolveCombat } from "../encounters";
import { Operation, Stacking, Stat, Target, type Card, type CombatEntity } from "../types";
import { SeededRng } from "../rng";

const entity = (id: string, player: boolean): CombatEntity => ({
  id,
  name: id,
  base_stats: { HP: 50_000, Power: 10_000, Speed: 100_000, Defense: 2_000, Energy: 3_000 },
  active_modifiers: [],
  ct: 0,
  is_player: player,
  card_pool: [],
  is_alive: true,
  current_energy: 3_000,
  draw_pile: [],
  hand: [],
  discard_pile: []
});

const strike: Card = {
  id: "strike",
  name: "Strike",
  energy_cost: 1,
  effects: [{ stat: Stat.HP, operation: Operation.FLAT_SUB, value: 15_000, duration: 0, target: Target.ENEMY_SINGLE, stacking: Stacking.replace, tags: [] }],
  tags: [],
  deck_copies: 1,
  upgrade_tier: 0,
  upgrade_paths: {}
};

describe("encounters", () => {
  it("applies damage as card value plus power minus defense", () => {
    const caster = entity("caster", true);
    const target = entity("target", false);
    playCard(strike, caster, [target], [caster, target]);
    expect(target.base_stats.HP).toBe(27_000);
    expect(caster.current_energy).toBe(2_999);
  });

  it("terminates combat when enemies die", () => {
    const player = entity("player", true);
    player.card_pool = ["strike"];
    const enemy = entity("enemy", false);
    enemy.base_stats.HP = 10_000;
    const result = resolveCombat([player], [enemy], { strike }, { rng: new SeededRng(1) });
    expect(result.player_won).toBe(true);
    expect(result.turns_taken).toBeGreaterThan(0);
  });
});
