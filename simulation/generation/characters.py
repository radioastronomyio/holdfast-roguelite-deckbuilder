"""Character generation — pure functions producing Characters from RNG + data pools."""

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from models.entity import Character, CharacterGenerationBounds
from models.modifier import Modifier, STAT_SCALE
from models.flavor import ElementStatMap, EpithetEntry, EpithetCondition1, EpithetCondition2
from models.enums import Stat, Operation, Target, Stacking


@dataclass
class FlavorData:
    """All flavor pool data needed for generation."""
    given_names: list[str]
    archetypes: list[str]
    region_nouns: list[str]
    element_stat_map: ElementStatMap
    epithet_conditions: list[EpithetEntry]


def load_flavor_data(mods_path: Path = Path("mods/default/flavor")) -> FlavorData:
    """Load all flavor pools from mod directory."""
    with open(mods_path / "given_names.json") as f:
        given_names = json.load(f)
    with open(mods_path / "archetypes.json") as f:
        archetypes = json.load(f)
    with open(mods_path / "region_nouns.json") as f:
        region_nouns = json.load(f)
    with open(mods_path / "element-stat-map.json") as f:
        element_stat_map = ElementStatMap(**json.load(f))
    with open(mods_path / "epithet-conditions.json") as f:
        raw = json.load(f)
        epithet_conditions = [EpithetEntry(**entry) for entry in raw]

    return FlavorData(
        given_names=given_names,
        archetypes=archetypes,
        region_nouns=region_nouns,
        element_stat_map=element_stat_map,
        epithet_conditions=epithet_conditions,
    )


def _compare(stat_value: int, op: str, threshold: int) -> bool:
    """Evaluate a comparison operator."""
    if op == ">=":
        return stat_value >= threshold
    elif op == "<=":
        return stat_value <= threshold
    elif op == ">":
        return stat_value > threshold
    elif op == "<":
        return stat_value < threshold
    elif op == "=":
        return stat_value == threshold
    elif op == "<>":
        return stat_value != threshold
    raise ValueError(f"Unknown operator: {op}")


def evaluate_epithet(
    stats: Dict[Stat, int],
    condition: EpithetEntry,
) -> bool:
    """
    Evaluate whether a character's stats satisfy an epithet's conditions.
    Stats are at display scale. All conditions in the entry must be met.
    """
    for cond in condition.conditions:
        if cond.type == 1:
            if not _compare(stats[cond.stat], cond.op, cond.value):
                return False
        elif cond.type == 2:
            result_a = _compare(stats[cond.stat_a], cond.op_a, cond.value_a)
            result_b = _compare(stats[cond.stat_b], cond.op_b, cond.value_b)
            if cond.logic == "AND":
                if not (result_a and result_b):
                    return False
            elif cond.logic == "OR":
                if not (result_a or result_b):
                    return False
            elif cond.logic == "XOR":
                if not (result_a ^ result_b):
                    return False
    return True


def _stat_key_to_element_map_key(stat: Stat) -> str:
    """Convert Stat enum to element_stat_map field name."""
    return stat.value.lower()


def generate_character(
    rng: random.Random,
    bounds: CharacterGenerationBounds,
    flavor: FlavorData,
) -> Character:
    """Generate a procedural character."""
    all_stats = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy]

    # 1. Allocate stats within bounds
    stats: Dict[Stat, int] = {}
    for s in all_stats:
        stats[s] = bounds.per_stat_min[s]

    total_budget = rng.randint(bounds.total_budget_min, bounds.total_budget_max)
    remaining = total_budget - sum(stats.values())

    # Distribute remaining budget randomly, respecting per_stat_max
    while remaining > 0:
        # Find stats that can still grow
        growable = [s for s in all_stats if stats[s] < bounds.per_stat_max[s]]
        if not growable:
            break
        stat = rng.choice(growable)
        room = bounds.per_stat_max[stat] - stats[stat]
        add = rng.randint(1, min(room, remaining))
        stats[stat] += add
        remaining -= add

    # 2. Evaluate epithet conditions against display-scale stats
    matching_epithets = [
        entry for entry in flavor.epithet_conditions
        if evaluate_epithet(stats, entry)
    ]
    epithet = rng.choice(matching_epithets).epithet if matching_epithets else None

    # 3. Select innate passive based on highest stat
    stat_values = [(s, stats[s]) for s in all_stats]
    max_val = max(v for _, v in stat_values)
    highest_stats = [s for s, v in stat_values if v == max_val]
    highest_stat = rng.choice(highest_stats)

    map_key = _stat_key_to_element_map_key(highest_stat)
    pools = getattr(flavor.element_stat_map, map_key)

    if rng.random() < 0.8:
        element = rng.choice(pools["default"])
    else:
        element = rng.choice(pools["rare"])

    passive_value = rng.randint(10, 25)
    innate_passive = Modifier(
        stat=highest_stat,
        operation=Operation.PCT_ADD,
        value=passive_value,
        duration=-1,
        target=Target.SELF,
        stacking=Stacking.stack,
        tags=["passive"],
    )

    # 4. Assemble name
    first_name = rng.choice(flavor.given_names)
    archetype = rng.choice(flavor.archetypes)
    region_noun = rng.choice(flavor.region_nouns)

    if epithet:
        name = f"{first_name}, {epithet} {archetype} from the {region_noun}"
    else:
        name = f"{first_name}, {archetype} from the {region_noun}"

    # 5. Scale stats
    base_stats = {s: v * STAT_SCALE for s, v in stats.items()}

    # 6. Build ID
    char_id = f"{first_name}_{archetype}".lower().replace(" ", "_")

    return Character(
        id=char_id,
        name=name,
        base_stats=base_stats,
        innate_passive=innate_passive,
        name_parts={
            "first_name": first_name,
            "title": archetype,
            "origin": region_noun,
        },
    )
