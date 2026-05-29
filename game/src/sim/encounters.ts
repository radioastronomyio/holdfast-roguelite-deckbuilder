import { applyStacking } from "./stats";
import { discardCard, discardHand, drawCards, getCurrentStat, initializeDeck, processTurnStart, tickUntilNextTurn } from "./turnOrder";
import { COMBAT_TURN_CAP, HAND_SIZE, Operation, STAT_SCALE, Stat, Target, type Card, type CombatEntity, type EventChoice, type Modifier } from "./types";
import type { SeededRng } from "./rng";
import type { PlayerStrategy, StrategyCampaignState } from "./strategies";

export interface CardPlayRecord {
  turn_number: number;
  caster_id: string;
  card_id: string;
  energy_cost: number;
  targets: string[];
  damage_total: number;
  healing_total: number;
}

export interface CombatResult {
  player_won: boolean;
  turns_taken: number;
  survivors: string[];
  combat_log: string[];
  final_state: CombatEntity[];
  card_plays: CardPlayRecord[];
  entity_turns: Record<string, number>;
  damage_dealt: Record<string, number>;
  damage_taken: Record<string, number>;
  healing_done: Record<string, number>;
  final_hp: Record<string, number>;
  hit_turn_cap: boolean;
  speed_action_ratios: Record<string, number>;
}

export interface HazardResult {
  survived: boolean;
  damage_taken: Record<string, number>;
  combat_log: string[];
  final_state: CombatEntity[];
}

export interface EventResult {
  choice_index: number;
  effects_applied: Modifier[];
  costs_applied: Modifier[];
  combat_log: string[];
  final_state: CombatEntity[];
}

export function playCard(card: Card, caster: CombatEntity, targets: CombatEntity[], allEntities: CombatEntity[]): string[] {
  const logs: string[] = [];
  if (caster.current_energy < card.energy_cost) {
    throw new Error(`${caster.name} lacks energy to play ${card.id}`);
  }
  caster.current_energy -= card.energy_cost;
  const casterPower = getCurrentStat(caster, Stat.Power);
  const allies = allEntities.filter((entity) => entity.is_player === caster.is_player && entity.is_alive);
  const enemies = allEntities.filter((entity) => entity.is_player !== caster.is_player && entity.is_alive);

  for (const effect of card.effects) {
    let effectTargets: CombatEntity[];
    if (effect.target === Target.SELF) effectTargets = [caster];
    else if (effect.target === Target.ALLY_ALL) effectTargets = allies;
    else if (effect.target === Target.ENEMY_ALL) effectTargets = enemies;
    else if (effect.target === Target.GLOBAL) effectTargets = allEntities.filter((entity) => entity.is_alive);
    else effectTargets = targets;

    for (const target of effectTargets) {
      if (!target.is_alive) continue;
      if (effect.operation === Operation.FLAT_SUB && effect.stat === Stat.HP && effect.duration === 0) {
        const actualDamage = Math.max(0, effect.value + casterPower - getCurrentStat(target, Stat.Defense));
        target.base_stats[Stat.HP] -= actualDamage;
        logs.push(`${caster.name} dealt ${Math.floor(actualDamage / STAT_SCALE)} HP damage to ${target.name}`);
        if (target.base_stats[Stat.HP] <= 0) {
          target.is_alive = false;
          logs.push(`${target.name} has died`);
        }
      } else if (effect.duration === 0) {
        if (effect.operation === Operation.FLAT_ADD) target.base_stats[effect.stat] += effect.value;
        if (effect.operation === Operation.FLAT_SUB) {
          target.base_stats[effect.stat] -= effect.value;
          if (effect.stat !== Stat.HP) target.base_stats[effect.stat] = Math.max(0, target.base_stats[effect.stat]);
        }
        logs.push(`${effect.stat} modified on ${target.name}`);
      } else {
        target.active_modifiers = applyStacking([...target.active_modifiers, effect]);
        logs.push(`Applied ${effect.stat} ${effect.operation} to ${target.name}`);
      }
    }
  }
  return logs;
}

