import { describe, expect, it } from "vitest";
import { CampaignStepper, CampaignStepperPhase } from "../campaignStepper";
import { loadGameDataFromPath } from "../loader.node";

describe("CampaignStepper", () => {
  it("drives seed 42 from region select into encounter flow and restores from JSON", async () => {
    const data = await loadGameDataFromPath("../data");
    const stepper = new CampaignStepper(42, data);
    expect(stepper.phase).toBe(CampaignStepperPhase.REGION_SELECT);
    expect(stepper.state.region_states).toHaveLength(6);
    expect(stepper.state.roster).toHaveLength(2);

    stepper.selectRegion(0);
    expect(stepper.phase).toBe(CampaignStepperPhase.PARTY_SELECT);
    stepper.selectParty(stepper.state.roster.slice(0, 2).map((character) => character.id));
    expect(stepper.phase).toBe(CampaignStepperPhase.ENCOUNTER_ACTIVE);

    const combat = stepper.getCombatStepper();
    if (combat) {
      expect(combat.snapshot().entities.some((entity) => !entity.is_player)).toBe(true);
      stepper.completeEncounter({ playerWon: true, survivors: stepper.selectedPartyIds });
    } else {
      stepper.completeEncounter({ playerWon: true, survivors: stepper.selectedPartyIds });
    }

    const restored = CampaignStepper.fromJSON(stepper.toJSON(), data);
    expect(restored.toJSON()).toEqual(stepper.toJSON());
  });
});
