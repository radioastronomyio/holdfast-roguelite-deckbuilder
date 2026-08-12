/** DEV gallery integration tests over the complete shared card catalog.
 *
 * @vitest-environment happy-dom
 */

import { afterEach, describe, expect, it, vi } from "vitest";
import baseCards from "../../../../data/cards/base-cards.json";
import hazardCards from "../../../../data/cards/hazard-cards.json";
import upgradeTrees from "../../../../data/cards/upgrade-trees.json";
import { renderCardGallery } from "./card-gallery";

const responses: Record<string, unknown> = {
  "data/cards/base-cards.json": baseCards,
  "data/cards/hazard-cards.json": hazardCards,
  "data/cards/upgrade-trees.json": upgradeTrees,
};

function installCatalogFetch(): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string | URL | Request) => {
      const path = String(input).replace(/^\//, "");
      const body = responses[path];
      if (!body) return { ok: false, status: 404, json: async () => ({}) };
      return { ok: true, status: 200, json: async () => body };
    }),
  );
}

describe("renderCardGallery", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("renders the complete 21-card JSON catalog exactly once", async () => {
    installCatalogFetch();
    const gallery = await renderCardGallery();
    const catalog = gallery.querySelector<HTMLElement>(".hf-gallery__catalog");
    const cards = Array.from(
      catalog?.querySelectorAll<HTMLElement>(".hf-card[data-card-id]") ?? [],
    );

    expect(catalog?.dataset.galleryCardCount).toBe("21");
    expect(cards).toHaveLength(21);
    expect(new Set(cards.map(({ dataset }) => dataset.cardId)).size).toBe(21);
    const artByCardId = Object.fromEntries(cards.map((card): [string, string] => [
      card.dataset.cardId ?? "",
      card.querySelector(".hf-card-art image")?.getAttribute("href") ?? "",
    ]));
    expect(artByCardId.immolate_01).toBe("/assets/card-icons/immolate-fireball.png");
    expect(Object.entries(artByCardId)
      .filter(([cardId]) => cardId !== "immolate_01")
      .every(([, href]) => /\/assets\/card-icons\/.+\.svg$/.test(href)))
      .toBe(true);
    expect(cards.every((card) => card.querySelector(".hf-card-badge--cost"))).toBe(true);
    expect(
      cards.every((card) =>
        Array.from(card.querySelectorAll(".hf-card-art > [class^='hf-card-art__']"))
          .map((layer) => layer.getAttribute("class")?.split(" ")[0])
          .join("|") ===
        "hf-card-art__sky|hf-card-art__glow|hf-card-art__motif|hf-card-art__ground|hf-card-art__vignette",
      ),
    ).toBe(true);
  });

  it("reserves the only gallery shine for the upgraded exemplar", async () => {
    installCatalogFetch();
    const gallery = await renderCardGallery();

    expect(gallery.querySelectorAll(".hf-gallery__catalog .hf-card--shine")).toHaveLength(0);
    expect(gallery.querySelectorAll(".hf-gallery__pair .hf-card--shine")).toHaveLength(1);
    expect(
      gallery.querySelector(".hf-gallery__pair .hf-card--shine")?.getAttribute("data-upgrade-tier"),
    ).toBe("2");
  });

  it("includes an accessible zero-raster card-back specimen", async () => {
    installCatalogFetch();
    const gallery = await renderCardGallery();
    const cardBack = gallery.querySelector<HTMLElement>(".hf-gallery__card-back .hf-card-back");

    expect(cardBack?.getAttribute("aria-label")).toBe("Holdfast card back");
    expect(cardBack?.querySelector(".hf-card-back__pattern")).not.toBeNull();
    expect(cardBack?.querySelector(".hf-card-back__emblem")).not.toBeNull();
    expect(cardBack?.querySelectorAll("img, image")).toHaveLength(0);
  });
});