function damageScore(card: Card): number {
  return card.effects
    .filter((effect) => effect.stat === Stat.HP && effect.operation === Operation.FLAT_SUB)
    .reduce((sum, effect) => sum + effect.value, 0);
}

function isAoe(card: Card): boolean {
  return card.effects.some((effect) => effect.target === Target.ENEMY_ALL);
}

function pickCard(caster: CombatEntity, availableCards: Card[], enemies: CombatEntity[]): [Card, CombatEntity[]] | null {
  const living = enemies.filter((enemy) => enemy.is_alive);
  const affordable = availableCards.filter((card) => card.energy_cost <= caster.current_energy);
  if (living.length === 0 || affordable.length === 0) return null;
  const card = affordable.reduce((best, current) => damageScore(current) > damageScore(best) ? current : best);
  return [card, isAoe(card) ? living : [living.reduce((low, current) => getCurrentStat(current, Stat.HP) < getCurrentStat(low, Stat.HP) ? current : low)]];
}

function finalHp(entities: CombatEntity[]): Record<string, number> {
  return Object.fromEntries(entities.map((entity) => [entity.id, Math.floor(entity.base_stats[Stat.HP] / STAT_SCALE)]));
}

export function resolveCombat(
  party: CombatEntity[],
  enemies: CombatEntity[],
  cardsById: Record<string, Card> = {},
  options: { region_modifiers?: Modifier[]; world_modifiers?: Modifier[]; player_strategy?: PlayerStrategy; strategy_state?: StrategyCampaignState; rng?: Pick<SeededRng, "shuffle"> } = {}
): CombatResult {
  const rng = options.rng ?? {
    shuffle: <T>(array: T[]) => {
      for (let i = array.length - 1; i > 0; i -= 1) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
      }
    }
  };
  const logs: string[] = [];
  const allEntities = [...party, ...enemies];
  for (const mod of options.region_modifiers ?? []) {
    for (const entity of allEntities) {
      if ((mod.target === Target.ALLY_ALL && entity.is_player) || (mod.target === Target.ENEMY_ALL && !entity.is_player) || mod.target === Target.GLOBAL) {
        entity.active_modifiers = applyStacking([...entity.active_modifiers, mod]);
      }
    }
  }
  for (const mod of options.world_modifiers ?? []) {
    for (const entity of allEntities) entity.active_modifiers = applyStacking([...entity.active_modifiers, mod]);
  }
  for (const entity of allEntities) {
    entity.current_energy = getCurrentStat(entity, Stat.Energy);
    initializeDeck(entity, cardsById, rng);
    drawCards(entity, HAND_SIZE, rng);
  }

  let turnsTaken = 0;
  const entityTurns = Object.fromEntries(allEntities.map((entity) => [entity.id, 0]));
  const damageDealt = Object.fromEntries(allEntities.map((entity) => [entity.id, 0]));
  const damageTaken = Object.fromEntries(allEntities.map((entity) => [entity.id, 0]));
  const healingDone = Object.fromEntries(allEntities.map((entity) => [entity.id, 0]));
  const cardPlays: CardPlayRecord[] = [];

  const makeResult = (won: boolean, hitCap: boolean): CombatResult => ({
    player_won: won,
    turns_taken: turnsTaken,
    survivors: party.filter((entity) => entity.is_alive).map((entity) => entity.id),
    combat_log: logs,
    final_state: allEntities,
    card_plays: cardPlays,
    entity_turns: entityTurns,
    damage_dealt: damageDealt,
    damage_taken: damageTaken,
    healing_done: healingDone,
    final_hp: finalHp(allEntities),
    hit_turn_cap: hitCap,
    speed_action_ratios: {}
  });

  while (true) {
    if (!enemies.some((enemy) => enemy.is_alive)) return makeResult(true, false);
    if (!party.some((player) => player.is_alive)) return makeResult(false, false);
    if (turnsTaken >= COMBAT_TURN_CAP) return makeResult(false, true);

    const actor = tickUntilNextTurn(allEntities);
    logs.push(...processTurnStart(actor, turnsTaken + 1));
    turnsTaken += 1;
    entityTurns[actor.id] = (entityTurns[actor.id] ?? 0) + 1;
    if (!actor.is_alive) continue;

    discardHand(actor);
    drawCards(actor, HAND_SIZE, rng);

    while (actor.is_alive) {
      const opponents = actor.is_player ? enemies : party;
      if (!opponents.some((entity) => entity.is_alive)) break;
      const handCards = actor.hand.map((id) => cardsById[id]).filter((card): card is Card => Boolean(card));
      const action = actor.is_player && options.player_strategy && options.strategy_state
        ? options.player_strategy.selectCard(actor, handCards, party.filter((entity) => entity.is_alive), enemies.filter((entity) => entity.is_alive))
        : pickCard(actor, handCards, opponents);
      if (!action) break;
      const [card, targets] = action;
      const before = new Map(allEntities.map((entity) => [entity.id, entity.base_stats[Stat.HP]]));
      logs.push(...playCard(card, actor, targets, allEntities));
      discardCard(actor, card.id);
      let damageTotal = 0;
      let healingTotal = 0;
      for (const entity of allEntities) {
        const delta = (before.get(entity.id) ?? entity.base_stats[Stat.HP]) - entity.base_stats[Stat.HP];
        if (delta > 0) {
          const display = Math.floor(delta / STAT_SCALE);
          damageTotal += display;
          damageDealt[actor.id] += display;
          damageTaken[entity.id] += display;
        } else if (delta < 0) {
          const display = Math.floor(-delta / STAT_SCALE);
          healingTotal += display;
          healingDone[actor.id] += display;
        }
      }
      cardPlays.push({ turn_number: turnsTaken, caster_id: actor.id, card_id: card.id, energy_cost: card.energy_cost, targets: targets.map((target) => target.id), damage_total: damageTotal, healing_total: healingTotal });
    }
  }
}

