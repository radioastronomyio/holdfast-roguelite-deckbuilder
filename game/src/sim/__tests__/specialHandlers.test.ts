import { describe, expect, it } from "vitest";
import { applySpecialHandler, checkSpecialTags, createSpecialHandlerContext } from "../specialHandlers";
import { Operation, Stacking, Stat, Target, type CombatEntity, type Modifier } from "../types";

const tagged = (tag: string, duration = 2): Modifier => ({
  stat: Stat.Speed,
  operation: Operation.PCT_SUB,
  value: 50,
  duration,
  target: Target.SELF,
  stacking: Stacking.stack,
  tags: [tag]
});

const entity: CombatEntity = {
  id: "e",
  name: "e",
  base_stats: { HP: 1, Power: 1, Speed: 1, Defense: 1, Energy: 1 },
  active_modifiers: [tagged("no_refresh_turn_2"), tagged("delayed_start_turn_2")],
  ct: 0,
  is_player: true,
  card_pool: [],
  is_alive: true,
  current_energy: 0,
  draw_pile: [],
  hand: [],
  discard_pile: []
};

describe("special handlers", () => {
  it("detects and applies each special tag", () => {
    expect(checkSpecialTags(tagged("status_duration_multiply_2"))).toBe("status_duration_multiply_2");
    const durationCtx = createSpecialHandlerContext(entity, 1, tagged("status_duration_multiply_2", 3));
    applySpecialHandler("status_duration_multiply_2", durationCtx);
    expect(durationCtx.modified_incoming?.duration).toBe(6);

    const noRefreshCtx = createSpecialHandlerContext(entity, 2);
    applySpecialHandler("no_refresh_turn_2", noRefreshCtx);
    expect(noRefreshCtx.suppress_energy_refresh).toBe(true);

    const delayedCtx = createSpecialHandlerContext(entity, 1);
    applySpecialHandler("delayed_start_turn_2", delayedCtx);
    expect(delayedCtx.modifiers_to_skip_decrement).toHaveLength(1);
  });
});
