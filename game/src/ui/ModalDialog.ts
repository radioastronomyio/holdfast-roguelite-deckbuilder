import * as Phaser from "phaser";
import { ActionButton } from "./ActionButton";
import { label, panel } from "./theme";

export class ModalDialog extends Phaser.GameObjects.Container {
  constructor(scene: Phaser.Scene, title: string, body: string, actions: Array<{ text: string; run: () => void }>) {
    super(scene, 640, 360);
    const bg = panel(scene, -240, -150, 480, 300);
    const heading = label(scene, -205, -112, title, 26);
    const copy = label(scene, -205, -62, body, 15);
    this.add([bg, heading, copy]);
    actions.forEach((action, index) => this.add(new ActionButton(scene, -100 + index * 200, 96, action.text, action.run, 160, 48)));
    scene.add.existing(this);
    this.setDepth(1000);
  }
}
