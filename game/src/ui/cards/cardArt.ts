/** Parametric SVG scene whose motif source may be a presentation-mapped SVG or PNG. */

import type { CardAccent } from "../gameui";
import { cardArtUrl, cardIconUrl } from "./cardMap";
import type { CardArtGround, CardArtSource, CardArtSymbol } from "./cardMap";

const SVG_NS = "http://www.w3.org/2000/svg";
let artId = 0;

export interface CardArtOptions {
  motif: CardArtSymbol;
  palette: CardAccent;
  ground: CardArtGround;
  artSource?: CardArtSource;
}

const GROUND_PATH: Record<CardArtGround, string> = {
  arcane: "M0 352 C68 326 112 350 178 330 C249 320 312 348 382 328 C450 320 518 344 600 324 L600 400 L0 400 Z",
  ash: "M0 350 L74 340 L136 352 L210 326 L292 348 L365 322 L444 344 L520 320 L600 336 L600 400 L0 400 Z",
  ice: "M0 352 L84 334 L151 348 L241 320 L332 346 L424 324 L511 342 L600 320 L600 400 L0 400 Z",
  marsh: "M0 354 C68 340 111 360 172 342 C243 324 303 356 369 338 C437 320 521 350 600 334 L600 400 L0 400 Z",
  ruin: "M0 352 L72 340 L126 354 L170 324 L235 346 L296 320 L359 348 L420 330 L489 352 L548 334 L600 344 L600 400 L0 400 Z",
  stone: "M0 350 L92 336 L168 350 L246 328 L322 346 L404 322 L481 340 L600 320 L600 400 L0 400 Z",
  thicket: "M0 356 C52 326 108 356 160 332 C218 320 282 356 341 328 C403 320 462 350 523 326 C550 320 573 332 600 320 L600 400 L0 400 Z",
};

function svgNode<K extends keyof SVGElementTagNameMap>(tag: K): SVGElementTagNameMap[K] {
  return document.createElementNS(SVG_NS, tag);
}

/** Build a compact inline SVG viewport that references one curated symbol. */
export function createCardSymbol(
  motif: CardArtSymbol,
  className: string,
): HTMLImageElement {
  const image = document.createElement("img");
  image.classList.add(className);
  image.src = cardIconUrl(motif, "svg");
  image.alt = "";
  image.setAttribute("aria-hidden", "true");
  image.draggable = false;
  return image;
}

export function createCardArt({
  motif,
  palette,
  ground: groundType,
  artSource = "svg",
}: CardArtOptions): SVGSVGElement {
  const id = artId++;
  const skyId = `hf-card-sky-${id}`;
  const glowId = `hf-card-glow-${id}`;
  const vignetteId = `hf-card-vignette-${id}`;

  const svg = svgNode("svg");
  svg.classList.add("hf-card-art", `hf-card-art--${palette}`);
  svg.setAttribute("viewBox", "0 0 600 400");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", `${motif.replaceAll("-", " ")} card art`);
  svg.setAttribute("data-motif", motif);
  svg.setAttribute("data-palette", palette);
  svg.setAttribute("data-art-source", artSource);

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

  const glowGradient = svgNode("radialGradient");
  glowGradient.id = glowId;
  const glowCore = svgNode("stop");
  glowCore.classList.add("hf-card-art__glow-stop", "hf-card-art__glow-stop--core");
  glowCore.setAttribute("offset", "0");
  const glowFade = svgNode("stop");
  glowFade.classList.add("hf-card-art__glow-stop", "hf-card-art__glow-stop--fade");
  glowFade.setAttribute("offset", "1");
  glowGradient.append(glowCore, glowFade);

  const vignetteGradient = svgNode("radialGradient");
  vignetteGradient.id = vignetteId;
  const clear = svgNode("stop");
  clear.classList.add("hf-card-art__vignette-stop", "hf-card-art__vignette-stop--clear");
  clear.setAttribute("offset", "0.52");
  const dark = svgNode("stop");
  dark.classList.add("hf-card-art__vignette-stop", "hf-card-art__vignette-stop--dark");
  dark.setAttribute("offset", "1");
  vignetteGradient.append(clear, dark);
  defs.append(skyGradient, glowGradient, vignetteGradient);

  const sky = svgNode("rect");
  sky.classList.add("hf-card-art__sky");
  sky.setAttribute("width", "600");
  sky.setAttribute("height", "400");
  sky.setAttribute("fill", `url(#${skyId})`);

  const glow = svgNode("ellipse");
  glow.classList.add("hf-card-art__glow");
  glow.setAttribute("cx", "300");
  glow.setAttribute("cy", "180");
  glow.setAttribute("rx", "210");
  glow.setAttribute("ry", "175");
  glow.setAttribute("fill", `url(#${glowId})`);

  const motifLayer = svgNode("image");
  motifLayer.classList.add("hf-card-art__motif");
  motifLayer.setAttribute("data-art-source", artSource);
  motifLayer.setAttribute("href", cardArtUrl(motif, artSource));
  motifLayer.setAttribute("x", "146");
  motifLayer.setAttribute("y", "18");
  motifLayer.setAttribute("width", "308");
  motifLayer.setAttribute("height", "308");
  motifLayer.setAttribute("preserveAspectRatio", "xMidYMid meet");

  const ground = svgNode("path");
  ground.classList.add("hf-card-art__ground", `hf-card-art__ground--${groundType}`);
  ground.setAttribute("d", GROUND_PATH[groundType]);

  const vignette = svgNode("rect");
  vignette.classList.add("hf-card-art__vignette");
  vignette.setAttribute("width", "600");
  vignette.setAttribute("height", "400");
  vignette.setAttribute("fill", `url(#${vignetteId})`);

  svg.append(defs, sky, glow, ground, motifLayer, vignette);
  return svg;
}
