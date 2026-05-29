import * as Phaser from "phaser";
import { assetManifest } from "../assets/manifest";
import type { Card } from "../sim/types";
import { label } from "./theme";

export class CardSprite extends Phaser.GameObjects.Container {
  readonly card: Card;
  private readonly frame: Phaser.GameObjects.Image;

  constructor(scene: Phaser.Scene, x: number, y: number, card: Card, hotkey: number, onClick: () => void) {
    super(scene, x, y);
    this.card = card;
    this.frame = scene.add.image(0, 0, assetManifest.cards.face.key).setOrigin(0.5).setDisplaySize(136, 190);
    const name = label(scene, -56, -70, card.name.slice(0, 16), 14, 0x2a1810);
    const cost = label(scene, -56, 52, `${hotkey}: ${card.energy_cost}E`, 13, 0x2a1810);
    const tags = label(scene, -56, 72, card.tags.slice(0, 2).join(" ").slice(0, 18), 10, 0x4d3122);
    this.add([this.frame, name, cost, tags]);
    this.frame.setInteractive({ useHandCursor: true });
    this.frame.on(Phaser.Input.Events.POINTER_DOWN, onClick);
    this.frame.on(Phaser.Input.Events.POINTER_OVER, () => this.setY(y - 12));
    this.frame.on(Phaser.Input.Events.POINTER_OUT, () => this.setY(y));
    scene.add.existing(this);
  }

  setSelected(selected: boolean): void {
    this.frame.setTint(selected ? 0xffe07a : 0xffffff);
  }
}
