import * as Phaser from "phaser";
import { assetManifest } from "../assets/manifest";
import { label, setButtonHitArea } from "./theme";

export class ActionButton extends Phaser.GameObjects.Container {
  private readonly normal: Phaser.GameObjects.Image;
  private readonly hover: Phaser.GameObjects.Image;
  private readonly caption: Phaser.GameObjects.BitmapText;

  constructor(scene: Phaser.Scene, x: number, y: number, text: string, onClick: () => void, width = 180, height = 54) {
    super(scene, x, y);
    this.normal = scene.add.image(0, 0, assetManifest.buttons.normal.key).setOrigin(0.5).setDisplaySize(width, height);
    this.hover = scene.add.image(0, 0, assetManifest.buttons.hover.key).setOrigin(0.5).setDisplaySize(width, height).setVisible(false);
    this.caption = label(scene, -width / 2 + 18, -10, text, 18);
    this.add([this.normal, this.hover, this.caption]);
    setButtonHitArea(this.normal, onClick);
    this.normal.on(Phaser.Input.Events.POINTER_OVER, () => this.hover.setVisible(true));
    this.normal.on(Phaser.Input.Events.POINTER_OUT, () => this.hover.setVisible(false));
    scene.add.existing(this);
  }

  setText(text: string): this {
    this.caption.setText(text);
    return this;
  }
}
