import * as Phaser from "phaser";
import { CampaignStepper, CampaignStepperPhase } from "../sim/campaignStepper";
import { STAT_SCALE, Stat } from "../sim/types";
import { saveCampaign } from "../systems/saveLoad";
import { ActionButton } from "../ui/ActionButton";
import { DebugPanel } from "../ui/DebugPanel";
import { label, panel } from "../ui/theme";

export class CampaignScene extends Phaser.Scene {
  constructor() {
    super("CampaignScene");
  }

  create(): void {
    const campaign = this.campaign();
    if (campaign.phase === CampaignStepperPhase.VICTORY || campaign.phase === CampaignStepperPhase.DEFEAT) {
      this.scene.start("GameOverScene", { victory: campaign.phase === CampaignStepperPhase.VICTORY });
      return;
    }
    panel(this, 0, 0, 1280, 720);
    label(this, 52, 34, `Campaign ${campaign.seed}`, 34);
    label(this, 52, 82, `Resources ${campaign.state.resources}  Skip ${campaign.state.skip_tokens}`, 18);
    this.drawRegions(campaign);
    this.drawRoster(campaign);
    new DebugPanel(this, () => campaign, () => null);
    saveCampaign(campaign);
  }

  private campaign(): CampaignStepper {
    return this.registry.get("campaign") as CampaignStepper;
  }

  private drawRegions(campaign: CampaignStepper): void {
    campaign.state.region_states.forEach((region, index) => {
      const x = 112 + (index % 3) * 260;
      const y = 174 + Math.floor(index / 3) * 190;
      const node = panel(this, x, y, 220, 128);
      node.setTint(region.conquered ? 0x758075 : 0xffffff);
      if (!region.conquered) {
        node.setInteractive({ useHandCursor: true });
        node.on(Phaser.Input.Events.POINTER_DOWN, () => {
          campaign.selectRegion(index);
          this.scene.start("PartySelectScene");
        });
      }
      label(this, x + 16, y + 18, region.region.name.slice(0, 20), 15);
      label(this, x + 16, y + 48, `Difficulty ${region.assigned_difficulty}`, 13);
      label(this, x + 16, y + 72, `Research ${region.research_level}`, 13);
      label(this, x + 16, y + 96, region.conquered ? "Conquered" : "Open", 13, region.conquered ? 0xb6ffbd : 0xffdd99);
    });
  }

  private drawRoster(campaign: CampaignStepper): void {
    panel(this, 910, 98, 310, 510);
    label(this, 934, 122, "Roster", 26);
    campaign.state.roster.forEach((character, index) => {
      const y = 172 + index * 76;
      label(this, 934, y, character.name.slice(0, 23), 14);
      label(this, 934, y + 24, `HP ${Math.floor(character.base_stats[Stat.HP] / STAT_SCALE)} P ${Math.floor(character.base_stats[Stat.Power] / STAT_SCALE)} S ${Math.floor(character.base_stats[Stat.Speed] / STAT_SCALE)}`, 12);
    });
    new ActionButton(this, 1064, 650, "Research", () => {
      campaign.phase = CampaignStepperPhase.RESEARCH_PHASE;
      campaign.selectResearch(0);
      campaign.endResearch();
      this.scene.restart();
    }, 170, 48);
  }
}
