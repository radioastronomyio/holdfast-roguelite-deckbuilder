/**
 * Holdfast boot path.
 *
 * Parses a seed (default fixed), loads the shared game data, constructs a
 * CampaignStepper, and routes to the main-menu placeholder. The campaign
 * stepper is authoritative for which screen comes next; the router's advance
 * callback drives it and re-routes to the phase it returns.
 */

import { loadGameData } from "./data";
import { CampaignStepper } from "./sim/campaignStepper";
import { partySize } from "./sim/campaign";
import { initRouter, showScreen } from "./ui/router";

const DEFAULT_SEED = 12345;

async function main(): Promise<void> {
  const params = new URLSearchParams(window.location.search);
  const seedParam = params.get("seed");
  const seed = seedParam && Number.isFinite(Number.parseInt(seedParam, 10))
    ? Number.parseInt(seedParam, 10)
    : DEFAULT_SEED;

  const gameData = await loadGameData();
  const stepper = new CampaignStepper(seed, gameData);

  const root = document.getElementById("game-root");
  if (!root) throw new Error("#game-root mount node missing");
  initRouter(root);
  showScreen("main-menu", stepper);

  // Dev hook for the capture harness: reach the terminal game-over screen via a
  // fresh stepper driven to defeat. The natural walk reaches game-over only
  // after a full campaign; the world-modifier TS parity bug (see worklog)
  // currently blocks that path, so the harness captures game-over through here.
  interface HoldfastDevHook {
    showGameOver: () => void;
  }
  (window as unknown as { __holdfast?: HoldfastDevHook }).__holdfast = {
    showGameOver: () => {
      const s = new CampaignStepper(seed, gameData);
      const firstUnconquered = s.state.region_states.findIndex((r) => !r.conquered);
      s.selectRegion(firstUnconquered);
      const ids = s.state.roster.slice(0, partySize(s.state)).map((c) => c.id);
      s.selectParty(ids);
      s.completeEncounter({ playerWon: false, survivors: [] });
      showScreen("game-over", s);
    },
  };
}

void main().catch((error) => {
  // eslint-disable-next-line no-console
  console.error(error);
  const root = document.getElementById("game-root");
  if (root) {
    root.innerHTML = `<div class="gui-panel gui-panel--danger" style="margin:2rem"><div class="gui-panel__header"><div class="gui-panel__title">Boot failed</div></div><div class="gui-panel__body"><p>${String(error)}</p></div></div>`;
  }
});
