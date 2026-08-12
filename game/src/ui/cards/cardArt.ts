/** Parametric, zero-raster SVG scene used by every Holdfast card. */

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
  arcane: "M0 310 C68 264 112 302 178 258 C249 215 312 294 382 252 C450 211 518 280 600 236 L600 400 L0 400 Z",
  ash: "M0 298 L74 280 L136 302 L210 250 L292 287 L365 239 L444 276 L520 225 L600 248 L600 400 L0 400 Z",
  ice: "M0 305 L84 270 L151 294 L241 238 L332 288 L424 246 L511 275 L600 218 L600 400 L0 400 Z",
  marsh: "M0 314 C68 286 111 326 172 294 C243 262 303 318 369 284 C437 249 521 307 600 275 L600 400 L0 400 Z",
  ruin: "M0 308 L72 282 L126 306 L170 248 L235 284 L296 228 L359 290 L420 255 L489 302 L548 266 L600 286 L600 400 L0 400 Z",
  stone: "M0 304 L92 278 L168 302 L246 264 L322 293 L404 250 L481 282 L600 232 L600 400 L0 400 Z",
  thicket: "M0 315 C52 259 108 317 160 271 C218 223 282 316 341 260 C403 200 462 303 523 249 C550 225 573 245 600 223 L600 400 L0 400 Z",
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
  motifLayer.setAttribute("x", "172");
  motifLayer.setAttribute("y", "74");
  motifLayer.setAttribute("width", "256");
  motifLayer.setAttribute("height", "256");
  motifLayer.setAttribute("preserveAspectRatio", "xMidYMid meet");

  const ground = svgNode("path");
  ground.classList.add("hf-card-art__ground", `hf-card-art__ground--${groundType}`);
  ground.setAttribute("d", GROUND_PATH[groundType]);

  const vignette = svgNode("rect");
  vignette.classList.add("hf-card-art__vignette");
  vignette.setAttribute("width", "600");
  vignette.setAttribute("height", "400");
  vignette.setAttribute("fill", `url(#${vignetteId})`);

  svg.append(defs, sky, glow, motifLayer, ground, vignette);
  return svg;
}
