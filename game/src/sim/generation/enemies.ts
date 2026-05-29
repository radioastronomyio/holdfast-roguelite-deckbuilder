import { AiHeuristic, STAT_SCALE, Stat, type Card, type Enemy, type FlavorData } from "../types";
import type { SeededRng } from "../rng";

const ROLE_WEIGHTS: Record<AiHeuristic, Record<Stat.HP | Stat.Power | Stat.Speed | Stat.Defense, number>> = {
  [AiHeuristic.aggressive]: { HP: 0.20, Power: 0.45, Speed: 0.25, Defense: 0.10 },
  [AiHeuristic.defensive]: { HP: 0.50, Power: 0.15, Speed: 0.15, Defense: 0.20 },
  [AiHeuristic.balanced]: { HP: 0.32, Power: 0.24, Speed: 0.24, Defense: 0.20 }
};

const COMBAT_STATS = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense] as const;

export function generateEnemy(
  rng: SeededRng,
  difficulty: number,
  availableCardIds: string[],
  options: { isElite?: boolean; flavor?: FlavorData | null; cardsById?: Record<string, Card> | null } = {}
): Enemy {
  const isElite = options.isElite ?? false;
  let cardIds = availableCardIds;
  if (options.cardsById) {
    cardIds = cardIds.filter((id) => !options.cardsById?.[id]?.tags.includes("hazard"));
  }

  let budget = 100 + difficulty * 25;
  if (isElite) budget = Math.trunc(budget * 1.5);
  const role = rng.choice([AiHeuristic.aggressive, AiHeuristic.defensive, AiHeuristic.balanced]);
  const weights = ROLE_WEIGHTS[role];
  const stats = {} as Record<Stat, number>;
  let remaining = budget;
  for (let i = 0; i < COMBAT_STATS.length; i += 1) {
    const stat = COMBAT_STATS[i];
    if (i === COMBAT_STATS.length - 1) {
      stats[stat] = remaining;
    } else {
      const baseAlloc = Math.trunc(budget * weights[stat]);
      const variance = Math.max(1, Math.floor(baseAlloc / 4));
      let alloc = rng.randint(Math.max(1, baseAlloc - variance), baseAlloc + variance);
      alloc = Math.min(alloc, remaining - (COMBAT_STATS.length - i - 1));
      alloc = Math.max(1, alloc);
      stats[stat] = alloc;
      remaining -= alloc;
    }
  }
  for (const stat of COMBAT_STATS) stats[stat] = Math.max(1, stats[stat]);
  const defenseCap = isElite ? 40 : 25;
  if (stats[Stat.Defense] > defenseCap) {
    const overflow = stats[Stat.Defense] - defenseCap;
    stats[Stat.Defense] = defenseCap;
    stats[Stat.HP] += overflow;
  }
  stats[Stat.Energy] = isElite ? rng.randint(3, 6) : rng.randint(2, 5);

  let cardPool: string[] = [];
  if (cardIds.length > 0) {
    const minPool = Math.min(isElite ? 3 : 2, cardIds.length);
    const maxPool = Math.min(isElite ? 5 : 4, cardIds.length);
    cardPool = rng.sample(cardIds, rng.randint(minPool, maxPool));
  }

  let name: string;
  if (options.flavor?.region_nouns.length && options.flavor.archetypes.length) {
    name = `${rng.choice(options.flavor.archetypes)} ${rng.choice(options.flavor.region_nouns)}`;
  } else {
    name = `Enemy D${difficulty}`;
  }

  return {
    id: `${name.toLowerCase().replaceAll(" ", "_")}_${rng.randint(1000, 9999)}`,
    name,
    base_stats: Object.fromEntries([Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy].map((stat) => [stat, stats[stat] * STAT_SCALE])) as Record<Stat, number>,
    card_pool: cardPool,
    ai_heuristic_tag: role,
    is_elite: isElite
  };
}
