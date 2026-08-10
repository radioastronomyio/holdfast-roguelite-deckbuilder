/** Parametric, zero-raster SVG scene used by every Holdfast card. */

import type { CardAccent } from "../gameui";
import { cardArtIconUrl } from "./cardMap";
import type { CardArtSymbol } from "./cardMap";

const SVG_NS = "http://www.w3.org/2000/svg";
let artId = 0;

export interface CardArtOptions {
  motif: CardArtSymbol;
  palette: CardAccent;
}

function svgNode<K extends keyof SVGElementTagNameMap>(tag: K): SVGElementTagNameMap[K] {
  return document.createElementNS(SVG_NS, tag);
}

/** Build a compact inline SVG viewport that references one curated symbol. */
export function createCardSymbol(
  motif: CardArtSymbol,
  className: string,
): SVGSVGElement {
  const svg = svgNode("svg");
  svg.classList.add(className);
  svg.setAttribute("viewBox", "0 0 512 512");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");

  const symbol = svgNode("use");
  symbol.setAttribute("href", cardArtIconUrl(motif));
  symbol.setAttribute("fill", "currentColor");
  svg.appendChild(symbol);
  return svg;
}

export function createCardArt({ motif, palette }: CardArtOptions): SVGSVGElement {
  const id = artId++;
  const skyId = `hf-card-sky-${id}`;
  const vignetteId = `hf-card-vignette-${id}`;

  const svg = svgNode("svg");
  svg.classList.add("hf-card-art", `hf-card-art--${palette}`);
  svg.setAttribute("viewBox", "0 0 600 400");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${motif.replaceAll("-", " ")} card art`);
  svg.setAttribute("data-motif", motif);
  svg.setAttribute("data-palette", palette);

  const defs = svgNode("defs");
  const skyGradient = svgNode("linearGradient");
  skyGradient.id = skyId;
  skyGradient.setAttribute("x1", "0");
  skyGradient.setAttribute("y1", "0");
  skyGradient.setAttribute("x2", "0");
  skyGradient.setAttribute("y2", "1");
  const skyBase = svgNode("stop");
  skyBase.classList.add("hf-card-art__sky-stop", "hf-card-art__sky-stop--base");
  skyBase.setAttribute("offset", "0");
  const skyAccent = svgNode("stop");
  skyAccent.classList.add("hf-card-art__sky-stop", "hf-card-art__sky-stop--accent");
  skyAccent.setAttribute("offset", "1");
  skyGradient.append(skyBase, skyAccent);

  const vignetteGradient = svgNode("radialGradient");
  vignetteGradient.id = vignetteId;
  const clear = svgNode("stop");
  clear.classList.add("hf-card-art__vignette-stop", "hf-card-art__vignette-stop--clear");
  clear.setAttribute("offset", "0.52");
  const dark = svgNode("stop");
  dark.classList.add("hf-card-art__vignette-stop", "hf-card-art__vignette-stop--dark");
  dark.setAttribute("offset", "1");
  vignetteGradient.append(clear, dark);
  defs.append(skyGradient, vignetteGradient);

  const sky = svgNode("rect");
  sky.classList.add("hf-card-art__sky");
  sky.setAttribute("width", "600");
  sky.setAttribute("height", "400");
  sky.setAttribute("fill", `url(#${skyId})`);

  const ground = svgNode("path");
  ground.classList.add("hf-card-art__ground");
  ground.setAttribute(
    "d",
    "M0 302 C72 270 123 296 181 269 C252 235 318 287 374 258 C446 220 514 266 600 230 L600 400 L0 400 Z",
  );

  const symbol = svgNode("use");
  symbol.classList.add("hf-card-art__symbol");
  symbol.setAttribute("href", cardArtIconUrl(motif));
  symbol.setAttribute("x", "172");
  symbol.setAttribute("y", "74");
  symbol.setAttribute("width", "256");
  symbol.setAttribute("height", "256");
  symbol.setAttribute("fill", "currentColor");

  const vignette = svgNode("rect");
  vignette.classList.add("hf-card-art__vignette");
  vignette.setAttribute("width", "600");
  vignette.setAttribute("height", "400");
  vignette.setAttribute("fill", `url(#${vignetteId})`);

  svg.append(defs, sky, ground, symbol, vignette);
  return svg;
}
