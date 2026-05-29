import * as Phaser from "phaser";
import { BootScene } from "./scenes/BootScene";
import { PreloadScene } from "./scenes/PreloadScene";
import { MainMenuScene } from "./scenes/MainMenuScene";
import { CampaignScene } from "./scenes/CampaignScene";
import { PartySelectScene } from "./scenes/PartySelectScene";
import { CombatScene } from "./scenes/CombatScene";
import { RewardScene } from "./scenes/RewardScene";
import { GameOverScene } from "./scenes/GameOverScene";

export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  pixelArt: true,
  width: 1280,
  height: 720,
  parent: "game-root",
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH,
    parent: "game-root",
    width: 1280,
    height: 720
  },
  scene: [BootScene, PreloadScene, MainMenuScene, CampaignScene, PartySelectScene, CombatScene, RewardScene, GameOverScene]
};
