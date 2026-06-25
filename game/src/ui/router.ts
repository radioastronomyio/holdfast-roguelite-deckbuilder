/**
 * Vanilla DOM screen router.
 *
 * Exposes `showScreen(name, stepper)` over a single root mount node. Each call
 * tears down the previous screen, composes a GameUI shell (header + status side
 * + main), and renders the requested placeholder screen inside the shell's main
 * viewport. The router is hand-rolled: no router library, no UI-framework
 * runtime dependency. The campaign stepper is authoritative for routing — the
 * advance callback drives the stepper and re-routes to the phase it returns.
 *
 * @module ui/router
 */

import type { CampaignStepper } from "../sim/campaignStepper";
import { createShell } from "./gameui";
import { defaultAdvance, phaseToScreen } from "./flow";
import { SCREENS, type ScreenName } from "./screens";

let mount: HTMLElement | null = null;
let renderNonce = 0;

export function initRouter(root: HTMLElement): void {
  mount = root;
}

const PHASE_LABEL: Record<ScreenName, string> = {
  "main-menu": "Main Menu",
  "campaign-map": "Campaign Map",
  "party-select": "Party Select",
  encounter: "Encounter",
  reward: "Reward",
  world: "World Phase",
  "game-over": "Game Over",
};

function buildStatusSide(stepper: CampaignStepper): HTMLElement {
  const panel = document.createElement("div");
  panel.className = "gui-panel gui-panel--primary";

  const header = document.createElement("div");
  header.className = "gui-panel__header";
  const title = document.createElement("div");
  title.className = "gui-panel__title";
  title.textContent = "Holdfast";
  header.appendChild(title);
  panel.appendChild(header);

  const body = document.createElement("div");
  body.className = "gui-panel__body";
  const conquered = stepper.state.region_states.filter((r) => r.conquered).length;
  const stats = [
    `Seed: ${stepper.seed}`,
    `Turn: ${stepper.state.turn_number}`,
    `Regions: ${conquered}/6`,
    `Resources: ${stepper.state.resources}`,
    `Phase: ${stepper.phase}`,
  ];
  for (const line of stats) {
    const p = document.createElement("p");
    p.textContent = line;
    body.appendChild(p);
  }
  panel.appendChild(body);
  return panel;
}

function buildHeader(name: ScreenName): HTMLElement {
  const bar = document.createElement("div");
  bar.style.display = "flex";
  bar.style.gap = "var(--gui-space-md)";
  bar.style.alignItems = "baseline";
  const brand = document.createElement("strong");
  brand.textContent = "HOLDFAST";
  brand.style.fontFamily = "var(--gui-font-display)";
  brand.style.letterSpacing = "0.08em";
  const phase = document.createElement("span");
  phase.textContent = PHASE_LABEL[name];
  phase.style.color = "var(--gui-text-muted)";
  bar.append(brand, phase);
  return bar;
}

export function showScreen(name: ScreenName, stepper: CampaignStepper): void {
  if (!mount) throw new Error("Router not initialised. Call initRouter(root) first.");

  // Tear down the previous screen.
  mount.innerHTML = "";

  const advance = (): void => {
    if (name === "main-menu") {
      showScreen(phaseToScreen(stepper.phase), stepper);
    } else {
      defaultAdvance(stepper);
      showScreen(phaseToScreen(stepper.phase), stepper);
    }
  };

  const screen = SCREENS[name];
  const panel = screen.render({ stepper, advance });

  const shell = createShell({
    side: "left",
    sideWidth: "300px",
    sideLabel: "Campaign status",
    header: buildHeader(name),
    sideContent: buildStatusSide(stepper),
    mainContent: panel,
  });
  shell.main.setAttribute("data-screen", name);
  shell.main.setAttribute("data-render", String(++renderNonce));
  mount.appendChild(shell.el);
}
