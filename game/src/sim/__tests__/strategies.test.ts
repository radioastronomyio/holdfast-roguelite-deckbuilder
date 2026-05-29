import { describe, expect, it } from "vitest";
import { AggressiveAI, BalancedAI, DefensiveAI } from "../strategies";
import { Operation, Stacking, Stat, Target, type Card, type CombatEntity } from "../types";

const entity = (id: string, hp: number, power: number): CombatEntity => ({
  id,
  name: id,
  base_stats: { HP: hp, Power: power, Speed: 50_000, Defense: 0, Energy: 3_000 },
  active_modifiers: [],
  ct: 0,
  is_player: true,
  card_pool: [],
  is_alive: true,
  current_energy: 3,
  draw_pile: [],
  hand: [],
  discard_pile: []
});

const card = (id: string, effects: Card["effects"], energy_cost = 1): Card => ({
  id,
  name: id,
  energy_cost,
  effects,
  tags: [],
  deck_copies: 1,
  upgrade_tier: 0,
  upgrade_paths: {}
});

const strike = card("strike", [{ stat: Stat.HP, operation: Operation.FLAT_SUB, value: 10_000, duration: 0, target: Target.ENEMY_SINGLE, stacking: Stacking.stack, tags: [] }]);
const sweep = card("sweep", [{ stat: Stat.HP, operation: Operation.FLAT_SUB, value: 8_000, duration: 0, target: Target.ENEMY_ALL, stacking: Stacking.stack, tags: [] }]);
const heal = card("heal", [{ stat: Stat.HP, operation: Operation.FLAT_ADD, value: 12_000, duration: 0, target: Target.ALLY_SINGLE, stacking: Stacking.stack, tags: [] }]);

describe("AI strategies", () => {
  it("aggressive scores AoE over single target when multiple enemies live", () => {
    const actor = entity("actor", 100_000, 20_000);
    const enemies = [entity("low", 10_000, 1_000), entity("high", 100_000, 1_000)];
    for (const enemy of enemies) enemy.is_player = false;
    const action = new AggressiveAI().selectCard(actor, [strike, sweep], [actor], enemies);
    expect(action?.[0].id).toBe("sweep");
    expect(action?.[1].map((target) => target.id)).toEqual(["low", "high"]);
  });

  it("defensive targets the highest power enemy with damage", () => {
    const actor = entity("actor", 100_000, 20_000);
    const enemies = [entity("low-power", 10_000, 1_000), entity("high-power", 100_000, 99_000)];
    for (const enemy of enemies) enemy.is_player = false;
    const action = new DefensiveAI().selectCard(actor, [strike], [actor], enemies);
    expect(action?.[1][0].id).toBe("high-power");
  });

  it("balanced prioritizes healing when an ally is below 40 percent HP", () => {
    const actor = entity("actor", 100_000, 20_000);
    const ally = entity("ally", 100_000, 1_000);
    ally.active_modifiers = [{ stat: Stat.HP, operation: Operation.FLAT_SUB, value: 70_000, duration: -1, target: Target.SELF, stacking: Stacking.stack, tags: [] }];
    const enemy = entity("enemy", 100_000, 1_000);
    enemy.is_player = false;
    const action = new BalancedAI().selectCard(actor, [strike, heal], [actor, ally], [enemy]);
    expect(action?.[0].id).toBe("heal");
    expect(action?.[1][0].id).toBe("ally");
  });
});
