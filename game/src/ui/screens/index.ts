/**
 * Placeholder screen registry — one module per campaign-stepper phase.
 *
 * @module ui/screens
 */

import type { ScreenDefinition, ScreenName } from "./shared";
import { mainMenuScreen } from "./mainMenu";
import { campaignMapScreen } from "./campaignMap";
import { partySelectScreen } from "./partySelect";
import { encounterScreen } from "./encounter";
import { rewardScreen } from "./reward";
import { worldScreen } from "./world";
import { gameOverScreen } from "./gameOver";

export type { ScreenName, ScreenContext, ScreenDefinition } from "./shared";

export const SCREENS: Record<ScreenName, ScreenDefinition> = {
  "main-menu": mainMenuScreen,
  "campaign-map": campaignMapScreen,
  "party-select": partySelectScreen,
  encounter: encounterScreen,
  reward: rewardScreen,
  world: worldScreen,
  "game-over": gameOverScreen,
};
