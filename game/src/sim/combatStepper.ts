import { applyStacking } from "./stats";
import { SeededRng, type RngState } from "./rng";
import { discardCard, discardHand, drawCards, getCurrentStat, initializeDeck, processTurnStart, tickUntilNextTurn } from "./turnOrder";
import { COMBAT_TURN_CAP, HAND_SIZE, Operation, STAT_SCALE, Stat, Target, type Card, type CombatEntity, type Modifier } from "./types";

export enum CombatStepperStatus {
  INIT = "INIT",
  TICKING = "TICKING",
  PLAYER_SELECT_CARD = "PLAYER_SELECT_CARD",
  PLAYER_SELECT_TARGET = "PLAYER_SELECT_TARGET",
  PLAYER_CONFIRM_END_TURN = "PLAYER_CONFIRM_END_TURN",
  RESOLVING_CARD = "RESOLVING_CARD",
  ENEMY_TURN = "ENEMY_TURN",
  COMBAT_WON = "COMBAT_WON",
  COMBAT_LOST = "COMBAT_LOST",
  COMBAT_TIMEOUT = "COMBAT_TIMEOUT"
}

export type StepEvent =
  | { type: "TURN_STARTED"; entityId: string; turnNumber: number }
  | { type: "HAND_DRAWN"; entityId: string; cardIds: string[] }
  | { type: "CARD_PLAYED"; casterId: string; cardId: string; targetIds: string[]; energyCost: number }
  | { type: "TARGET_DAMAGED"; entityId: string; amount: number; newHp: number; isDead: boolean }
  | { type: "TARGET_HEALED"; entityId: string; amount: number; newHp: number }
  | { type: "MODIFIER_APPLIED"; entityId: string; modifier: Modifier }
  | { type: "MODIFIER_EXPIRED"; entityId: string; count: number }
  | { type: "CARD_DISCARDED"; entityId: string; cardId: string }
  | { type: "ENTITY_DIED"; entityId: string }
  | { type: "COMBAT_ENDED"; playerWon: boolean; survivors: string[] };

export interface StepResult {
  status: CombatStepperStatus;
  events: StepEvent[];
  activeEntityId: string | null;
  message?: string;
}

export interface CombatStepperOptions {
  seed?: number;
  rngState?: RngState;
  region_modifiers?: Modifier[];
  world_modifiers?: Modifier[];
}

export interface CombatStepperState {
  status: CombatStepperStatus;
  entities: CombatEntity[];
  turnNumber: number;
  activeEntityId: string | null;
  selectedCardIndex: number | null;
  rng: RngState;
}

function cloneEntity(entity: CombatEntity): CombatEntity {
  return {
    ...entity,
    base_stats: { ...entity.base_stats },
    active_modifiers: entity.active_modifiers.map((modifier) => ({ ...modifier, tags: [...modifier.tags] })),
    card_pool: [...entity.card_pool],
    draw_pile: [...entity.draw_pile],
    hand: [...entity.hand],
    discard_pile: [...entity.discard_pile]
  };
}

function display(value: number): number {
  return Math.floor(value / STAT_SCALE);
}

function rngState(rng: SeededRng): RngState {
  const state = rng.getState();
  return { ...state, mt: state.mt.map((value) => value >>> 0) };
}

function damageScore(card: Card): number {
  return card.effects
    .filter((effect) => effect.stat === Stat.HP && effect.operation === Operation.FLAT_SUB)
    .reduce((sum, effect) => sum + effect.value, 0);
}

function hasTarget(card: Card, target: Target): boolean {
  return card.effects.some((effect) => effect.target === target);
}

export class CombatStepper {
  private status: CombatStepperStatus;
  private entities: CombatEntity[];
  private readonly cardsById: Record<string, Card>;
  private readonly rng: SeededRng;
  private turnNumber;
  private activeEntityId: string | null;
  private selectedCardIndex: number | null;

