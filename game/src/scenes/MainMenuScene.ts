import * as Phaser from "phaser";
import { CampaignStepper } from "../sim/campaignStepper";
import type { GameData } from "../sim/types";
import { loadCampaign } from "../systems/saveLoad";
import { ActionButton } from "../ui/ActionButton";
import { SeedInput } from "../ui/SeedInput";
import { label, panel } from "../ui/theme";

export class MainMenuScene extends Phaser.Scene {
  private seedText?: Phaser.GameObjects.BitmapText;
  private seedInput?: SeedInput;

  constructor() {
    super("MainMenuScene");
  }

  create(): void {
    panel(this, 0, 0, 1280, 720);
    label(this, 452, 118, "Holdfast", 64);
    this.seedText = label(this, 514, 214, "Seed: 42", 20);
    new ActionButton(this, 640, 304, "New Game", () => this.openSeed());
    new ActionButton(this, 640, 374, "Random Seed", () => this.startNew(Phaser.Math.Between(1, 999999)));
    new ActionButton(this, 640, 444, "Continue", () => this.continueGame());
  }

  private gameData(): GameData {
    return this.registry.get("gameData") as GameData;
  }

  private openSeed(): void {
    this.seedInput?.destroy();
    this.seedInput = new SeedInput(this, 640, 548, (seed) => this.startNew(seed));
  }

  private startNew(seed: number): void {
    this.seedText?.setText(`Seed: ${seed}`);
    this.registry.set("campaign", new CampaignStepper(seed, this.gameData()));
    this.scene.start("CampaignScene");
  }

  private continueGame(): void {
    const stepper = loadCampaign(this.gameData());
    if (!stepper) return;
    this.registry.set("campaign", stepper);
    this.scene.start("CampaignScene");
  }
}
