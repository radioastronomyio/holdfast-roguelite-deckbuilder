/** @vitest-environment happy-dom */

import { describe, expect, it } from "vitest";
import { createCardArt } from "./cardArt";
import { CARD_ART_SYMBOLS } from "./cardMap";

describe("createCardArt", () => {
  it("builds the complete five-layer inline SVG scene in its locked paint order", () => {
    const art = createCardArt({ motif: "crossed-swords", palette: "danger", ground: "stone" });

    expect(art.tagName.toLowerCase()).toBe("svg");
    expect(art.getAttribute("viewBox")).toBe("0 0 600 400");
    expect(art.querySelector("linearGradient")).not.toBeNull();
    expect(
      Array.from(art.children)
        .filter((child) => child.classList.length > 0)
        .map((child) => child.getAttribute("class")),
    ).toEqual([
      "hf-card-art__sky",
      "hf-card-art__glow",
      "hf-card-art__motif",
      "hf-card-art__ground hf-card-art__ground--stone",
      "hf-card-art__vignette",
    ]);
    expect(art.querySelector(".hf-card-art__ground")?.tagName.toLowerCase()).toBe("path");
    expect(art.querySelector(".hf-card-art__motif")?.tagName.toLowerCase()).toBe("use");
  });

  it("binds every curated motif through a currentColor symbol slot", () => {
    for (const motif of CARD_ART_SYMBOLS) {
      const art = createCardArt({ motif, palette: "primary", ground: "arcane" });
      const symbol = art.querySelector(".hf-card-art__motif");
      expect(symbol?.getAttribute("href"), motif).toBe(
        `/assets/card-art-icons/${motif}.svg#icon`,
      );
      expect(symbol?.getAttribute("fill"), motif).toBe("currentColor");
    }
  });

  it("records the selected palette as a semantic class", () => {
    const art = createCardArt({ motif: "ice-bolt", palette: "info", ground: "ice" });
    expect(art.classList.contains("hf-card-art--info")).toBe(true);
  });
});
