/** @vitest-environment happy-dom */

import { describe, expect, it } from "vitest";
import { createCardArt } from "./cardArt";
import { CARD_ART_GROUNDS, CARD_ART_SYMBOLS } from "./cardMap";

function pathYCoordinates(path: string): number[] {
  const coordinates = Array.from(path.matchAll(/-?\d+(?:\.\d+)?/g), ([value]) => Number(value));
  return coordinates.filter((_, index) => index % 2 === 1);
}

describe("createCardArt", () => {
  it("builds the complete five-layer inline SVG scene in its locked paint order", () => {
    const art = createCardArt({ motif: "crescent_blade", palette: "danger", ground: "stone" });

    expect(art.tagName.toLowerCase()).toBe("svg");
    expect(art.getAttribute("viewBox")).toBe("0 0 600 400");
    expect(art.querySelector("linearGradient")).not.toBeNull();
    expect(
      Array.from(art.children)
        .filter((child) => child.tagName.toLowerCase() !== "defs")
        .map((child) => child.getAttribute("class")),
    ).toEqual([
      "hf-card-art__sky",
      "hf-card-art__glow",
      "hf-card-art__ground hf-card-art__ground--stone",
      "hf-card-art__motif",
      "hf-card-art__vignette",
    ]);
    expect(art.querySelector(".hf-card-art__ground")?.tagName.toLowerCase()).toBe("path");
    expect(art.querySelector(".hf-card-art__motif")?.tagName.toLowerCase()).toBe("image");
  });

  it("keeps every ground peak at or below the lower 20 percent of the art band", () => {
    for (const ground of CARD_ART_GROUNDS) {
      const art = createCardArt({ motif: "crescent_blade", palette: "danger", ground });
      const path = art.querySelector(".hf-card-art__ground")?.getAttribute("d") ?? "";
      const visibleYs = pathYCoordinates(path).filter((value) => value < 400);

      expect(visibleYs.length, ground).toBeGreaterThan(0);
      expect(visibleYs.every(Number.isFinite), ground).toBe(true);
      expect(Math.min(...visibleYs), ground).toBeGreaterThanOrEqual(320);
    }
  });

  it("raises the motif centre to 43 percent and scales it up by about 20 percent", () => {
    const art = createCardArt({ motif: "crescent_blade", palette: "danger", ground: "stone" });
    const motif = art.querySelector(".hf-card-art__motif");
    const x = Number(motif?.getAttribute("x"));
    const y = Number(motif?.getAttribute("y"));
    const width = Number(motif?.getAttribute("width"));
    const height = Number(motif?.getAttribute("height"));

    expect(x + width / 2).toBe(300);
    expect(y + height / 2).toBeCloseTo(400 * 0.43, 0);
    expect(width / 256).toBeCloseTo(1.2, 1);
    expect(height).toBe(width);
  });

  it("binds every curated motif as a self-coloured derived SVG image", () => {
    for (const motif of CARD_ART_SYMBOLS) {
      const art = createCardArt({ motif, palette: "primary", ground: "arcane" });
      const symbol = art.querySelector(".hf-card-art__motif");
      expect(symbol?.getAttribute("href"), motif).toBe(
        `/assets/card-icons/${motif}.svg`,
      );
      expect(symbol?.getAttribute("fill"), motif).toBeNull();
    }
  });

  it("uses a derived SVG motif when no presentation source is supplied", () => {
    const art = createCardArt({ motif: "arcane_burst", palette: "primary", ground: "arcane" });
    const motif = art.querySelector(".hf-card-art__motif");

    expect(art.getAttribute("data-art-source")).toBe("svg");
    expect(motif?.getAttribute("data-art-source")).toBe("svg");
    expect(motif?.getAttribute("href")).toBe("/assets/card-icons/arcane_burst.svg");
  });

  it("uses the Immolate PNG inside the shared image motif layer", () => {
    const art = createCardArt({
      motif: "fireball",
      palette: "danger",
      ground: "ash",
      artSource: "image",
    });
    const motif = art.querySelector(".hf-card-art__motif");

    expect(art.getAttribute("data-art-source")).toBe("image");
    expect(motif?.tagName.toLowerCase()).toBe("image");
    expect(motif?.getAttribute("data-art-source")).toBe("image");
    expect(motif?.getAttribute("href")).toBe("/assets/card-icons/immolate-fireball.png");
  });

  it("records the selected palette as a semantic class", () => {
    const art = createCardArt({ motif: "frostbite", palette: "info", ground: "ice" });
    expect(art.classList.contains("hf-card-art--info")).toBe(true);
  });
});