  constructor(party: CombatEntity[], enemies: CombatEntity[], cardsById: Record<string, Card>, options: CombatStepperOptions = {}) {
    this.status = CombatStepperStatus.INIT;
    this.entities = [...party, ...enemies].map(cloneEntity);
    this.cardsById = cardsById;
    this.rng = new SeededRng(options.seed ?? 1);
    if (options.rngState) this.rng.setState(options.rngState);
    this.turnNumber = 0;
    this.activeEntityId = null;
    this.selectedCardIndex = null;
    this.applyOpeningModifiers([...(options.region_modifiers ?? []), ...(options.world_modifiers ?? [])]);
    for (const entity of this.entities) {
      entity.current_energy = getCurrentStat(entity, Stat.Energy);
      if (entity.draw_pile.length === 0 && entity.hand.length === 0 && entity.discard_pile.length === 0) {
        initializeDeck(entity, cardsById, this.rng);
      }
    }
  }

  snapshot(): { status: CombatStepperStatus; entities: CombatEntity[]; turnNumber: number; activeEntityId: string | null } {
    return {
      status: this.status,
      entities: this.entities.map(cloneEntity),
      turnNumber: this.turnNumber,
      activeEntityId: this.activeEntityId
    };
  }

  advance(): StepResult {
    const ended = this.checkEnd();
    if (ended) return ended;
    if (this.turnNumber >= COMBAT_TURN_CAP) {
      this.status = CombatStepperStatus.COMBAT_TIMEOUT;
      return this.result([]);
    }

    this.status = CombatStepperStatus.TICKING;
    const actor = tickUntilNextTurn(this.entities);
    this.activeEntityId = actor.id;
    this.turnNumber += 1;
    const events = this.turnStartEvents(actor);
    if (!actor.is_alive) return this.advance();

    discardHand(actor);
    const drawn = drawCards(actor, HAND_SIZE, this.rng);
    events.push({ type: "HAND_DRAWN", entityId: actor.id, cardIds: drawn });
    if (actor.is_player) {
      this.status = CombatStepperStatus.PLAYER_SELECT_CARD;
      return this.result(events);
    }

    this.status = CombatStepperStatus.ENEMY_TURN;
    while (actor.is_alive && this.opponents(actor).some((entity) => entity.is_alive)) {
      const play = this.pickEnemyPlay(actor);
      if (!play) break;
      events.push(...this.resolveCard(actor, play.card, play.targets));
    }
    const end = this.checkEnd();
    if (end) return { ...end, events: [...events, ...end.events] };
    return this.result(events);
  }

  selectCard(cardIndex: number): StepResult {
    const actor = this.activeActor();
    if (!actor || !actor.is_player || this.status !== CombatStepperStatus.PLAYER_SELECT_CARD) {
      return this.result([], "No player is selecting a card.");
    }
    const cardId = actor.hand[cardIndex];
    const card = cardId ? this.cardsById[cardId] : undefined;
    if (!card) return this.result([], "Invalid card.");
    if (actor.current_energy < card.energy_cost) return this.result([], `${card.name} is not affordable.`);
    this.selectedCardIndex = cardIndex;
    if (this.needsTarget(card)) {
      this.status = CombatStepperStatus.PLAYER_SELECT_TARGET;
      return this.result([]);
    }
    const events = this.resolveCard(actor, card, this.autoTargets(actor, card));
    this.selectedCardIndex = null;
    const end = this.checkEnd();
    if (end) return { ...end, events: [...events, ...end.events] };
    this.status = CombatStepperStatus.PLAYER_SELECT_CARD;
    return this.result(events);
  }

  selectTarget(targetId: string): StepResult {
    const actor = this.activeActor();
    if (!actor || this.status !== CombatStepperStatus.PLAYER_SELECT_TARGET || this.selectedCardIndex === null) {
      return this.result([], "No card is waiting for a target.");
    }
    const target = this.entities.find((entity) => entity.id === targetId && entity.is_alive);
    const card = this.cardsById[actor.hand[this.selectedCardIndex]];
    if (!target || !card) return this.result([], "Invalid target.");
    const events = this.resolveCard(actor, card, [target]);
    this.selectedCardIndex = null;
    const end = this.checkEnd();
    if (end) return { ...end, events: [...events, ...end.events] };
    this.status = CombatStepperStatus.PLAYER_SELECT_CARD;
    return this.result(events);
  }

