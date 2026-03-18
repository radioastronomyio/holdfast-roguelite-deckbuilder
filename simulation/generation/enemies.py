"""Enemy generation — pure functions producing Enemies from RNG + difficulty."""

import random
from typing import List, Optional

from models.entity import Enemy
from models.modifier import STAT_SCALE
from models.enums import Stat, AiHeuristic
from generation.characters import FlavorData


# Role weight profiles: {stat: weight}
_ROLE_WEIGHTS = {
    AiHeuristic.aggressive: {
        Stat.HP: 0.15, Stat.Power: 0.35, Stat.Speed: 0.25, Stat.Defense: 0.10, Stat.Energy: 0.15,
    },
    AiHeuristic.defensive: {
        Stat.HP: 0.35, Stat.Power: 0.10, Stat.Speed: 0.15, Stat.Defense: 0.25, Stat.Energy: 0.15,
    },
    AiHeuristic.balanced: {
        Stat.HP: 0.25, Stat.Power: 0.20, Stat.Speed: 0.20, Stat.Defense: 0.20, Stat.Energy: 0.15,
    },
}


def generate_enemy(
    rng: random.Random,
    difficulty: int,
    available_card_ids: list[str],
    is_elite: bool = False,
    flavor: FlavorData | None = None,
) -> Enemy:
    """Generate a procedural enemy."""
    # 1. Base stat budget
    budget = 150 + (difficulty * 30)
    if is_elite:
        budget = int(budget * 1.5)

    # 2. Role selection and stat distribution
    role = rng.choice([AiHeuristic.aggressive, AiHeuristic.defensive, AiHeuristic.balanced])
    weights = _ROLE_WEIGHTS[role]

    all_stats = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy]
    stats: dict[Stat, int] = {}
    remaining = budget
    for i, stat in enumerate(all_stats):
        if i == len(all_stats) - 1:
            stats[stat] = remaining
        else:
            # Allocate proportionally with some variance
            base_alloc = int(budget * weights[stat])
            variance = max(1, base_alloc // 4)
            alloc = rng.randint(max(1, base_alloc - variance), base_alloc + variance)
            alloc = min(alloc, remaining - (len(all_stats) - i - 1))  # leave at least 1 per remaining stat
            alloc = max(1, alloc)
            stats[stat] = alloc
            remaining -= alloc

    # Ensure all stats are at least 1
    for stat in all_stats:
        if stats[stat] < 1:
            stats[stat] = 1

    # 3. Card pool
    if is_elite:
        pool_size = rng.randint(3, min(5, len(available_card_ids)))
    else:
        pool_size = rng.randint(2, min(4, len(available_card_ids)))
    card_pool = rng.sample(available_card_ids, pool_size)

    # 4. Name generation
    if flavor and flavor.region_nouns and flavor.archetypes:
        adj = rng.choice(flavor.archetypes)
        noun = rng.choice(flavor.region_nouns)
        name = f"{adj} {noun}"
    else:
        name = f"Enemy D{difficulty}"
        adj = "enemy"
        noun = f"d{difficulty}"

    # 5. Scale stats
    base_stats = {s: v * STAT_SCALE for s, v in stats.items()}

    # 6. Build ID
    enemy_id = f"{name.lower().replace(' ', '_')}_{rng.randint(1000, 9999)}"

    return Enemy(
        id=enemy_id,
        name=name,
        base_stats=base_stats,
        card_pool=card_pool,
        ai_heuristic_tag=role,
        is_elite=is_elite,
    )
