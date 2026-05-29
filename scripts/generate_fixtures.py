#!/usr/bin/env python3
"""Generate deterministic Python golden fixtures for the TypeScript sim port."""

from __future__ import annotations

import json
import platform
import random
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIM = ROOT / "simulation"
if str(SIM) not in sys.path:
    sys.path.insert(0, str(SIM))

from agents.heuristics import AggressiveAI  # noqa: E402
from campaign.loader import load_game_data  # noqa: E402
from campaign.runner import character_to_combat_entity, enemy_data_to_combat_entity, run_campaign  # noqa: E402
from engine.encounters import resolve_combat  # noqa: E402
from engine.stats import calculate_stat  # noqa: E402
from models.enums import Operation, Stacking, Stat, Target  # noqa: E402
from models.modifier import Modifier, STAT_SCALE  # noqa: E402


FIXTURE_DIR = ROOT / "game" / "src" / "sim" / "__fixtures__"


def dump(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def modifier(stat: Stat, op: Operation, value: int, duration: int = -1) -> Modifier:
    return Modifier(
        stat=stat,
        operation=op,
        value=value,
        duration=duration,
        target=Target.SELF,
        stacking=Stacking.stack,
        tags=[],
    )


def rng_fixture() -> dict:
    r = random.Random(12345)
    random_values = [r.random() for _ in range(1000)]
    r = random.Random(12345)
    bits = [r.getrandbits(32) for _ in range(1000)]
    r = random.Random(12345)
    below = [r.randrange(100) for _ in range(1000)]
    r = random.Random(12345)
    choices = [r.choice(list(range(10))) for _ in range(1000)]
    r = random.Random(12345)
    shuffles = []
    for _ in range(1000):
        values = list(range(10))
        r.shuffle(values)
        shuffles.append(values)
    r = random.Random(99999)
    randint = [r.randint(1, 100) for _ in range(500)]
    return {
        "seed": 12345,
        "random": random_values,
        "getrandbits32": bits,
        "randbelow100": below,
        "choice10": choices,
        "shuffle10": shuffles,
        "randint_seed": 99999,
        "randint_1_100": randint,
    }


def stat_fixture() -> list[dict]:
    cases = [
        {"name": "flat add", "base": 1000, "stat": Stat.HP, "mods": [modifier(Stat.HP, Operation.FLAT_ADD, 500)]},
        {"name": "flat sub", "base": 1000, "stat": Stat.HP, "mods": [modifier(Stat.HP, Operation.FLAT_SUB, 2500)]},
        {"name": "pct add", "base": 1000, "stat": Stat.HP, "mods": [modifier(Stat.HP, Operation.PCT_ADD, 50)]},
        {"name": "pct sub", "base": 1000, "stat": Stat.HP, "mods": [modifier(Stat.HP, Operation.PCT_SUB, 150)]},
        {"name": "multiply", "base": 1000, "stat": Stat.HP, "mods": [modifier(Stat.HP, Operation.MULTIPLY, 1500)]},
        {"name": "speed cap", "base": 100000, "stat": Stat.Speed, "mods": [modifier(Stat.Speed, Operation.PCT_ADD, 125)]},
        {"name": "speed floor", "base": 100000, "stat": Stat.Speed, "mods": [modifier(Stat.Speed, Operation.PCT_SUB, 100)]},
        {"name": "negative floor division", "base": 1000, "stat": Stat.HP, "mods": [modifier(Stat.HP, Operation.FLAT_SUB, 2500), modifier(Stat.HP, Operation.PCT_ADD, 50)]},
    ]
    while len(cases) < 22:
        i = len(cases)
        stat = [Stat.HP, Stat.Power, Stat.Speed, Stat.Defense, Stat.Energy][i % 5]
        cases.append({
            "name": f"generated {i}",
            "base": (i + 1) * 1000,
            "stat": stat,
            "mods": [
                modifier(stat, Operation.FLAT_ADD if i % 2 else Operation.FLAT_SUB, (i % 7 + 1) * 100),
                modifier(stat, Operation.PCT_ADD if i % 3 else Operation.PCT_SUB, i % 80),
            ],
        })
    result = []
    for case in cases:
        mods = case["mods"]
        result.append({
            "name": case["name"],
            "base": case["base"],
            "stat": case["stat"].value,
            "modifiers": [m.model_dump(mode="json") for m in mods],
            "result": calculate_stat(case["base"], mods, case["stat"]),
        })
    return result


def combat_fixture(game_data) -> dict:
    character = game_data.characters[0]
    enemy_data = game_data.enemies_by_id["scavenger_patrol"]
    party = [character_to_combat_entity(character, [], [])]
    enemies = [enemy_data_to_combat_entity(enemy_data, 1)]
    party[0].card_pool = ["arcane_strike_01"]
    enemies[0].card_pool = ["guard_up_01"]
    result = resolve_combat(party, enemies, game_data.cards_by_id, rng=random.Random(42))
    return {
        "player_won": result.player_won,
        "turns_taken": result.turns_taken,
        "final_hp": result.final_hp,
        "survivors": result.survivors,
    }


def campaign_fixture(game_data) -> dict:
    result = run_campaign(42, game_data, AggressiveAI())
    return {
        "seed": result.seed,
        "victory": result.victory,
        "regions_cleared": result.regions_cleared,
        "total_turns": result.total_turns,
        "region_order": result.region_order,
        "region_difficulties": result.region_difficulties,
        "world_cards_accepted_ids": result.world_cards_accepted_ids,
        "world_cards_skipped_ids": result.world_cards_skipped_ids,
        "upgrade_branches_chosen": result.upgrade_branches_chosen,
        "starting_roster_ids": result.starting_roster_ids,
        "drafted_character_ids": result.drafted_character_ids,
        "card_pool_ids": result.card_pool_ids,
    }


def main() -> int:
    if platform.python_version_tuple()[0:2] != ("3", "12"):
        raise SystemExit(f"Python 3.12.x required, got {platform.python_version()}")
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    game_data = load_game_data(ROOT / "data", ROOT / "mods" / "default" / "flavor")
    dump(FIXTURE_DIR / "rng_sequence.json", rng_fixture())
    dump(FIXTURE_DIR / "stat_calculations.json", stat_fixture())
    dump(FIXTURE_DIR / "combat_seed_42.json", combat_fixture(game_data))
    dump(FIXTURE_DIR / "campaign_seed_42.json", campaign_fixture(game_data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
