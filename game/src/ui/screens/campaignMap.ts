/**
 * Campaign map placeholder — REGION_SELECT.
 *
 * @module ui/screens/campaignMap
 */

import type { ScreenDefinition } from "./shared";
import { makePanel, readoutLine } from "./shared";

export const campaignMapScreen: ScreenDefinition = {
  name: "campaign-map",
  render(ctx) {
    const { state } = ctx.stepper;
    const lines = state.region_states.map(
      (r, i) => `${i + 1}. ${r.region.name} (difficulty ${r.assigned_difficulty})${r.conquered ? " — conquered" : ""}`,
    );
    return makePanel({
      accent: "info",
      title: "Campaign Map",
      readout: `Turn ${state.turn_number} · ${state.resources} resources`,
      body: lines.map(readoutLine),
      advanceLabel: "Assault Next Region",
      advanceAccent: "info",
      onAdvance: ctx.advance,
    });
  },
};
