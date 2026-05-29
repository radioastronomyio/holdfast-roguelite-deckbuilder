import { Operation, NarrativePosition, STAT_SCALE, Stacking, Stat, Target, type Card, type Enemy, type FlavorData, type Modifier, type Region } from "../types";
import type { SeededRng } from "../rng";
import { generateEncounter } from "./encounters";

const ALL_STATS = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy];

const mod = (partial: Omit<Modifier, "tags"> & { tags?: string[] }): Modifier => ({ tags: [], ...partial });

export function generateRegion(
  rng: SeededRng,
  difficulty: number,
  availableCardIds: string[],
  flavor: FlavorData,
  options: { regionAdjectives?: string[]; enemyRegistry?: Map<string, Enemy>; cardsById?: Record<string, Card> | null } = {}
): Region {
  const adjectives = options.regionAdjectives ?? flavor.region_adjectives;
  const adjective = rng.choice(adjectives);
  const noun = rng.choice(flavor.region_nouns);
  const name = `${adjective} ${noun}`;
  const modifier_stack: Modifier[] = [];
  for (let i = 0, count = rng.randint(1, Math.min(3, 1 + Math.floor(difficulty / 2))); i < count; i += 1) {
    const stat = rng.choice(ALL_STATS);
    const isPct = rng.choice([true, false]);
    const operation = isPct ? rng.choice([Operation.PCT_ADD, Operation.PCT_SUB]) : rng.choice([Operation.FLAT_ADD, Operation.FLAT_SUB]);
    const value = isPct ? rng.randint(5, 15) + difficulty * 2 : rng.randint(2, 8) * STAT_SCALE + difficulty * STAT_SCALE;
    const target = rng.choice([Target.ALLY_ALL, Target.ENEMY_ALL]);
    modifier_stack.push(mod({ stat, operation, value, duration: -1, target, stacking: Stacking.stack }));
  }
  const encounters = [
    generateEncounter(rng, NarrativePosition.approach, difficulty, availableCardIds, flavor, options),
    generateEncounter(rng, NarrativePosition.settlement, difficulty, availableCardIds, flavor, options),
    generateEncounter(rng, NarrativePosition.stronghold, difficulty, availableCardIds, flavor, options)
  ];
  const rewardStat = rng.choice(ALL_STATS);
  const rewardOperation = rng.choice([Operation.FLAT_ADD, Operation.PCT_ADD]);
  const rewardValue = rewardOperation === Operation.FLAT_ADD ? rng.randint(1, 3) * STAT_SCALE : rng.randint(5, 15);
  return {
    id: `${adjective}_${noun}`.toLowerCase().replaceAll(" ", "_"),
    name,
    region_type: adjective,
    modifier_stack,
    encounters,
    meta_reward: mod({ stat: rewardStat, operation: rewardOperation, value: rewardValue, duration: -1, target: Target.SELF, stacking: Stacking.stack }),
    research_layers: [
      { level: 1, reveal_type: "region_type", cost: 10 * difficulty },
      { level: 2, reveal_type: "primary_modifier", cost: 25 * difficulty },
      { level: 3, reveal_type: "encounter_details", cost: 50 * difficulty },
      { level: 4, reveal_type: "boss_mechanics", cost: 100 * difficulty }
    ]
  };
}
