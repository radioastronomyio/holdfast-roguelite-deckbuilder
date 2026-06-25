/**
 * Main menu placeholder — the boot screen.
 *
 * @module ui/screens/mainMenu
 */

import type { ScreenDefinition } from "./shared";
import { makePanel, readoutLine } from "./shared";

export const mainMenuScreen: ScreenDefinition = {
  name: "main-menu",
  render(ctx) {
    const { stepper } = ctx;
    const conquered = stepper.state.region_states.filter((r) => r.conquered).length;
    return makePanel({
      accent: "primary",
      title: "Holdfast",
      readout: `Seed ${stepper.seed} · ${conquered}/6 regions conquered`,
      body: [readoutLine("A roguelite deckbuilder on the dark-fantasy frontier. Six regions stand between you and victory.")],
      advanceLabel: "Begin Campaign",
      advanceAccent: "primary",
      onAdvance: ctx.advance,
    });
  },
};
