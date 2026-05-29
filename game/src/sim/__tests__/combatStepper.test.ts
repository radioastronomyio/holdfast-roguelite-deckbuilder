import { describe, expect, it } from "vitest";
import { CombatStepper, CombatStepperStatus } from "../combatStepper";
import { Operation, Stacking, Stat, Target, type Card, type CombatEntity } from "../types";

const entity = (id: string, player: boolean, hp = 50_000): CombatEntity => ({
  id,
  name: id,
  base_stats: { HP: hp, Power: 10_000, Speed: 100_000, Defense: 2_000, Energy: 3_000 },
  active_modifiers: [],
  ct: 0,
  is_player: player,
  card_pool: ["strike"],
  is_alive: true,
  current_energy: 0,
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
  deck_copies: 5,
  upgrade_tier: 0,
  upgrade_paths: {}
};

describe("CombatStepper", () => {
  it("advances to a player card selection with turn and hand events", () => {
    const stepper = new CombatStepper([entity("hero", true)], [entity("enemy", false)], { strike }, { seed: 7 });
    const result = stepper.advance();
    expect(result.status).toBe(CombatStepperStatus.PLAYER_SELECT_CARD);
    expect(result.activeEntityId).toBe("hero");
    expect(result.events.map((event) => event.type)).toEqual(["TURN_STARTED", "HAND_DRAWN"]);
    expect(stepper.snapshot().entities.find((item) => item.id === "hero")?.hand).toHaveLength(5);
  });

  it("selects a card, targets an enemy, emits typed combat events, and discards the card", () => {
    const stepper = new CombatStepper([entity("hero", true)], [entity("enemy", false)], { strike }, { seed: 7 });
    stepper.advance();
    expect(stepper.selectCard(0).status).toBe(CombatStepperStatus.PLAYER_SELECT_TARGET);
    const result = stepper.selectTarget("enemy");
    expect(result.status).toBe(CombatStepperStatus.PLAYER_SELECT_CARD);
    expect(result.events.map((event) => event.type)).toContain("CARD_PLAYED");
    expect(result.events.map((event) => event.type)).toContain("TARGET_DAMAGED");
    expect(stepper.snapshot().entities.find((item) => item.id === "hero")?.discard_pile).toEqual(["strike"]);
  });

  it("auto-resolves enemy turns and can serialize and restore", () => {
    const hero = entity("hero", true);
    const enemy = entity("enemy", false);
    hero.ct = 0;
    enemy.ct = 100_000;
    const stepper = new CombatStepper([hero], [enemy], { strike }, { seed: 11 });
    const enemyTurn = stepper.advance();
    expect(enemyTurn.events.some((event) => event.type === "CARD_PLAYED")).toBe(true);
    const restored = CombatStepper.fromJSON(stepper.toJSON(), { strike });
    expect(restored.toJSON()).toEqual(stepper.toJSON());
  });
});