  endTurn(): StepResult {
    const actor = this.activeActor();
    if (actor) discardHand(actor);
    this.selectedCardIndex = null;
    return this.advance();
  }

  toJSON(): CombatStepperState {
    return {
      status: this.status,
      entities: this.entities.map(cloneEntity),
      turnNumber: this.turnNumber,
      activeEntityId: this.activeEntityId,
      selectedCardIndex: this.selectedCardIndex,
      rng: rngState(this.rng)
    };
  }

  static fromJSON(state: CombatStepperState, cardsById: Record<string, Card>): CombatStepper {
    const party = state.entities.filter((entity) => entity.is_player);
    const enemies = state.entities.filter((entity) => !entity.is_player);
    const stepper = new CombatStepper(party, enemies, cardsById, { rngState: state.rng });
    stepper.entities = state.entities.map(cloneEntity);
    stepper.status = state.status;
    stepper.turnNumber = state.turnNumber;
    stepper.activeEntityId = state.activeEntityId;
    stepper.selectedCardIndex = state.selectedCardIndex;
    stepper.rng.setState(state.rng);
    return stepper;
  }

  private result(events: StepEvent[], message?: string): StepResult {
    return { status: this.status, events, activeEntityId: this.activeEntityId, message };
  }

  private activeActor(): CombatEntity | null {
    return this.entities.find((entity) => entity.id === this.activeEntityId) ?? null;
  }

  private allies(actor: CombatEntity): CombatEntity[] {
    return this.entities.filter((entity) => entity.is_alive && entity.is_player === actor.is_player);
  }

  private opponents(actor: CombatEntity): CombatEntity[] {
    return this.entities.filter((entity) => entity.is_alive && entity.is_player !== actor.is_player);
  }

  private needsTarget(card: Card): boolean {
    return card.effects.some((effect) => effect.target === Target.ENEMY_SINGLE || effect.target === Target.ALLY_SINGLE);
  }

  private autoTargets(actor: CombatEntity, card: Card): CombatEntity[] {
    if (hasTarget(card, Target.SELF)) return [actor];
    if (hasTarget(card, Target.ALLY_ALL)) return this.allies(actor);
    if (hasTarget(card, Target.ENEMY_ALL)) return this.opponents(actor);
    if (hasTarget(card, Target.GLOBAL)) return this.entities.filter((entity) => entity.is_alive);
    if (hasTarget(card, Target.ALLY_SINGLE)) return [this.allies(actor)[0]].filter(Boolean);
    return [this.opponents(actor)[0]].filter(Boolean);
  }

  private turnStartEvents(actor: CombatEntity): StepEvent[] {
    const before = actor.active_modifiers.length;
    processTurnStart(actor, this.turnNumber);
    const events: StepEvent[] = [{ type: "TURN_STARTED", entityId: actor.id, turnNumber: this.turnNumber }];
    const expired = Math.max(0, before - actor.active_modifiers.length);
    if (expired > 0) events.push({ type: "MODIFIER_EXPIRED", entityId: actor.id, count: expired });
    if (!actor.is_alive) events.push({ type: "ENTITY_DIED", entityId: actor.id });
    return events;
  }

  private pickEnemyPlay(actor: CombatEntity): { card: Card; targets: CombatEntity[] } | null {
    const living = this.opponents(actor);
    const affordable = actor.hand.map((id) => this.cardsById[id]).filter((card): card is Card => Boolean(card) && card.energy_cost <= actor.current_energy);
    if (living.length === 0 || affordable.length === 0) return null;
    const card = affordable.reduce((best, current) => damageScore(current) > damageScore(best) ? current : best);
    const targets = hasTarget(card, Target.ENEMY_ALL) ? living : [living.reduce((low, current) => getCurrentStat(current, Stat.HP) < getCurrentStat(low, Stat.HP) ? current : low)];
    return { card, targets };
  }

