import { Operation, NarrativePosition, STAT_SCALE, Stacking, Stat, Target, type Card, type CombatEncounter, type Encounter, type Enemy, type EventChoice, type EventEncounter, type FlavorData, type HazardEncounter, type Modifier } from "../types";
import type { SeededRng } from "../rng";
import { generateEnemy } from "./enemies";

const ALL_STATS = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy];

const mod = (partial: Omit<Modifier, "tags"> & { tags?: string[] }): Modifier => ({ tags: [], ...partial });

export function generateEventChoices(rng: SeededRng, difficulty: number, numChoices = 2): EventChoice[] {
  const choices: EventChoice[] = [];
  for (let i = 0; i < numChoices; i += 1) {
    const effects: Modifier[] = [];
    for (let j = 0, count = rng.randint(1, 2); j < count; j += 1) {
      const stat = rng.choice(ALL_STATS);
      const operation = rng.choice([Operation.PCT_ADD, Operation.FLAT_ADD]);
      const value = operation === Operation.PCT_ADD ? rng.randint(5, 10) + difficulty * 2 : (rng.randint(1, 3) + difficulty) * STAT_SCALE;
      effects.push(mod({ stat, operation, value, duration: rng.randint(2, 5), target: Target.SELF, stacking: Stacking.stack }));
    }
    const cost: Modifier[] = [];
    for (let j = 0, count = rng.randint(1, 2); j < count; j += 1) {
      const stat = rng.choice(ALL_STATS);
      const operation = rng.choice([Operation.PCT_SUB, Operation.FLAT_SUB]);
      const value = operation === Operation.PCT_SUB ? rng.randint(3, 8) + difficulty : (rng.randint(1, 2) + difficulty) * STAT_SCALE;
      cost.push(mod({ stat, operation, value, duration: rng.randint(2, 5), target: Target.SELF, stacking: Stacking.stack }));
    }
    choices.push({ description: `A difficult choice at difficulty ${difficulty}`, effects, cost });
  }
  return choices;
}

function generateHazard(rng: SeededRng, position: NarrativePosition, difficulty: number, flavor: FlavorData): HazardEncounter {
  const hazard_modifiers: Modifier[] = [];
  for (let i = 0, count = rng.randint(1, 3); i < count; i += 1) {
    const stat = rng.choice(ALL_STATS);
    const operation = rng.choice([Operation.FLAT_SUB, Operation.PCT_SUB]);
    const value = operation === Operation.FLAT_SUB ? (rng.randint(1, 3) + difficulty) * STAT_SCALE : rng.randint(10, 25) + difficulty * 3;
    hazard_modifiers.push(mod({ stat, operation, value, duration: -1, target: Target.ALLY_ALL, stacking: Stacking.stack }));
  }
  const hazard_duration = rng.randint(2, 5);
  const adj = flavor.region_nouns.length ? rng.choice(flavor.region_nouns) : "Unknown";
  const name = `Hazardous ${adj}`;
  return { type: "hazard", narrative_position: position, name, description: `A ${name.toLowerCase()} blocks the path ahead.`, hazard_modifiers, hazard_duration };
}

function generateEvent(rng: SeededRng, position: NarrativePosition, difficulty: number, flavor: FlavorData): EventEncounter {
  const choices = generateEventChoices(rng, difficulty, rng.randint(2, 3));
  const noun = flavor.region_nouns.length ? rng.choice(flavor.region_nouns) : "Place";
  const name = `Crossroads of ${noun}`;
  return { type: "event", narrative_position: position, name, description: `A strange encounter at the ${name.toLowerCase()}.`, choices };
}

function generateCombat(
  rng: SeededRng,
  position: NarrativePosition,
  difficulty: number,
  availableCardIds: string[],
  flavor: FlavorData,
  forceElite: boolean,
  options: { enemyRegistry?: Map<string, Enemy>; cardsById?: Record<string, Card> | null }
): CombatEncounter {
  const enemies: string[] = [];
  const enemyCards: string[] = [];
  const add = (enemy: Enemy) => {
    enemies.push(enemy.id);
    enemyCards.push(...enemy.card_pool);
    options.enemyRegistry?.set(enemy.id, enemy);
  };
  if (forceElite) {
    add(generateEnemy(rng, difficulty, availableCardIds, { isElite: true, flavor, cardsById: options.cardsById }));
    for (let i = 0, count = rng.randint(0, 2); i < count; i += 1) add(generateEnemy(rng, difficulty, availableCardIds, { flavor, cardsById: options.cardsById }));
  } else {
    for (let i = 0, count = rng.randint(1, 3); i < count; i += 1) add(generateEnemy(rng, difficulty, availableCardIds, { flavor, cardsById: options.cardsById }));
  }
  const seen = new Set<string>();
  const uniqueCards = enemyCards.filter((id) => {
    if (seen.has(id)) return false;
    seen.add(id);
    return true;
  });
  const noun = flavor.region_nouns.length ? rng.choice(flavor.region_nouns) : "Ground";
  const name = `Battle at ${noun}`;
  return { type: "combat", narrative_position: position, name, description: `Enemies await at the ${name.toLowerCase()}.`, enemies, enemy_cards: uniqueCards };
}

export function generateEncounter(
  rng: SeededRng,
  position: NarrativePosition,
  difficulty: number,
  availableCardIds: string[],
  flavor: FlavorData,
  options: { enemyRegistry?: Map<string, Enemy>; cardsById?: Record<string, Card> | null } = {}
): Encounter {
  if (position === NarrativePosition.approach) return rng.random() < 0.6 ? generateHazard(rng, position, difficulty, flavor) : generateEvent(rng, position, difficulty, flavor);
  if (position === NarrativePosition.settlement) return rng.random() < 0.7 ? generateCombat(rng, position, difficulty, availableCardIds, flavor, false, options) : generateEvent(rng, position, difficulty, flavor);
  if (position === NarrativePosition.stronghold) return generateCombat(rng, position, difficulty, availableCardIds, flavor, true, options);
  throw new Error(`Unknown narrative position: ${position}`);
}
