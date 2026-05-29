import { describe, expect, it } from "vitest";
import { drawCards, discardCard, discardHand, initializeDeck, processTurnStart, tickUntilNextTurn } from "../turnOrder";
import { AiHeuristic, Operation, Stacking, Stat, Target, type Card, type CombatEntity } from "../types";
import { SeededRng } from "../rng";

const entity = (id: string, speed: number, ct = 0): CombatEntity => ({
  id,
  name: id,
  base_stats: { HP: 10_000, Power: 1_000, Speed: speed, Defense: 0, Energy: 3_000 },
  active_modifiers: [],
  ct,
  is_player: true,
  card_pool: [],
  ai_heuristic: AiHeuristic.balanced,
  is_alive: true,
  current_energy: 0,
  draw_pile: [],
  hand: [],
  discard_pile: []
});

const card = (id: string, copies: number): Card => ({
  id,
  name: id,
  energy_cost: 1,
  effects: [],
  tags: [],
  deck_copies: copies,
  upgrade_tier: 0,
  upgrade_paths: {}
});

describe("turn order", () => {
  it("advances CT and breaks ties by overflow, speed, then position", () => {
    const a = entity("a", 50_000);
    const b = entity("b", 60_000);
    const actor = tickUntilNextTurn([a, b]);
    expect(actor.id).toBe("b");
    expect(b.ct).toBe(20_000);
  });

  it("decrements and expires modifiers before refreshing energy", () => {
    const e = entity("e", 50_000);
    e.active_modifiers = [{
      stat: Stat.Energy,
      operation: Operation.FLAT_ADD,
      value: 2_000,
      duration: 1,
      target: Target.SELF,
      stacking: Stacking.stack,
      tags: []
    }];
    const logs = processTurnStart(e, 1);
    expect(logs).toEqual(["e: 1 modifier(s) expired"]);
    expect(e.current_energy).toBe(3_000);
  });

  it("builds, draws, discards, and reshuffles a deck", () => {
    const e = entity("e", 50_000);
    e.card_pool = ["a", "b"];
    initializeDeck(e, { a: card("a", 2), b: card("b", 1) }, new SeededRng(1));
    expect(e.draw_pile).toHaveLength(3);
    expect(drawCards(e, 2, new SeededRng(2))).toHaveLength(2);
    discardCard(e, e.hand[0]);
    discardHand(e);
    e.draw_pile = [];
    expect(drawCards(e, 3, new SeededRng(3)).length).toBeGreaterThan(0);
  });
});
