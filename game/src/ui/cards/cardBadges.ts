/** Inline-SVG energy badge and upgrade gem factories for Holdfast cards. */

const SVG_NS = "http://www.w3.org/2000/svg";
const MAX_UPGRADE_TIER = 3;

function svgElement<K extends keyof SVGElementTagNameMap>(
  tag: K,
  attributes: Record<string, string>,
): SVGElementTagNameMap[K] {
  const element = document.createElementNS(SVG_NS, tag);
  for (const [name, value] of Object.entries(attributes)) {
    element.setAttribute(name, value);
  }
  return element;
}

/** Render a card's display-scale energy cost as an accent-inheriting badge. */
export function createCostBadge(cost: number): SVGSVGElement {
  const badge = svgElement("svg", {
    class: "hf-card-badge hf-card-badge--cost",
    viewBox: "0 0 48 48",
    role: "img",
    "aria-label": `${cost} energy`,
  });
  badge.dataset.cost = String(cost);

  const rim = svgElement("circle", {
    class: "hf-card-badge__rim",
    cx: "24",
    cy: "24",
    r: "21",
    fill: "none",
    stroke: "currentColor",
  });
  const core = svgElement("path", {
    class: "hf-card-badge__core",
    d: "M24 6 40 18 34 39 14 39 8 18Z",
    fill: "currentColor",
  });
  const label = svgElement("text", {
    class: "hf-card-badge__label",
    x: "24",
    y: "31",
    "text-anchor": "middle",
  });
  label.textContent = String(cost);

  badge.append(rim, core, label);
  return badge;
}

/** Render upgrade_tier as a single gem with an explicit base/upgraded state. */
export function createUpgradeGem(tier: number): SVGSVGElement {
  const normalized = Math.min(Math.max(Math.trunc(tier), 0), MAX_UPGRADE_TIER);
  const gem = svgElement("svg", {
    class: `hf-card-gem hf-card-gem--tier-${normalized}`,
    viewBox: "0 0 48 48",
    role: "img",
    "aria-label": normalized === 0 ? "Base card" : `Upgrade tier ${normalized}`,
  });
  gem.dataset.upgradeTier = String(normalized);

  const stone = svgElement("polygon", {
    class: "hf-card-gem__stone",
    points: "24,3 43,17 36,41 12,41 5,17",
    fill: "currentColor",
    stroke: "currentColor",
  });
  const facet = svgElement("path", {
    class: "hf-card-gem__facet",
    d: "M5 17h38L24 41ZM24 3v38M12 41l12-25 12 25",
    fill: "none",
    stroke: "currentColor",
  });
  const numeral = svgElement("text", {
    class: "hf-card-gem__label",
    x: "24",
    y: "30",
    "text-anchor": "middle",
  });
  numeral.textContent = String(normalized);

  gem.append(stone, facet, numeral);
  return gem;
}
