import { describe, expect, it } from "vitest";
import { calculateStat, applyStacking } from "../stats";
import { Operation, Stacking, Stat, Target, type Modifier } from "../types";

const mod = (partial: Partial<Modifier>): Modifier => ({
  stat: Stat.HP,
  operation: Operation.FLAT_ADD,
  value: 0,
  duration: -1,
  target: Target.SELF,
  stacking: Stacking.replace,
  tags: [],
  ...partial
});

describe("stats resolver", () => {
  it("uses Python floor division for negative HP intermediates", () => {
    const result = calculateStat(1_000, [
      mod({ operation: Operation.FLAT_SUB, value: 2_500 }),
      mod({ operation: Operation.PCT_ADD, value: 50 })
    ], Stat.HP);
    expect(result).toBe(-2250);
    expect(Number.isSafeInteger(result)).toBe(true);
  });

  it("applies stack, replace, and max grouping by stat and operation", () => {
    const stacked = applyStacking([
      mod({ stat: Stat.Power, operation: Operation.FLAT_ADD, value: 1, stacking: Stacking.stack }),
      mod({ stat: Stat.Power, operation: Operation.FLAT_ADD, value: 2, stacking: Stacking.stack }),
      mod({ stat: Stat.Speed, operation: Operation.PCT_ADD, value: 10, stacking: Stacking.replace }),
      mod({ stat: Stat.Speed, operation: Operation.PCT_ADD, value: 20, stacking: Stacking.replace }),
      mod({ stat: Stat.Defense, operation: Operation.FLAT_ADD, value: 7, stacking: Stacking.max }),
      mod({ stat: Stat.Defense, operation: Operation.FLAT_ADD, value: 4, stacking: Stacking.max })
    ]);
    expect(stacked.map((m) => m.value)).toEqual([1, 2, 20, 7]);
  });

  it("caps positive speed percentage and enforces speed floor", () => {
    expect(calculateStat(100_000, [
      mod({ stat: Stat.Speed, operation: Operation.PCT_ADD, value: 125 })
    ], Stat.Speed)).toBe(175_000);
    expect(calculateStat(100_000, [
      mod({ stat: Stat.Speed, operation: Operation.PCT_SUB, value: 100 })
    ], Stat.Speed)).toBe(10_000);
  });

  it("applies sequential multiply modifiers after flat and percent", () => {
    expect(calculateStat(10_000, [
      mod({ stat: Stat.Power, operation: Operation.FLAT_ADD, value: 5_000, stacking: Stacking.stack }),
      mod({ stat: Stat.Power, operation: Operation.PCT_ADD, value: 50, stacking: Stacking.stack }),
      mod({ stat: Stat.Power, operation: Operation.MULTIPLY, value: 500, stacking: Stacking.stack }),
      mod({ stat: Stat.Power, operation: Operation.MULTIPLY, value: 1500, stacking: Stacking.stack })
    ], Stat.Power)).toBe(16_875);
  });
});
