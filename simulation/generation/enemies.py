"""Enemy generation — pure functions producing Enemies from RNG + difficulty."""

import random
from typing import List, Optional

from models.entity import Enemy
from models.modifier import STAT_SCALE
from models.enums import Stat, AiHeuristic
from generation.characters import FlavorData


# Role weight profiles: {stat: weight} — 4 combat stats only, Energy set separately
# Defensive role tanks via HP, not invulnerable Defense; weights sum to 1.0
_ROLE_WEIGHTS = {
    AiHeuristic.aggressive: {
        Stat.HP: 0.20, Stat.Power: 0.45, Stat.Speed: 0.25, Stat.Defense: 0.10,
    },
    AiHeuristic.defensive: {
        Stat.HP: 0.50, Stat.Power: 0.15, Stat.Speed: 0.15, Stat.Defense: 0.20,
    },
    AiHeuristic.balanced: {
        Stat.HP: 0.32, Stat.Power: 0.24, Stat.Speed: 0.24, Stat.Defense: 0.20,
    },
}

# Hard cap on Defense in display-scale to prevent invulnerability
_DEFENSE_CAP_NORMAL = 20
_DEFENSE_CAP_ELITE = 30


def generate_enemy(
    rng: random.Random,
    difficulty: int,
    available_card_ids: list[str],
    is_elite: bool = False,
    flavor: FlavorData | None = None,
    cards_by_id: dict | None = None,
) -> Enemy:
    """Generate a procedural enemy."""
    # Filter out hazard cards — enemies must not play cards that debuff their own side
    if cards_by_id is not None:
        available_card_ids = [
            cid for cid in available_card_ids
            if "hazard" not in (cards_by_id[cid].tags if cid in cards_by_id else [])
        ]

    # 1. Base stat budget (reduced from 150 so diff-1 enemies are clearly weaker than players)
    budget = 90 + (difficulty * 25)
    if is_elite:
        budget = int(budget * 1.5)

    # 2. Role selection and stat distribution across 4 combat stats (HP/Power/Speed/Defense)
    role = rng.choice([AiHeuristic.aggressive, AiHeuristic.defensive, AiHeuristic.balanced])
    weights = _ROLE_WEIGHTS[role]

    combat_stats = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense]
    stats: dict[Stat, int] = {}
    remaining = budget
    for i, stat in enumerate(combat_stats):
        if i == len(combat_stats) - 1:
            stats[stat] = remaining
        else:
            # Allocate proportionally with some variance
            base_alloc = int(budget * weights[stat])
            variance = max(1, base_alloc // 4)
            alloc = rng.randint(max(1, base_alloc - variance), base_alloc + variance)
            alloc = min(alloc, remaining - (len(combat_stats) - i - 1))  # leave at least 1 per remaining stat
            alloc = max(1, alloc)
            stats[stat] = alloc
            remaining -= alloc

    # Ensure all combat stats are at least 1
    for stat in combat_stats:
        if stats[stat] < 1:
            stats[stat] = 1

    # Cap Defense to prevent invulnerability (player best single-hit is ~50 raw at diff 1)
    defense_cap = _DEFENSE_CAP_ELITE if is_elite else _DEFENSE_CAP_NORMAL
    if stats[Stat.Defense] > defense_cap:
        overflow = stats[Stat.Defense] - defense_cap
        stats[Stat.Defense] = defense_cap
        stats[Stat.HP] += overflow  # redirect excess Defense budget into HP

    # Energy is a resource stat — set from a fixed range independent of combat budget
    stats[Stat.Energy] = rng.randint(3, 6) if is_elite else rng.randint(2, 5)

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
