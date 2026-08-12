/** @vitest-environment happy-dom */

import { describe, expect, it } from "vitest";
import { createHoldfastCardBack } from "./cardBack";

describe("createHoldfastCardBack", () => {
  it("renders an accessible, SVG-only Runic card back with its distinct anatomy", () => {
    const back = createHoldfastCardBack();

    expect(back.tagName.toLowerCase()).toBe("article");
    expect(back.classList.contains("hf-card-back")).toBe(true);
    expect(back.classList.contains("hf-card-back--magic")).toBe(true);
    expect(back.getAttribute("role")).toBe("img");
    expect(back.getAttribute("aria-label")).toBe("Holdfast card back");
    expect(back.querySelector(".hf-card-back__pattern pattern")).not.toBeNull();
    const emblem = back.querySelector(".hf-card-back__emblem image");
    expect(emblem?.getAttribute("href")).toBe("/assets/card-icons/arcane_burst.svg");
    expect(emblem?.getAttribute("data-runic-mode")).toBe("rune");
    expect(back.querySelectorAll("img, image[href$='.png']")).toHaveLength(0);
  });

  it("gives each repeated SVG field an isolated pattern reference", () => {
    const first = createHoldfastCardBack();
    const second = createHoldfastCardBack();
    const firstId = first.querySelector(".hf-card-back__pattern pattern")?.id;
    const secondId = second.querySelector(".hf-card-back__pattern pattern")?.id;

    expect(firstId).toMatch(/^hf-card-back-runes-/);
    expect(secondId).toMatch(/^hf-card-back-runes-/);
    expect(firstId).not.toBe(secondId);
  });
});
