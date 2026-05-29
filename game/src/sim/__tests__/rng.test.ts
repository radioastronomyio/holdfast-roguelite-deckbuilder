import { describe, expect, it } from "vitest";
import { SeededRng } from "../rng";

describe("SeededRng", () => {
  it("matches CPython random for first known seed values", () => {
    const rng = new SeededRng(12345);
    expect(rng.random()).toBe(0.41661987254534116);
    expect(rng.getrandbits(32)).toBe(43676229);
    expect(rng.randBelow(100)).toBe(38);
    expect(rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])).toBe(5);
  });

  it("restores serialized state exactly", () => {
    const rng = new SeededRng(99999);
    rng.random();
    const state = rng.getState();
    const a = rng.randint(1, 100);
    const restored = new SeededRng(1);
    restored.setState(state);
    expect(restored.randint(1, 100)).toBe(a);
  });
});
