import * as Phaser from "phaser";
import { assetManifest } from "../assets/manifest";
import { STAT_SCALE, Stat, type CombatEntity } from "../sim/types";
import { BarWidget } from "./BarWidget";
import { label, panel } from "./theme";

export class EntityPanel extends Phaser.GameObjects.Container {
  readonly entityId: string;
  private readonly hp: BarWidget;
  private readonly status: Phaser.GameObjects.BitmapText;

  constructor(scene: Phaser.Scene, x: number, y: number, entity: CombatEntity, onClick?: () => void) {
    super(scene, x, y);
    this.entityId = entity.id;
    const bg = panel(scene, 0, 0, 210, 104, assetManifest.panels.secondary.key);
    if (onClick) {
      bg.setInteractive({ useHandCursor: true });
      bg.on(Phaser.Input.Events.POINTER_DOWN, onClick);
    }
    const name = label(scene, 14, 12, entity.name.slice(0, 18), 14);
    this.hp = new BarWidget(scene, 14, 42, 176, "HP");
    this.status = label(scene, 14, 72, "", 11, 0xb9d7ff);
    this.add([bg, name, this.hp, this.status]);
    this.refresh(entity);
    scene.add.existing(this);
  }

  refresh(entity: CombatEntity): void {
    const hp = Math.max(0, Math.floor(entity.base_stats[Stat.HP] / STAT_SCALE));
    this.hp.setValue(hp, Math.max(hp, 1));
    this.status.setText(`${entity.current_energy}E CT ${Math.floor(entity.ct / STAT_SCALE)} Mods ${entity.active_modifiers.length}`);
    this.setAlpha(entity.is_alive ? 1 : 0.45);
  }
}
