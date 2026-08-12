/** Parametric vector-only card back, visually paired with the Holdfast front. */

import "./card.css";
import { cardIconUrl, RUNIC_ICON_MODES } from "./cardMap";

const SVG_NS = "http://www.w3.org/2000/svg";
let patternId = 0;
const BACK_EMBLEM = "arcane_burst" as const;

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

/** Render a face-down Holdfast card with an active-vocabulary Runic emblem. */
export function createHoldfastCardBack(): HTMLElement {
  const back = document.createElement("article");
  back.className = "hf-card-back hf-card-back--magic";
  back.setAttribute("role", "img");
  back.setAttribute("aria-label", "Holdfast card back");

  const pattern = createBackPattern();
  const emblem = createRunicEmblem();
  back.append(pattern, emblem);
  return back;
}

function createBackPattern(): SVGSVGElement {
  const runesId = `hf-card-back-runes-${patternId++}`;
  const pattern = svgElement("svg", {
    class: "hf-card-back__pattern",
    viewBox: "0 0 744 1200",
    "aria-hidden": "true",
    focusable: "false",
  });
  const defs = svgElement("defs", {});
  const runes = svgElement("pattern", {
    id: runesId,
    width: "96",
    height: "96",
    patternUnits: "userSpaceOnUse",
  });
  const knot = svgElement("path", {
    d: "M12 48 30 30 48 48 66 30 84 48 66 66 48 48 30 66Z M48 12v72 M12 48h72",
    fill: "none",
    stroke: "currentColor",
  });
  runes.appendChild(knot);
  defs.appendChild(runes);

  const field = svgElement("rect", {
    class: "hf-card-back__field",
    width: "744",
    height: "1200",
    fill: `url(#${runesId})`,
  });
  const innerFrame = svgElement("rect", {
    class: "hf-card-back__inner-frame",
    x: "36",
    y: "36",
    width: "672",
    height: "1128",
    rx: "24",
    fill: "none",
    stroke: "currentColor",
  });
  const seal = svgElement("path", {
    class: "hf-card-back__seal",
    d: "M372 212 515 355 372 498 229 355ZM372 702 515 845 372 988 229 845Z",
    fill: "none",
    stroke: "currentColor",
  });

  pattern.append(defs, field, innerFrame, seal);
  return pattern;
}

function createRunicEmblem(): SVGSVGElement {
  const emblem = svgElement("svg", {
    class: "hf-card-back__emblem",
    viewBox: "0 0 240 240",
    "data-runic-symbol": BACK_EMBLEM,
    "data-runic-mode": RUNIC_ICON_MODES[BACK_EMBLEM],
    "aria-hidden": "true",
    focusable: "false",
  });
  const outer = svgElement("polygon", {
    points: "120,12 211,65 211,175 120,228 29,175 29,65",
    fill: "none",
    stroke: "currentColor",
  });
  const rune = svgElement("image", {
    href: cardIconUrl(BACK_EMBLEM, "svg"),
    x: "24",
    y: "24",
    width: "192",
    height: "192",
    preserveAspectRatio: "xMidYMid meet",
    "data-runic-mode": RUNIC_ICON_MODES[BACK_EMBLEM],
  });
  emblem.append(outer, rune);
  return emblem;
}
