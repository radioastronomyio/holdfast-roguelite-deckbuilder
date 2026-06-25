/**
 * Campaign flow mapping and default stepper advance.
 *
 * The screen graph is the `CampaignStepperPhase` enum: each phase maps to a
 * placeholder screen, and the stepper is authoritative for which screen comes
 * next. `defaultAdvance` performs the placeholder's default choice for the
 * current phase (first region, full party, auto-win encounter, first upgrade,
 * first recruit, accept world card) so the walk proves the router + stepper
 * wiring without implementing real screen interaction.
 *
 * @module ui/flow
 */

import { CampaignStepper, CampaignStepperPhase } from "../sim/campaignStepper";
import { partySize } from "../sim/campaign";
import type { ScreenName } from "./screens";

export function phaseToScreen(phase: CampaignStepperPhase): ScreenName {
  switch (phase) {
    case CampaignStepperPhase.REGION_SELECT:
      return "campaign-map";
    case CampaignStepperPhase.PARTY_SELECT:
      return "party-select";
    case CampaignStepperPhase.ENCOUNTER_ACTIVE:
    case CampaignStepperPhase.ENCOUNTER_TRANSITION:
      return "encounter";
    case CampaignStepperPhase.POST_CONQUEST_UPGRADES:
    case CampaignStepperPhase.POST_CONQUEST_DRAFT:
      return "reward";
    case CampaignStepperPhase.WORLD_PHASE:
    case CampaignStepperPhase.RESEARCH_PHASE:
      return "world";
    case CampaignStepperPhase.VICTORY:
    case CampaignStepperPhase.DEFEAT:
      return "game-over";
  }
}

/**
 * Perform the placeholder's default advancing action for the stepper's current
 * phase. The stepper mutates to its next phase; the caller re-routes.
 */
export function defaultAdvance(stepper: CampaignStepper): void {
  switch (stepper.phase) {
    case CampaignStepperPhase.REGION_SELECT: {
      const index = stepper.state.region_states.findIndex((region) => !region.conquered);
      if (index >= 0) stepper.selectRegion(index);
      break;
    }
    case CampaignStepperPhase.PARTY_SELECT: {
      const ids = stepper.state.roster.slice(0, partySize(stepper.state)).map((character) => character.id);
      stepper.selectParty(ids);
      break;
    }
    case CampaignStepperPhase.ENCOUNTER_ACTIVE:
    case CampaignStepperPhase.ENCOUNTER_TRANSITION: {
      stepper.completeEncounter({ playerWon: true, survivors: [...stepper.selectedPartyIds] });
      break;
    }
    case CampaignStepperPhase.POST_CONQUEST_UPGRADES: {
      const trees = stepper.gameData.upgrade_trees;
      const cardId = Object.keys(trees)[0];
      const branch = Object.keys(trees[cardId])[0];
      stepper.selectUpgrade(cardId, branch);
      break;
    }
    case CampaignStepperPhase.POST_CONQUEST_DRAFT: {
      stepper.selectDraftCharacter(0);
      break;
    }
    case CampaignStepperPhase.WORLD_PHASE: {
      stepper.evaluateWorldCard(true);
      break;
    }
    case CampaignStepperPhase.RESEARCH_PHASE: {
      stepper.endResearch();
      break;
    }
    case CampaignStepperPhase.VICTORY:
    case CampaignStepperPhase.DEFEAT:
      break;
  }
}
