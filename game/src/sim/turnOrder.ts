import { calculateStat } from "./stats";
import { CT_THRESHOLD, HAND_SIZE, Stat, type Card, type CombatEntity } from "./types";
import type { SeededRng } from "./rng";

export function createCombatEntity(partial: Partial<CombatEntity> & Pick<CombatEntity, "id" | "name" | "base_stats">): CombatEntity {
  return {
    active_modifiers: [],
    ct: 0,
    is_player: true,
    card_pool: [],
    ai_heuristic: null,
    is_alive: true,
    current_energy: 0,
    draw_pile: [],
    hand: [],
    discard_pile: [],
    ...partial
  };
}

export function getCurrentStat(entity: CombatEntity, stat: Stat): number {
  return calculateStat(entity.base_stats[stat], entity.active_modifiers, stat);
}

export function tickUntilNextTurn(entities: CombatEntity[]): CombatEntity {
  const living = entities.filter((entity) => entity.is_alive);
  if (living.length === 0) throw new Error("No living entities to tick");

  let minTicks: number | null = null;
  for (const entity of living) {
    const speed = getCurrentStat(entity, Stat.Speed);
    if (speed <= 0) continue;
    const needed = Math.max(0, CT_THRESHOLD - entity.ct);
    const ticks = needed > 0 ? Math.ceil(needed / speed) : 0;
    if (minTicks === null || ticks < minTicks) minTicks = ticks;
  }

  if (minTicks === null) {
    const actor = living.sort((a, b) => entities.indexOf(a) - entities.indexOf(b))[0];
    actor.ct = 0;
    return actor;
  }

  for (const entity of living) {
    entity.ct += minTicks * getCurrentStat(entity, Stat.Speed);
  }

  const ready = living.filter((entity) => entity.ct >= CT_THRESHOLD);
  const candidates = ready.length > 0 ? ready : living;
  candidates.sort((a, b) => {
    const ctDiff = b.ct - a.ct;
    if (ctDiff !== 0) return ctDiff;
    const speedDiff = getCurrentStat(b, Stat.Speed) - getCurrentStat(a, Stat.Speed);
    if (speedDiff !== 0) return speedDiff;
    return entities.indexOf(a) - entities.indexOf(b);
  });

  const actor = candidates[0];
  actor.ct = actor.ct >= CT_THRESHOLD ? actor.ct - CT_THRESHOLD : 0;
  return actor;
}

export function processTurnStart(entity: CombatEntity, _encounterTurn = 0): string[] {
  const logs: string[] = [];
  entity.active_modifiers = entity.active_modifiers.map((modifier) =>
    modifier.duration > 0 ? { ...modifier, duration: modifier.duration - 1 } : modifier
  );
  const expired = entity.active_modifiers.filter((modifier) => modifier.duration === 0);
  entity.active_modifiers = entity.active_modifiers.filter((modifier) => modifier.duration !== 0);
  if (expired.length > 0) logs.push(`${entity.name}: ${expired.length} modifier(s) expired`);
  if (entity.is_alive && getCurrentStat(entity, Stat.HP) <= 0) {
    entity.is_alive = false;
    logs.push(`${entity.name} has died`);
  }
  entity.current_energy = getCurrentStat(entity, Stat.Energy);
  return logs;
}

export function initializeDeck(entity: CombatEntity, cardsById: Record<string, Card>, rng: Pick<SeededRng, "shuffle">): void {
  const deck: string[] = [];
  for (const cardId of entity.card_pool) {
    const card = cardsById[cardId];
    if (card) {
      for (let i = 0; i < (card.deck_copies ?? 1); i += 1) deck.push(cardId);
    }
  }
  rng.shuffle(deck);
  entity.draw_pile = deck;
  entity.hand = [];
  entity.discard_pile = [];
}

export function drawCards(entity: CombatEntity, count: number, rng: Pick<SeededRng, "shuffle">): string[] {
  const drawn: string[] = [];
  for (let i = 0; i < count; i += 1) {
    if (entity.draw_pile.length === 0) {
      if (entity.discard_pile.length === 0) break;
      entity.draw_pile = [...entity.discard_pile];
      entity.discard_pile = [];
      rng.shuffle(entity.draw_pile);
    }
    const cardId = entity.draw_pile.shift();
    if (cardId === undefined) break;
    entity.hand.push(cardId);
    drawn.push(cardId);
  }
  return drawn;
}

export function discardHand(entity: CombatEntity): void {
  entity.discard_pile.push(...entity.hand);
  entity.hand = [];
}

export function discardCard(entity: CombatEntity, cardId: string): void {
  const index = entity.hand.indexOf(cardId);
  if (index >= 0) {
    entity.hand.splice(index, 1);
    entity.discard_pile.push(cardId);
  }
}

export { HAND_SIZE };
