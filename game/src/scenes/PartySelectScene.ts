import * as Phaser from "phaser";
import { CampaignStepper } from "../sim/campaignStepper";
import { STAT_SCALE, Stat } from "../sim/types";
import { ActionButton } from "../ui/ActionButton";
import { label, panel } from "../ui/theme";

export class PartySelectScene extends Phaser.Scene {
  private selected = new Set<string>();

  constructor() {
    super("PartySelectScene");
  }

  create(): void {
    const campaign = this.campaign();
    panel(this, 0, 0, 1280, 720);
    label(this, 58, 36, "Choose Party", 38);
    const max = Math.min(3, campaign.state.roster.length);
    if (this.selected.size === 0) {
      for (const character of campaign.state.roster.slice(0, max)) this.selected.add(character.id);
    }
    campaign.state.roster.forEach((character, index) => {
      const x = 78 + (index % 3) * 380;
      const y = 126 + Math.floor(index / 3) * 160;
      const card = panel(this, x, y, 330, 126);
      card.setInteractive({ useHandCursor: true });
      card.on(Phaser.Input.Events.POINTER_DOWN, () => {
        if (this.selected.has(character.id)) this.selected.delete(character.id);
        else if (this.selected.size < max) this.selected.add(character.id);
        this.scene.restart({ selected: [...this.selected] });
      });
      label(this, x + 18, y + 18, character.name.slice(0, 26), 15, this.selected.has(character.id) ? 0xffe07a : 0xf7ead0);
      label(this, x + 18, y + 48, `HP ${Math.floor(character.base_stats[Stat.HP] / STAT_SCALE)} Power ${Math.floor(character.base_stats[Stat.Power] / STAT_SCALE)}`, 13);
      label(this, x + 18, y + 72, `Speed ${Math.floor(character.base_stats[Stat.Speed] / STAT_SCALE)} Defense ${Math.floor(character.base_stats[Stat.Defense] / STAT_SCALE)} Energy ${Math.floor(character.base_stats[Stat.Energy] / STAT_SCALE)}`, 13);
      label(this, x + 18, y + 96, character.innate_passive.tags.join(" ").slice(0, 28), 11, 0xb9d7ff);
    });
    new ActionButton(this, 1082, 646, "Deploy", () => {
      campaign.selectParty([...this.selected]);
      this.scene.start("CombatScene");
    });
  }

  init(data: { selected?: string[] }): void {
    this.selected = new Set(data.selected ?? []);
  }

  private campaign(): CampaignStepper {
    return this.registry.get("campaign") as CampaignStepper;
  }
}
