import * as Phaser from "phaser";
import { CampaignStepper, CampaignStepperPhase } from "../sim/campaignStepper";
import type { Card, GameData } from "../sim/types";
import { saveCampaign } from "../systems/saveLoad";
import { ActionButton } from "../ui/ActionButton";
import { label, panel } from "../ui/theme";

export class RewardScene extends Phaser.Scene {
  constructor() {
    super("RewardScene");
  }

  create(): void {
    const campaign = this.campaign();
    panel(this, 0, 0, 1280, 720);
    if (campaign.phase === CampaignStepperPhase.VICTORY || campaign.phase === CampaignStepperPhase.DEFEAT) {
      this.scene.start("GameOverScene", { victory: campaign.phase === CampaignStepperPhase.VICTORY });
      return;
    }
    label(this, 54, 38, "Rewards", 38);
    if (campaign.phase === CampaignStepperPhase.POST_CONQUEST_UPGRADES) this.drawUpgrades(campaign);
    else if (campaign.phase === CampaignStepperPhase.POST_CONQUEST_DRAFT) this.drawDraft(campaign);
    else if (campaign.phase === CampaignStepperPhase.WORLD_PHASE) this.drawWorld(campaign);
    else this.backToCampaign(campaign);
  }

  private campaign(): CampaignStepper {
    return this.registry.get("campaign") as CampaignStepper;
  }

  private gameData(): GameData {
    return this.registry.get("gameData") as GameData;
  }

  private drawUpgrades(campaign: CampaignStepper): void {
    const options = Object.values(this.gameData().cards_by_id).filter((card) => !card.tags.includes("hazard")).slice(0, 3);
    options.forEach((card, index) => {
      const x = 104 + index * 360;
      panel(this, x, 160, 290, 210);
      label(this, x + 24, 190, card.name, 18);
      const branch = this.firstBranch(card);
      label(this, x + 24, 230, branch ? `Upgrade ${branch}` : "No branch", 14);
      new ActionButton(this, x + 145, 320, "Choose", () => {
        if (branch) campaign.selectUpgrade(card.id, branch);
        else campaign.phase = CampaignStepperPhase.POST_CONQUEST_DRAFT;
        saveCampaign(campaign);
        this.scene.restart();
      }, 150, 46);
    });
  }

  private drawDraft(campaign: CampaignStepper): void {
    const draft = campaign.toJSON().draftCandidates;
    draft.forEach((character, index) => {
      const x = 104 + index * 360;
      panel(this, x, 160, 290, 210);
      label(this, x + 24, 190, character.name.slice(0, 24), 15);
      label(this, x + 24, 228, Object.entries(character.base_stats).map(([key, value]) => `${key} ${Math.floor(value / 1000)}`).slice(0, 3).join(" "), 12);
      new ActionButton(this, x + 145, 320, "Draft", () => {
        campaign.selectDraftCharacter(index);
        saveCampaign(campaign);
        this.scene.restart();
      }, 150, 46);
    });
  }

  private drawWorld(campaign: CampaignStepper): void {
    const ids = campaign.toJSON().worldCandidates;
    if (ids.length === 0) {
      this.backToCampaign(campaign);
      return;
    }
    const card = this.gameData().world_deck.find((item) => item.id === ids[0]);
    panel(this, 360, 154, 560, 310);
    label(this, 406, 198, card?.name ?? "World Card", 26);
    label(this, 406, 254, (card?.description ?? "").slice(0, 54), 14);
    new ActionButton(this, 520, 404, "Accept", () => {
      campaign.evaluateWorldCard(true);
      saveCampaign(campaign);
      this.scene.restart();
    });
    new ActionButton(this, 760, 404, "Skip", () => {
      campaign.evaluateWorldCard(false);
      saveCampaign(campaign);
      this.scene.restart();
    });
  }

  private firstBranch(card: Card): string | null {
    return Object.keys(this.gameData().upgrade_trees[card.id] ?? card.upgrade_paths)[0] ?? null;
  }

  private backToCampaign(campaign: CampaignStepper): void {
    saveCampaign(campaign);
    this.scene.start("CampaignScene");
  }
}
