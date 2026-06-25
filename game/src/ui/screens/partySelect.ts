/**
 * Party select placeholder — PARTY_SELECT.
 *
 * @module ui/screens/partySelect
 */

import { STAT_SCALE } from "../../sim/types";
import { partySize } from "../../sim/campaign";
import type { ScreenDefinition } from "./shared";
import { makePanel, readoutLine } from "./shared";

export const partySelectScreen: ScreenDefinition = {
  name: "party-select",
  render(ctx) {
    const { state } = ctx.stepper;
    const allowed = partySize(state);
    const lines = state.roster.map((c, i) => {
      const hp = Math.floor(c.base_stats.HP / STAT_SCALE);
      return `${i + 1}. ${c.name} — HP ${hp}${i < allowed ? " (selected)" : ""}`;
    });
    return makePanel({
      accent: "success",
      title: "Party Select",
      readout: `Roster ${state.roster.length} · party size ${allowed}`,
      body: lines.map(readoutLine),
      advanceLabel: "Deploy Party",
      advanceAccent: "success",
      onAdvance: ctx.advance,
    });
  },
};
