import * as Phaser from "phaser";
import { CampaignStepper } from "../sim/campaignStepper";
import { clearSave, exportBugReport } from "../systems/saveLoad";
import { ActionButton } from "../ui/ActionButton";
import { label, panel } from "../ui/theme";

export class GameOverScene extends Phaser.Scene {
  private victory = false;

  constructor() {
    super("GameOverScene");
  }

  init(data: { victory?: boolean }): void {
    this.victory = Boolean(data.victory);
  }

  create(): void {
    const campaign = this.registry.get("campaign") as CampaignStepper | undefined;
    panel(this, 0, 0, 1280, 720);
    if (this.victory) this.add.image(640, 138, "victory-star").setDisplaySize(96, 96);
    label(this, 492, 238, this.victory ? "Victory" : "Defeat", 54);
    label(this, 448, 320, `Seed ${campaign?.seed ?? "-"}  Regions ${campaign?.state.region_states.filter((region) => region.conquered).length ?? 0}/6`, 20);
    new ActionButton(this, 520, 444, "New Game", () => {
      clearSave();
      this.scene.start("MainMenuScene");
    });
    if (campaign) new ActionButton(this, 760, 444, "Export Run", () => exportBugReport(campaign));
  }
}
