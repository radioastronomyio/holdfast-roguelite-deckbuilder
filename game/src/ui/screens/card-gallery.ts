/**
 * DEV-only card gallery route.
 *
 * Renders every base and hazard card in the shared JSON as a Holdfast card in
 * dark-fantasy, plus a base-versus-upgraded exemplar so the gem and shine
 * overlay are visible in the baseline. The gallery is a standalone showcase:
 * it has no combat dependency and no CampaignStepper. It is gated behind
 * `import.meta.env.DEV` at the router, so it is stripped from production
 * builds entirely.
 *
 * @module ui/screens/card-gallery
 */

import type { Card, UpgradeTree } from "../../sim/types";
import { createHoldfastCard } from "../cards/holdfastCard";

const BASE = import.meta.env.BASE_URL;

async function fetchJson<T>(relativePath: string): Promise<T> {
  const response = await fetch(`${BASE}${relativePath}`);
  if (!response.ok) throw new Error(`Failed to load ${relativePath}: ${response.status}`);
  return (await response.json()) as T;
}

/**
 * Build and return the gallery main-viewport element: every base card, every
 * hazard card, and a base-vs-upgraded pair. Mounted inside the GameUI shell by
 * the router's DEV-gated `showCardGallery`.
 */
export async function renderCardGallery(): Promise<HTMLElement> {
  const [baseCards, hazardCards, upgradeTrees] = await Promise.all([
    fetchJson<Card[]>("data/cards/base-cards.json"),
    fetchJson<Card[]>("data/cards/hazard-cards.json"),
    fetchJson<Record<string, UpgradeTree>>("data/cards/upgrade-trees.json"),
  ]);

  const root = document.createElement("div");
  root.className = "hf-gallery";

  const catalog = document.createElement("div");
  catalog.className = "hf-gallery__catalog";
  catalog.dataset.galleryCardCount = String(baseCards.length + hazardCards.length);
  catalog.appendChild(buildSection("Base Cards", baseCards, upgradeTrees));
  catalog.appendChild(buildSection("Hazard Cards", hazardCards, upgradeTrees));

  root.appendChild(catalog);
  root.appendChild(buildUpgradedExemplar(baseCards, upgradeTrees));

  return root;
}

function buildSection(title: string, cards: Card[], trees: Record<string, UpgradeTree>): HTMLElement {
  const section = document.createElement("section");
  section.className = "hf-gallery__section";

  const heading = document.createElement("h2");
  heading.className = "hf-gallery__heading";
  heading.textContent = `${title} (${cards.length})`;
  section.appendChild(heading);

  const grid = document.createElement("div");
  grid.className = "hf-gallery__grid";
  for (const card of cards) {
    const control = createHoldfastCard(card, { upgradeTree: trees[card.id], selectable: true });
    grid.appendChild(control.el);
  }
  section.appendChild(grid);
  return section;
}

/**
 * Build the base-versus-upgraded exemplar: the same card rendered as a base
 * (tier 0) and as an upgraded tier-2 card, side by side, so the gem and accent
 * shine are visible in the dark-fantasy baseline.
 */
function buildUpgradedExemplar(baseCards: Card[], trees: Record<string, UpgradeTree>): HTMLElement {
  const section = document.createElement("section");
  section.className = "hf-gallery__section";

  const heading = document.createElement("h2");
  heading.className = "hf-gallery__heading";
  heading.textContent = "Base vs Upgraded";
  section.appendChild(heading);

  const pair = document.createElement("div");
  pair.className = "hf-gallery__pair";

  const base = baseCards[0];
  const upgraded: Card = { ...base, upgrade_tier: 2, name: `${base.name} +2` };

  pair.appendChild(wrapLabel("Base", createHoldfastCard(base, { upgradeTree: trees[base.id] }).el));
  pair.appendChild(wrapLabel("Upgraded (+2)", createHoldfastCard(upgraded, { upgradeTree: trees[base.id] }).el));

  section.appendChild(pair);
  return section;
}

function wrapLabel(label: string, cardEl: HTMLElement): HTMLElement {
  const wrap = document.createElement("div");
  wrap.className = "hf-gallery__labeled";
  const cap = document.createElement("div");
  cap.className = "hf-gallery__label";
  cap.textContent = label;
  wrap.append(cap, cardEl);
  return wrap;
}
