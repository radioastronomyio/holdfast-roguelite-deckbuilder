/**
 * Game over placeholder — VICTORY / DEFEAT.
 *
 * @module ui/screens/gameOver
 */

import { CampaignStepperPhase } from "../../sim/campaignStepper";
import type { ScreenDefinition } from "./shared";
import { makePanel, readoutLine } from "./shared";

export const gameOverScreen: ScreenDefinition = {
  name: "game-over",
  render(ctx) {
    const { stepper } = ctx;
    const isVictory = stepper.phase === CampaignStepperPhase.VICTORY;
    const conquered = stepper.state.region_states.filter((r) => r.conquered).length;
    return makePanel({
      accent: isVictory ? "success" : "danger",
      title: isVictory ? "Victory" : "Defeat",
      readout: `Seed ${stepper.seed} · ${conquered}/6 regions conquered · turn ${stepper.state.turn_number}`,
      body: [
        readoutLine(
          isVictory
            ? "All six regions are conquered. The campaign is won."
            : "The party has fallen. The campaign is lost.",
        ),
        readoutLine("The game-over screen (spec 04) replaces this placeholder."),
      ],
      advanceLabel: "Run Complete",
      terminal: true,
      onAdvance: ctx.advance,
    });
  },
};
