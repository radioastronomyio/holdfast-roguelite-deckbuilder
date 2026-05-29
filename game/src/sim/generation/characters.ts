import { Operation, STAT_SCALE, Stacking, Stat, Target, type Character, type CharacterGenerationBounds, type FlavorData } from "../types";
import type { SeededRng } from "../rng";

type EpithetCondition =
  | { type: 1; stat: Stat; op: string; value: number }
  | { type: 2; stat_a: Stat; op_a: string; value_a: number; logic: "AND" | "OR" | "XOR"; stat_b: Stat; op_b: string; value_b: number };

interface EpithetEntry {
  epithet: string;
  conditions: EpithetCondition[];
}

const ALL_STATS = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy];

function compare(statValue: number, op: string, threshold: number): boolean {
  if (op === ">=") return statValue >= threshold;
  if (op === "<=") return statValue <= threshold;
  if (op === ">") return statValue > threshold;
  if (op === "<") return statValue < threshold;
  if (op === "=") return statValue === threshold;
  if (op === "<>") return statValue !== threshold;
  throw new Error(`Unknown operator: ${op}`);
}

export function evaluateEpithet(stats: Record<Stat, number>, entry: EpithetEntry): boolean {
  for (const condition of entry.conditions) {
    if (condition.type === 1) {
      if (!compare(stats[condition.stat], condition.op, condition.value)) return false;
    } else {
      const resultA = compare(stats[condition.stat_a], condition.op_a, condition.value_a);
      const resultB = compare(stats[condition.stat_b], condition.op_b, condition.value_b);
      if (condition.logic === "AND" && !(resultA && resultB)) return false;
      if (condition.logic === "OR" && !(resultA || resultB)) return false;
      if (condition.logic === "XOR" && !(resultA !== resultB)) return false;
    }
  }
  return true;
}

export function loadFlavorData(raw: FlavorData): FlavorData {
  return raw;
}

export function generateCharacter(rng: SeededRng, bounds: CharacterGenerationBounds, flavor: FlavorData): Character {
  const stats = Object.fromEntries(ALL_STATS.map((stat) => [stat, bounds.per_stat_min[stat]])) as Record<Stat, number>;
  const totalBudget = rng.randint(bounds.total_budget_min, bounds.total_budget_max);
  let remaining = totalBudget - ALL_STATS.reduce((sum, stat) => sum + stats[stat], 0);

  while (remaining > 0) {
    const growable = ALL_STATS.filter((stat) => stats[stat] < bounds.per_stat_max[stat]);
    if (growable.length === 0) break;
    const stat = rng.choice(growable);
    const room = bounds.per_stat_max[stat] - stats[stat];
    const add = rng.randint(1, Math.min(room, remaining));
    stats[stat] += add;
    remaining -= add;
  }

  const epithets = flavor.epithet_conditions as unknown as EpithetEntry[];
  const matchingEpithets = epithets.filter((entry) => evaluateEpithet(stats, entry));
  const epithet = matchingEpithets.length > 0 ? rng.choice(matchingEpithets).epithet : null;

  const maxValue = Math.max(...ALL_STATS.map((stat) => stats[stat]));
  const highestStat = rng.choice(ALL_STATS.filter((stat) => stats[stat] === maxValue));
  const pools = flavor.element_stat_map[highestStat.toLowerCase()];
  if (!pools) throw new Error(`Missing element pool for ${highestStat}`);
  rng.random() < 0.8 ? rng.choice(pools.default) : rng.choice(pools.rare);

  const passiveValue = rng.randint(10, 25);
  const firstName = rng.choice(flavor.given_names);
  const archetype = rng.choice(flavor.archetypes);
  const regionNoun = rng.choice(flavor.region_nouns);
  const name = epithet
    ? `${firstName}, ${epithet} ${archetype} from the ${regionNoun}`
    : `${firstName}, ${archetype} from the ${regionNoun}`;

  return {
    id: `${firstName}_${archetype}`.toLowerCase().replaceAll(" ", "_"),
    name,
    base_stats: Object.fromEntries(ALL_STATS.map((stat) => [stat, stats[stat] * STAT_SCALE])) as Record<Stat, number>,
    innate_passive: {
      stat: highestStat,
      operation: Operation.PCT_ADD,
      value: passiveValue,
      duration: -1,
      target: Target.SELF,
      stacking: Stacking.stack,
      tags: ["passive"]
    },
    name_parts: {
      first_name: firstName,
      title: archetype,
      origin: regionNoun
    }
  };
}
