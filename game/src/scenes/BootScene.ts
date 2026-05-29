import * as Phaser from "phaser";
import { assetManifest } from "../assets/manifest";

export class BootScene extends Phaser.Scene {
  constructor() {
    super("BootScene");
  }

  preload(): void {
    this.load.bitmapFont(assetManifest.font.key, assetManifest.font.image, assetManifest.font.fnt);
    this.load.image(assetManifest.cursor.key, assetManifest.cursor.path);
    this.load.image(assetManifest.panels.primary.key, assetManifest.panels.primary.path);
    this.load.image(assetManifest.bars.hp.key, assetManifest.bars.hp.path);
  }

  create(): void {
    this.input.setDefaultCursor(`url(${assetManifest.cursor.path}), pointer`);
    this.scene.start("PreloadScene");
  }
}
