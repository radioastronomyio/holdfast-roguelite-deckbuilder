import * as Phaser from "phaser";
import { assetManifest } from "../assets/manifest";
import { label, panel } from "./theme";

export class BarWidget extends Phaser.GameObjects.Container {
  private readonly fill: Phaser.GameObjects.Image;
  private readonly text: Phaser.GameObjects.BitmapText;
  private readonly barWidth: number;

  constructor(scene: Phaser.Scene, x: number, y: number, width: number, title: string, texture = assetManifest.bars.hp.key) {
    super(scene, x, y);
    const bg = panel(scene, -4, -4, width + 8, 24, assetManifest.panels.slot.key).setScrollFactor(1);
    this.fill = scene.add.image(0, 0, texture).setOrigin(0, 0).setDisplaySize(width, 16);
    this.text = label(scene, 6, -1, title, 12, 0x1a120f);
    this.barWidth = width;
    this.add([bg, this.fill, this.text]);
    scene.add.existing(this);
  }

  setValue(current: number, max: number): void {
    const ratio = max <= 0 ? 0 : Phaser.Math.Clamp(current / max, 0, 1);
    this.fill.setDisplaySize(Math.max(1, Math.floor(this.barWidth * ratio)), 16);
    this.text.setText(`${current}/${max}`);
  }
}
