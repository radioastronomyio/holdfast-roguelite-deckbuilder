import * as Phaser from "phaser";
import { ActionButton } from "./ActionButton";
import { label, panel } from "./theme";

export class SeedInput extends Phaser.GameObjects.Container {
  private value = "";
  private readonly valueText: Phaser.GameObjects.BitmapText;

  constructor(scene: Phaser.Scene, x: number, y: number, onSubmit: (seed: number) => void) {
    super(scene, x, y);
    const bg = panel(scene, -170, -70, 340, 150);
    this.valueText = label(scene, -132, -20, "42", 28);
    this.value = "42";
    this.add([bg, label(scene, -132, -50, "Seed", 18), this.valueText, new ActionButton(scene, 74, 42, "Start", () => onSubmit(Number(this.value || "1")), 140, 44)]);
    scene.input.keyboard?.on(Phaser.Input.Keyboard.Events.ANY_KEY_DOWN, (event: KeyboardEvent) => {
      if (/^[0-9]$/.test(event.key) && this.value.length < 10) this.value += event.key;
      if (event.key === "Backspace") this.value = this.value.slice(0, -1);
      if (event.key === "Enter") onSubmit(Number(this.value || "1"));
      this.valueText.setText(this.value || "0");
    });
    scene.add.existing(this);
    this.setDepth(900);
  }
}
