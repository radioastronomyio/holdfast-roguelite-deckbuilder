/**
 * Encounter placeholder — ENCOUNTER_ACTIVE / ENCOUNTER_TRANSITION.
 *
 * @module ui/screens/encounter
 */

import type { ScreenDefinition } from "./shared";
import { makePanel, readoutLine } from "./shared";

export const encounterScreen: ScreenDefinition = {
  name: "encounter",
  render(ctx) {
    const { stepper } = ctx;
    const snap = stepper.toJSON();
    const regionIndex = stepper.selectedRegionIndex ?? 0;
    const region = stepper.state.region_states[regionIndex];
    const encounters = region?.region.encounters.length ?? 0;
    const lines = stepper.selectedPartyIds.map((id) => {
      const character = stepper.state.roster.find((c) => c.id === id);
      return `Deployed: ${character?.name ?? id}`;
    });
    return makePanel({
      accent: "danger",
      title: "Encounter",
      readout: `${region?.region.name ?? "Region"} · encounter ${snap.encounterIndex + 1}/${encounters}`,
      body: [
        readoutLine(`Phase: ${stepper.phase}`),
        ...lines.map(readoutLine),
        readoutLine("Combat renders in spec 03. This placeholder auto-resolves the encounter on advance."),
      ],
      advanceLabel: "Resolve Encounter",
      advanceAccent: "danger",
      onAdvance: ctx.advance,
    });
  },
};
