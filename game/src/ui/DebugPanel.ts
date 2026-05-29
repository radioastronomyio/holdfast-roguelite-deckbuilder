import * as Phaser from "phaser";
import type { CampaignStepper } from "../sim/campaignStepper";
import { CombatStepper } from "../sim/combatStepper";
import { label, panel } from "./theme";

export class DebugPanel extends Phaser.GameObjects.Container {
  private readonly text: Phaser.GameObjects.BitmapText;
  private visibleState = false;

  constructor(scene: Phaser.Scene, private readonly getCampaign: () => CampaignStepper | null, private readonly getCombat: () => CombatStepper | null) {
    super(scene, 944, 16);
    this.add(panel(scene, 0, 0, 320, 300).setAlpha(0.78));
    this.text = label(scene, 14, 14, "", 12);
    this.add(this.text);
    scene.add.existing(this);
    this.setDepth(1200);
    this.setVisible(false);
    scene.input.keyboard?.on("keydown-BACKTICK", () => {
      this.visibleState = !this.visibleState;
      this.setVisible(this.visibleState);
      this.refresh();
    });
  }

  refresh(): void {
    const campaign = this.getCampaign();
    const combat = this.getCombat();
    const combatState = combat?.snapshot();
    this.text.setText([
      `seed: ${campaign?.seed ?? "-"}`,
      `phase: ${campaign?.phase ?? "-"}`,
      `active: ${combatState?.activeEntityId ?? "-"}`,
      `rng calls: ${campaign?.toJSON().rng.callCount ?? "-"}`,
      `entities: ${combatState?.entities.length ?? 0}`,
      `mods: ${combatState?.entities.flatMap((entity) => entity.active_modifiers).length ?? 0}`,
      `log: ${(campaign?.state.campaign_log ?? []).slice(-8).join(" | ")}`
    ].join("\n"));
  }
}