export function resolveHazard(
  party: CombatEntity[],
  hazardModifiers: Modifier[],
  hazardDuration: number,
  regionModifiers: Modifier[] = [],
  worldModifiers: Modifier[] = []
): HazardResult {
  const logs: string[] = [];
  const damageTaken = Object.fromEntries(party.map((entity) => [entity.id, 0]));
  for (const mod of [...regionModifiers, ...worldModifiers]) {
    for (const entity of party) entity.active_modifiers = applyStacking([...entity.active_modifiers, mod]);
  }
  for (let turn = 0; turn < hazardDuration; turn += 1) {
    for (const entity of party) {
      if (!entity.is_alive) continue;
      for (const mod of hazardModifiers) {
        if (mod.stat === Stat.HP && mod.operation === Operation.FLAT_SUB) {
          const damage = Math.max(0, mod.value - getCurrentStat(entity, Stat.Defense));
          entity.base_stats[Stat.HP] -= damage;
          damageTaken[entity.id] += damage;
          if (entity.base_stats[Stat.HP] <= 0) {
            entity.is_alive = false;
            logs.push(`${entity.name} died to hazard`);
          }
        }
      }
    }
  }
  return { survived: party.some((entity) => entity.is_alive), damage_taken: damageTaken, combat_log: logs, final_state: party };
}

export function resolveEvent(party: CombatEntity[], choices: EventChoice[], choiceIndex: number): EventResult {
  if (choiceIndex < 0 || choiceIndex >= choices.length) {
    throw new Error(`Invalid choice index ${choiceIndex} for event with ${choices.length} choices`);
  }
  const choice = choices[choiceIndex];
  for (const mod of choice.effects) {
    for (const entity of party) entity.active_modifiers = applyStacking([...entity.active_modifiers, mod]);
  }
  for (const mod of choice.cost) {
    for (const entity of party) {
      if (mod.stat === Stat.HP && mod.operation === Operation.FLAT_SUB) entity.base_stats[Stat.HP] -= mod.value;
      else entity.active_modifiers = applyStacking([...entity.active_modifiers, mod]);
    }
  }
  return { choice_index: choiceIndex, effects_applied: choice.effects, costs_applied: choice.cost, combat_log: [`Event choice ${choiceIndex} applied: ${choice.description}`], final_state: party };
}
