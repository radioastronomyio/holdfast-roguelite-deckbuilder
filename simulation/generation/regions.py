"""Region generation — pure functions producing Regions from RNG + difficulty + data pools."""

import json
import random
from pathlib import Path
from typing import List

from models.campaign import Region, ResearchLayer
from models.modifier import Modifier, STAT_SCALE
from models.enums import Stat, Operation, Target, Stacking, NarrativePosition
from generation.characters import FlavorData
from generation.encounters import generate_encounter


def _load_region_adjectives(mods_path: Path = Path("mods/default/flavor")) -> list[str]:
    """Load region adjectives from mod directory."""
    with open(mods_path / "region_adjectives.json") as f:
        return json.load(f)


def generate_region(
    rng: random.Random,
    difficulty: int,
    available_card_ids: list[str],
    flavor: FlavorData,
    region_adjectives: list[str] | None = None,
    enemy_registry: dict | None = None,
) -> Region:
    """Generate a procedural region."""
    # Load adjectives if not provided
    if region_adjectives is None:
        region_adjectives = _load_region_adjectives()

    # 1. Name
    adjective = rng.choice(region_adjectives)
    noun = rng.choice(flavor.region_nouns)
    name = f"{adjective} {noun}"

    # 2. Region type
    region_type = adjective

    # 3. Modifier stack: 1-3 permanent modifiers scaled to difficulty
    num_mods = rng.randint(1, min(3, 1 + difficulty // 2))
    all_stats = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy]
    pct_ops = [Operation.PCT_ADD, Operation.PCT_SUB]
    flat_ops = [Operation.FLAT_ADD, Operation.FLAT_SUB]
    targets = [Target.ALLY_ALL, Target.ENEMY_ALL]

    modifier_stack = []
    for _ in range(num_mods):
        stat = rng.choice(all_stats)
        is_pct = rng.choice([True, False])
        if is_pct:
            op = rng.choice(pct_ops)
            value = rng.randint(5, 15) + difficulty * 2
        else:
            op = rng.choice(flat_ops)
            value = rng.randint(2, 8) * STAT_SCALE + difficulty * STAT_SCALE
        target = rng.choice(targets)
        modifier_stack.append(Modifier(
            stat=stat,
            operation=op,
            value=value,
            duration=-1,
            target=target,
            stacking=Stacking.stack,
        ))

    # 4. Generate 3 encounters
    encounters = [
        generate_encounter(rng, NarrativePosition.approach, difficulty, available_card_ids, flavor, enemy_registry),
        generate_encounter(rng, NarrativePosition.settlement, difficulty, available_card_ids, flavor, enemy_registry),
        generate_encounter(rng, NarrativePosition.stronghold, difficulty, available_card_ids, flavor, enemy_registry),
    ]

    # 5. Meta-reward
    reward_stat = rng.choice(all_stats)
    reward_op = rng.choice([Operation.FLAT_ADD, Operation.PCT_ADD])
    if reward_op == Operation.FLAT_ADD:
        reward_value = rng.randint(1, 3) * STAT_SCALE
    else:
        reward_value = rng.randint(5, 15)

    meta_reward = Modifier(
        stat=reward_stat,
        operation=reward_op,
        value=reward_value,
        duration=-1,
        target=Target.SELF,
        stacking=Stacking.stack,
    )

    # 6. Research layers
    research_layers = [
        ResearchLayer(level=1, reveal_type="region_type", cost=10 * difficulty),
        ResearchLayer(level=2, reveal_type="primary_modifier", cost=25 * difficulty),
        ResearchLayer(level=3, reveal_type="encounter_details", cost=50 * difficulty),
        ResearchLayer(level=4, reveal_type="boss_mechanics", cost=100 * difficulty),
    ]

    # 7. Build ID
    region_id = f"{adjective}_{noun}".lower().replace(" ", "_")

    return Region(
        id=region_id,
        name=name,
        region_type=region_type,
        modifier_stack=modifier_stack,
        encounters=encounters,
        meta_reward=meta_reward,
        research_layers=research_layers,
    )
