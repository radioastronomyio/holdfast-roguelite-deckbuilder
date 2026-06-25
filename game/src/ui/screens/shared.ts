/**
 * Shared helpers and types for placeholder screens.
 *
 * @module ui/screens/shared
 */

import type { CampaignStepper } from "../../sim/campaignStepper";
import { createButton } from "../gameui";

export type ScreenName =
  | "main-menu"
  | "campaign-map"
  | "party-select"
  | "encounter"
  | "reward"
  | "world"
  | "game-over";

export interface ScreenContext {
  stepper: CampaignStepper;
  advance: () => void;
}

export interface ScreenDefinition {
  name: ScreenName;
  render: (ctx: ScreenContext) => HTMLElement;
}

type Accent = "primary" | "success" | "warning" | "danger" | "info" | "magic" | "pink";

export interface PanelOptions {
  accent?: Accent;
  title: string;
  readout: string;
  body?: HTMLElement[];
  advanceLabel: string;
  advanceAccent?: Accent;
  onAdvance: () => void;
  terminal?: boolean;
}

/**
 * Build a `.gui-panel` placeholder: title, a one-line state readout drawn from
 * the stepper, an optional body, and a primary `.gui-btn` that advances the
 * campaign. Composed entirely from GameUI structure classes.
 */
export function makePanel(opts: PanelOptions): HTMLElement {
  const panel = document.createElement("div");
  panel.className = `gui-panel gui-panel--${opts.accent ?? "primary"}`;

  const header = document.createElement("div");
  header.className = "gui-panel__header";
  const title = document.createElement("div");
  title.className = "gui-panel__title";
  title.textContent = opts.title;
  header.appendChild(title);
  panel.appendChild(header);

  const subtitle = document.createElement("div");
  subtitle.className = "gui-panel__subtitle";
  subtitle.textContent = opts.readout;
  panel.appendChild(subtitle);

  const body = document.createElement("div");
  body.className = "gui-panel__body";
  if (opts.body) {
    for (const node of opts.body) body.appendChild(node);
  }
  panel.appendChild(body);

  const footer = document.createElement("div");
  footer.className = "gui-panel__footer";
  if (!opts.terminal) {
    const btn = createButton({
      label: opts.advanceLabel,
      accent: opts.advanceAccent ?? "primary",
      variant: "solid",
      onClick: opts.onAdvance,
    });
    btn.el.setAttribute("data-advance", "");
    footer.appendChild(btn.el);
  } else {
    const chip = document.createElement("span");
    chip.className = "gui-panel__chip gui-panel__chip--solid";
    chip.textContent = "Run complete";
    footer.appendChild(chip);
  }
  panel.appendChild(footer);

  return panel;
}

/** A muted readout line for the panel body. */
export function readoutLine(text: string): HTMLElement {
  const p = document.createElement("p");
  p.textContent = text;
  return p;
}
