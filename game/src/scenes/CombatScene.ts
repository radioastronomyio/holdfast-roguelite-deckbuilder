import * as Phaser from "phaser";
import { CampaignStepper, CampaignStepperPhase } from "../sim/campaignStepper";
import { CombatStepper, CombatStepperStatus, type StepEvent } from "../sim/combatStepper";
import type { Card, CombatEntity } from "../sim/types";
import { saveCampaign } from "../systems/saveLoad";
import { CardSprite } from "../ui/CardSprite";
import { DebugPanel } from "../ui/DebugPanel";
import { EntityPanel } from "../ui/EntityPanel";
import { label, panel } from "../ui/theme";

export class CombatScene extends Phaser.Scene {
  private combat!: CombatStepper;
  private logLines: string[] = [];
  private selectedCardIndex: number | null = null;
  private hand: CardSprite[] = [];

  constructor() {
    super("CombatScene");
  }

  create(): void {
    const stepper = this.campaign().getCombatStepper();
    if (!stepper) {
      this.campaign().completeEncounter({ playerWon: true, survivors: this.campaign().selectedPartyIds });
      this.scene.start("RewardScene");
      return;
    }
    this.combat = stepper;
    panel(this, 0, 0, 1280, 720);
    this.input.keyboard?.on("keydown", (event: KeyboardEvent) => {
      const index = Number(event.key) - 1;
      if (index >= 0 && index < 5) this.playCard(index);
      if (event.key === "e" || event.key === "E") this.endTurn();
    });
    new DebugPanel(this, () => this.campaign(), () => this.combat);
    this.settleTurn();
  }

  private campaign(): CampaignStepper {
    return this.registry.get("campaign") as CampaignStepper;
  }

  private settleTurn(): void {
    let result = this.combat.snapshot().status === CombatStepperStatus.INIT ? this.combat.advance() : { status: this.combat.snapshot().status, events: [], activeEntityId: this.combat.snapshot().activeEntityId };
    while (result.status === CombatStepperStatus.ENEMY_TURN || result.status === CombatStepperStatus.TICKING) {
      this.consume(result.events);
      result = this.combat.advance();
    }
    this.consume(result.events);
    this.render();
    if (result.status === CombatStepperStatus.COMBAT_WON || result.status === CombatStepperStatus.COMBAT_LOST || result.status === CombatStepperStatus.COMBAT_TIMEOUT) this.finishCombat(result.events);
  }

  private render(): void {
    this.children.removeAll(true);
    panel(this, 0, 0, 1280, 720);
    label(this, 34, 22, "Combat", 30);
    label(this, 538, 22, `Turn ${this.combat.snapshot().turnNumber}  Active ${this.combat.snapshot().activeEntityId ?? "-"}`, 18);
    this.drawEntities();
    this.drawHand();
    this.drawLog();
    new DebugPanel(this, () => this.campaign(), () => this.combat);
  }

  private drawEntities(): void {
    const entities = this.combat.snapshot().entities;
    entities.filter((entity) => entity.is_player).forEach((entity, index) => {
      new EntityPanel(this, 70, 128 + index * 126, entity);
    });
    entities.filter((entity) => !entity.is_player).forEach((entity, index) => {
      new EntityPanel(this, 840, 128 + index * 126, entity, () => this.target(entity.id));
    });
  }

  private drawHand(): void {
    this.hand = [];
    const actor = this.activeActor();
    if (!actor?.is_player || this.combat.snapshot().status !== CombatStepperStatus.PLAYER_SELECT_CARD && this.combat.snapshot().status !== CombatStepperStatus.PLAYER_SELECT_TARGET) return;
    actor.hand.forEach((cardId, index) => {
      const card = this.card(cardId);
      if (!card) return;
      const sprite = new CardSprite(this, 316 + index * 150, 594, card, index + 1, () => this.playCard(index));
      sprite.setSelected(index === this.selectedCardIndex);
      this.hand.push(sprite);
    });
    label(this, 956, 638, "E: End Turn", 16);
  }

