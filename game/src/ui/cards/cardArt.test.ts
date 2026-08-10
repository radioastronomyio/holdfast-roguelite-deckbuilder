/** @vitest-environment happy-dom */

import { describe, expect, it } from "vitest";
import { createCardArt } from "./cardArt";
import { CARD_ART_SYMBOLS } from "./cardMap";

describe("createCardArt", () => {
  it("builds the complete four-layer inline SVG scene", () => {
    const art = createCardArt({ motif: "crossed-swords", palette: "danger" });

    expect(art.tagName.toLowerCase()).toBe("svg");
    expect(art.getAttribute("viewBox")).toBe("0 0 600 400");
    expect(art.querySelector("linearGradient")).not.toBeNull();
    expect(art.querySelector(".hf-card-art__sky")).not.toBeNull();
    expect(art.querySelector(".hf-card-art__ground")?.tagName.toLowerCase()).toBe("path");
    expect(art.querySelector(".hf-card-art__symbol")?.tagName.toLowerCase()).toBe("use");
    expect(art.querySelector(".hf-card-art__vignette")).not.toBeNull();
  });

  it("binds every curated motif through a currentColor symbol slot", () => {
    for (const motif of CARD_ART_SYMBOLS) {
      const art = createCardArt({ motif, palette: "primary" });
      const symbol = art.querySelector(".hf-card-art__symbol");
      expect(symbol?.getAttribute("href"), motif).toBe(
        `/assets/card-art-icons/${motif}.svg#icon`,
      );
      expect(symbol?.getAttribute("fill"), motif).toBe("currentColor");
    }
  });

  it("records the selected palette as a semantic class", () => {
    const art = createCardArt({ motif: "ice-bolt", palette: "info" });
    expect(art.classList.contains("hf-card-art--info")).toBe(true);
  });
});
