import * as Phaser from "phaser";
import { assetManifest } from "../assets/manifest";

export const FONT_KEY = assetManifest.font.key;
export const WIDTH = 1280;
export const HEIGHT = 720;

export function label(scene: Phaser.Scene, x: number, y: number, text: string, size = 18, tint = 0xf7ead0): Phaser.GameObjects.BitmapText {
  return scene.add.bitmapText(x, y, FONT_KEY, text, size).setTint(tint);
}

export function panel(scene: Phaser.Scene, x: number, y: number, width: number, height: number, texture: string = assetManifest.panels.primary.key): Phaser.GameObjects.Image {
  const image = scene.add.image(x, y, texture).setOrigin(0, 0);
  image.setDisplaySize(width, height);
  return image;
}

export function setButtonHitArea(image: Phaser.GameObjects.Image, onClick: () => void): void {
  image.setInteractive({ useHandCursor: true });
  image.on(Phaser.Input.Events.POINTER_DOWN, onClick);
}
