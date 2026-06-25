/**
 * Reward placeholder — POST_CONQUEST_UPGRADES / POST_CONQUEST_DRAFT.
 *
 * @module ui/screens/reward
 */

import { CampaignStepperPhase } from "../../sim/campaignStepper";
import type { ScreenDefinition } from "./shared";
import { makePanel, readoutLine } from "./shared";

export const rewardScreen: ScreenDefinition = {
  name: "reward",
  render(ctx) {
    const { stepper } = ctx;
    const isUpgrade = stepper.phase === CampaignStepperPhase.POST_CONQUEST_UPGRADES;
    const snap = stepper.toJSON();
    return makePanel({
      accent: "magic",
      title: isUpgrade ? "Upgrade" : "Recruit",
      readout: `${stepper.phase} · ${stepper.state.resources} resources`,
      body: [
        readoutLine(
          isUpgrade
            ? "Region conquered. Choose a card upgrade."
            : `Choose a recruit · ${snap.draftCandidates.length} candidates`,
        ),
        readoutLine("The card renderer (spec 02) and reward flow (spec 04) replace this placeholder."),
      ],
      advanceLabel: isUpgrade ? "Take First Upgrade" : "Recruit First Candidate",
      advanceAccent: "magic",
      onAdvance: ctx.advance,
    });
  },
};
