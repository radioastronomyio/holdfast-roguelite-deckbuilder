/**
 * World phase placeholder — WORLD_PHASE / RESEARCH_PHASE.
 *
 * @module ui/screens/world
 */

import { CampaignStepperPhase } from "../../sim/campaignStepper";
import type { ScreenDefinition } from "./shared";
import { makePanel, readoutLine } from "./shared";

export const worldScreen: ScreenDefinition = {
  name: "world",
  render(ctx) {
    const { stepper } = ctx;
    const isWorld = stepper.phase === CampaignStepperPhase.WORLD_PHASE;
    const snap = stepper.toJSON();
    return makePanel({
      accent: "pink",
      title: isWorld ? "World Phase" : "Research Phase",
      readout: `Skip tokens ${stepper.state.skip_tokens} · ${stepper.phase}`,
      body: [
        readoutLine(
          isWorld
            ? `${snap.worldCandidates.length} world card(s) offered. Accept applies its modifiers.`
            : "Research layers unlock region information. This placeholder ends the phase on advance.",
        ),
        readoutLine("The world screen (spec 04) replaces this placeholder."),
      ],
      advanceLabel: isWorld ? "Accept World Card" : "End Research",
      advanceAccent: "pink",
      onAdvance: ctx.advance,
    });
  },
};