  private resolveCard(caster: CombatEntity, card: Card, selectedTargets: CombatEntity[]): StepEvent[] {
    if (caster.current_energy < card.energy_cost) return [];
    const events: StepEvent[] = [{ type: "CARD_PLAYED", casterId: caster.id, cardId: card.id, targetIds: selectedTargets.map((target) => target.id), energyCost: card.energy_cost }];
    caster.current_energy -= card.energy_cost;
    const casterPower = getCurrentStat(caster, Stat.Power);

    for (const effect of card.effects) {
      const targets = this.effectTargets(effect, caster, selectedTargets);
      for (const target of targets) {
        if (!target.is_alive) continue;
        const beforeHp = target.base_stats[Stat.HP];
        if (effect.operation === Operation.FLAT_SUB && effect.stat === Stat.HP && effect.duration === 0) {
          const actualDamage = Math.max(0, effect.value + casterPower - getCurrentStat(target, Stat.Defense));
          target.base_stats[Stat.HP] -= actualDamage;
          if (target.base_stats[Stat.HP] <= 0) target.is_alive = false;
          events.push({ type: "TARGET_DAMAGED", entityId: target.id, amount: display(beforeHp - target.base_stats[Stat.HP]), newHp: display(target.base_stats[Stat.HP]), isDead: !target.is_alive });
          if (!target.is_alive) events.push({ type: "ENTITY_DIED", entityId: target.id });
        } else if (effect.duration === 0) {
          if (effect.operation === Operation.FLAT_ADD) target.base_stats[effect.stat] += effect.value;
          if (effect.operation === Operation.FLAT_SUB) {
            target.base_stats[effect.stat] -= effect.value;
            if (effect.stat !== Stat.HP) target.base_stats[effect.stat] = Math.max(0, target.base_stats[effect.stat]);
          }
          if (effect.stat === Stat.HP && target.base_stats[Stat.HP] > beforeHp) {
            events.push({ type: "TARGET_HEALED", entityId: target.id, amount: display(target.base_stats[Stat.HP] - beforeHp), newHp: display(target.base_stats[Stat.HP]) });
          }
        } else {
          target.active_modifiers = applyStacking([...target.active_modifiers, effect]);
          events.push({ type: "MODIFIER_APPLIED", entityId: target.id, modifier: effect });
        }
      }
    }
    discardCard(caster, card.id);
    events.push({ type: "CARD_DISCARDED", entityId: caster.id, cardId: card.id });
    return events;
  }

  private effectTargets(effect: Modifier, caster: CombatEntity, selectedTargets: CombatEntity[]): CombatEntity[] {
    if (effect.target === Target.SELF) return [caster];
    if (effect.target === Target.ALLY_ALL) return this.allies(caster);
    if (effect.target === Target.ENEMY_ALL) return this.opponents(caster);
    if (effect.target === Target.GLOBAL) return this.entities.filter((entity) => entity.is_alive);
    return selectedTargets;
  }

  private checkEnd(): StepResult | null {
    const partyAlive = this.entities.some((entity) => entity.is_player && entity.is_alive);
    const enemyAlive = this.entities.some((entity) => !entity.is_player && entity.is_alive);
    if (partyAlive && enemyAlive) return null;
    const playerWon = partyAlive && !enemyAlive;
    this.status = playerWon ? CombatStepperStatus.COMBAT_WON : CombatStepperStatus.COMBAT_LOST;
    const survivors = this.entities.filter((entity) => entity.is_player && entity.is_alive).map((entity) => entity.id);
    return this.result([{ type: "COMBAT_ENDED", playerWon, survivors }]);
  }

  private applyOpeningModifiers(modifiers: Modifier[]): void {
    for (const modifier of modifiers) {
      for (const entity of this.entities) {
        if ((modifier.target === Target.ALLY_ALL && entity.is_player) || (modifier.target === Target.ENEMY_ALL && !entity.is_player) || modifier.target === Target.GLOBAL) {
          entity.active_modifiers = applyStacking([...entity.active_modifiers, modifier]);
        }
      }
    }
  }
}