  private drawLog(): void {
    panel(this, 1002, 472, 246, 170);
    this.logLines.slice(-8).forEach((line, index) => label(this, 1022, 492 + index * 18, line.slice(0, 28), 11));
  }

  private playCard(index: number): void {
    const result = this.combat.selectCard(index);
    this.consume(result.events);
    if (result.status === CombatStepperStatus.PLAYER_SELECT_TARGET) {
      this.selectedCardIndex = index;
      this.logLines.push("Choose target");
      this.render();
      return;
    }
    this.selectedCardIndex = null;
    this.render();
    if (result.status === CombatStepperStatus.COMBAT_WON || result.status === CombatStepperStatus.COMBAT_LOST) this.finishCombat(result.events);
  }

  private target(entityId: string): void {
    if (this.selectedCardIndex === null) return;
    const result = this.combat.selectTarget(entityId);
    this.selectedCardIndex = null;
    this.consume(result.events);
    this.render();
    if (result.status === CombatStepperStatus.COMBAT_WON || result.status === CombatStepperStatus.COMBAT_LOST) this.finishCombat(result.events);
  }

  private endTurn(): void {
    const result = this.combat.endTurn();
    this.consume(result.events);
    this.selectedCardIndex = null;
    this.render();
    this.time.delayedCall(300, () => this.settleTurn());
  }

  private consume(events: StepEvent[]): void {
    for (const event of events) {
      if (event.type === "TURN_STARTED") this.logLines.push(`${event.entityId} turn`);
      if (event.type === "HAND_DRAWN") this.logLines.push(`${event.cardIds.length} cards drawn`);
      if (event.type === "CARD_PLAYED") this.logLines.push(`${event.casterId} plays ${event.cardId}`);
      if (event.type === "TARGET_DAMAGED") {
        this.logLines.push(`${event.entityId} -${event.amount}`);
        this.floatText(event.entityId, `-${event.amount}`, 0xff6b5f);
      }
      if (event.type === "TARGET_HEALED") this.logLines.push(`${event.entityId} +${event.amount}`);
      if (event.type === "ENTITY_DIED") this.logLines.push(`${event.entityId} falls`);
      if (event.type === "COMBAT_ENDED") this.logLines.push(event.playerWon ? "Victory" : "Defeat");
    }
  }

  private floatText(entityId: string, text: string, tint: number): void {
    const entity = this.combat.snapshot().entities.find((item) => item.id === entityId);
    if (!entity) return;
    const isPlayer = entity.is_player;
    const sameSide = this.combat.snapshot().entities.filter((item) => item.is_player === isPlayer);
    const index = sameSide.findIndex((item) => item.id === entityId);
    const x = isPlayer ? 226 : 1000;
    const y = 130 + index * 126;
    const float = label(this, x, y, text, 18, tint);
    this.tweens.add({ targets: float, y: y - 32, alpha: 0, duration: 500, onComplete: () => float.destroy() });
  }

  private finishCombat(events: StepEvent[]): void {
    const ended = events.find((event): event is Extract<StepEvent, { type: "COMBAT_ENDED" }> => event.type === "COMBAT_ENDED");
    const campaign = this.campaign();
    const won = ended?.playerWon ?? false;
    campaign.completeEncounter({ playerWon: won, survivors: ended?.survivors ?? [] });
    saveCampaign(campaign);
    this.time.delayedCall(600, () => {
      if (campaign.phase === CampaignStepperPhase.DEFEAT) this.scene.start("GameOverScene", { victory: false });
      else this.scene.start("RewardScene");
    });
  }

  private activeActor(): CombatEntity | null {
    const state = this.combat.snapshot();
    return state.entities.find((entity) => entity.id === state.activeEntityId) ?? null;
  }

  private card(cardId: string): Card | null {
    const data = this.registry.get("gameData") as { cards_by_id: Record<string, Card> };
    return data.cards_by_id[cardId] ?? null;
  }
}
