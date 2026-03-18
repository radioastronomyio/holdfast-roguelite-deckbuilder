# M2b: Procedural Generation

**Status:** Spec
**Date:** 2026-03-17
**Depends on:** M2a (Resolver Engine & Combat System — complete, 192 tests passing)
**Context:** With the resolver engine working, we need procedurally generated content to feed into it. This milestone creates generators for characters, enemies, regions, and encounters — all pure functions taking an RNG seed and returning Pydantic model instances.

---

## Overview

Four generator modules producing game content from existing data pools and configuration. All generators are pure functions: given a seed and parameters, they produce deterministic output. No campaign state awareness — generators don't know what turn it is or what's been conquered. They answer: "give me a character/region/enemy/encounter at difficulty X with seed Y."

All new code lands in `simulation/generation/`. All tests run via `pytest simulation/tests/ -v` from repo root.

---

## Existing Codebase (Reference — Do Not Modify)

| File | Contains |
|------|----------|
| `simulation/models/entity.py` | `Character`, `Enemy`, `CharacterGenerationBounds` |
| `simulation/models/campaign.py` | `Region`, `CombatEncounter`, `HazardEncounter`, `EventEncounter`, `EventChoice`, `ResearchLayer`, `WorldCard` |
| `simulation/models/modifier.py` | `Modifier`, `STAT_SCALE = 1000` |
| `simulation/models/flavor.py` | `EpithetCondition1`, `EpithetCondition2`, `EpithetEntry`, `ElementStatMap`, `FlavorPools` |
| `simulation/models/enums.py` | `Stat`, `Operation`, `Target`, `Stacking`, `AiHeuristic`, `NarrativePosition`, `EncounterType` |
| `simulation/models/card.py` | `Card` |
| `data/entities/generation-bounds.json` | Per-stat min/max and total budget (display-scale values, NOT pre-scaled) |
| `data/entities/example-enemies.json` | 4 example enemies with card_pool references |
| `data/cards/base-cards.json` | 15 base cards with effects |
| `data/cards/hazard-cards.json` | Hazard cards |
| `mods/default/flavor/given_names.json` | 60+ first names |
| `mods/default/flavor/archetypes.json` | 20+ archetype labels |
| `mods/default/flavor/action_verbs.json` | 30+ action words |
| `mods/default/flavor/region_adjectives.json` | 30+ adjectives |
| `mods/default/flavor/region_nouns.json` | 30+ nouns |
| `mods/default/flavor/element-stat-map.json` | Stat → element pools (default/rare) |
| `mods/default/flavor/epithet-conditions.json` | 20+ epithet conditions |

Import pattern: `from models.entity import Character, Enemy, CharacterGenerationBounds`

---

## Design Constraints (Non-Negotiable)

1. **All generators are pure functions.** Given identical seed + parameters, output is identical. Use `random.Random(seed)` instances, never the global `random` module.

2. **STAT_SCALE = 1000.** Generation bounds are at display scale (HP min: 50 means 50, not 50000). Generators produce stats at display scale internally, then multiply by `STAT_SCALE` before constructing model instances. The Character model expects pre-scaled `base_stats` (e.g., HP 140 → stored as 140000).

3. **Generators consume data from `mods/default/flavor/` and `data/`.** They do NOT hardcode card names, enemy stats, or flavor text. Everything comes from pool files. This preserves mod-readiness.

4. **Narrative arc rules are fixed.** Per GDD:
   - Approach (position 1): 60% hazard, 40% event. Never combat.
   - Settlement (position 2): 70% combat, 30% event.
   - Stronghold (position 3): 100% elite combat. Always.

5. **No campaign logic in generators.** Generators don't know about conquered regions, roster state, or world phase. They take explicit parameters (difficulty level, available card pool) and return model instances.

6. **Epithet condition evaluation uses display-scale stats.** The epithet-conditions.json values (e.g., "power >= 70") are compared against display-scale stat values (not STAT_SCALE values). Evaluate before scaling.

---

## Deliverable 1: Character Generator (`simulation/generation/characters.py`)

### Outcome

Generate procedural characters with randomized stats, names, innate passives, and epithets.

### Data Loading

```python
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
```

### Character Generation

```python
def generate_character(
    rng: random.Random,
    bounds: CharacterGenerationBounds,
    flavor: FlavorData,
) -> Character:
    """
    Generate a procedural character.

    1. Allocate stats within bounds:
       a. Start each stat at its per_stat_min
       b. Calculate remaining budget (total_budget random between min/max minus sum of mins)
       c. Distribute remaining budget randomly across stats, respecting per_stat_max
    2. Evaluate epithet conditions against display-scale stats
    3. Select innate passive based on character's highest stat:
       a. Find the character's highest stat (break ties randomly)
       b. Look up that stat in element_stat_map
       c. 80% chance: pick from default pool, 20% from rare pool
       d. Create a permanent PCT_ADD modifier for that stat (value 10-25, random)
    4. Assemble name: "{first_name}, {epithet} {archetype} from the {region_noun}"
       - If no epithet qualifies, omit the epithet segment
    5. Multiply all stat values by STAT_SCALE to produce base_stats dict
    6. Return Character model instance
    """
```

### Epithet Evaluation

```python
def evaluate_epithet(
    stats: dict[Stat, int],  # display-scale stats
    condition: EpithetEntry,
) -> bool:
    """
    Evaluate whether a character's stats satisfy an epithet's conditions.
    Type 1: single stat threshold (stat op value)
    Type 2: dual stat with AND/OR/XOR logic
    """
```

### Tests (`simulation/tests/test_generation_characters.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Stats within bounds | Generate 100 characters | All stats within per_stat_min/max, total within budget |
| Stats pre-scaled | Generate character | All base_stats values are display_value × STAT_SCALE |
| Deterministic with same seed | Generate twice with seed=42 | Identical characters |
| Different seeds produce different characters | seed=42 vs seed=99 | Different stats |
| Name contains first_name | Generate character | name_parts["first_name"] is from given_names pool |
| Name contains archetype | Generate character | name_parts["title"] is from archetypes pool |
| Innate passive is permanent | Generate character | innate_passive.duration == -1 |
| Innate passive targets SELF | Generate character | innate_passive.target == SELF |
| Epithet type 1 evaluation | stats={Power: 80}, condition "power >= 70" | True |
| Epithet type 1 negative | stats={Power: 50}, condition "power >= 70" | False |
| Epithet type 2 AND | stats meeting both conditions | True |
| Epithet type 2 XOR | stats meeting exactly one | True |
| Epithet type 2 XOR both | stats meeting both | False |
| Character has valid ID | Generate character | id is non-empty, lowercase, underscore-separated |

---

## Deliverable 2: Enemy Generator (`simulation/generation/enemies.py`)

### Outcome

Generate enemies with stats scaled to difficulty level, card pools selected from available cards.

```python
def generate_enemy(
    rng: random.Random,
    difficulty: int,           # 1-6 (region number)
    available_card_ids: list[str],
    is_elite: bool = False,
    flavor: FlavorData | None = None,
) -> Enemy:
    """
    Generate a procedural enemy.

    1. Base stat budget = 150 + (difficulty * 30). Elite: multiply budget by 1.5.
    2. Distribute budget across 5 stats with role variance:
       - rng selects a role bias: aggressive (high Power/Speed), defensive (high HP/Defense), balanced
       - Allocate proportionally to role weights
    3. Card pool: select 2-4 cards randomly from available_card_ids
       - Elite enemies get 3-5 cards
    4. ai_heuristic_tag matches role bias
    5. Multiply all stat values by STAT_SCALE
    6. Generate name from flavor pools (or default "{adjective} {noun}" pattern)
    7. Return Enemy model instance
    """
```

### Tests (`simulation/tests/test_generation_enemies.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Higher difficulty = higher stats | difficulty=1 vs difficulty=6 | difficulty=6 has higher total stats |
| Elite enemies are stronger | is_elite=True vs False, same difficulty | Elite has higher total stats |
| Card pool from available cards | available_card_ids=["a","b","c"] | Enemy card_pool is subset |
| Card pool non-empty | Any generation | len(card_pool) >= 2 |
| Deterministic with same seed | Same seed + params | Identical enemies |
| Valid ai_heuristic_tag | Generate enemy | Tag is one of aggressive/defensive/balanced |
| Stats pre-scaled | Generate enemy | All base_stats values are multiples of STAT_SCALE |
| Elite flag set correctly | is_elite=True | enemy.is_elite is True |

---

## Deliverable 3: Region Generator (`simulation/generation/regions.py`)

### Outcome

Generate a complete Region with 3 encounters following the narrative arc, modifier stacks, meta-reward, and research layers.

```python
def generate_region(
    rng: random.Random,
    difficulty: int,              # 1-6 (order in campaign)
    available_card_ids: list[str],
    flavor: FlavorData,
) -> Region:
    """
    Generate a procedural region.

    1. Name: "{adjective} {noun}" from flavor pools (e.g., "Ashen Wastes")
    2. Region type: the adjective becomes region_type
    3. Modifier stack: 1-3 permanent modifiers active during all region encounters
       - Scaled to difficulty: higher difficulty = stronger/more modifiers
       - Stats affected chosen randomly, operations from PCT_ADD/PCT_SUB/FLAT_ADD/FLAT_SUB
       - Values: base 5-15 for PCT, 2000-8000 (STAT_SCALE) for FLAT, scaled by difficulty
       - Target: ALLY_ALL or ENEMY_ALL (affects party or enemies throughout region)
    4. Generate 3 encounters via generate_encounter() (see Deliverable 4):
       - Position 0 (approach): hazard or event per GDD weights
       - Position 1 (settlement): combat or event per GDD weights
       - Position 2 (stronghold): always elite combat
    5. Meta-reward: one permanent modifier granted on conquest
       - Stat chosen randomly, operation FLAT_ADD or PCT_ADD
       - Value: modest but meaningful (FLAT_ADD 1000-3000 at STAT_SCALE, PCT_ADD 5-15)
       - duration=-1, target=SELF (applied to each participant individually)
    6. Research layers: fixed structure, costs scaled by difficulty
       - Level 1: reveal_type="region_type", cost=10×difficulty
       - Level 2: reveal_type="primary_modifier", cost=25×difficulty
       - Level 3: reveal_type="encounter_details", cost=50×difficulty
       - Level 4: reveal_type="boss_mechanics", cost=100×difficulty
    7. Return Region model instance
    """
```

### Tests (`simulation/tests/test_generation_regions.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Exactly 3 encounters | Generate region | len(region.encounters) == 3 |
| Narrative arc order | Generate region | approach → settlement → stronghold |
| Stronghold is combat | Generate region | encounters[2].type == "combat" |
| Stronghold is elite | Generate 20 regions | All stronghold encounters reference at least one elite enemy |
| Approach never combat | Generate 100 regions | No approach encounter has type "combat" |
| Modifier stack scales with difficulty | difficulty=1 vs difficulty=6 | difficulty=6 has stronger/more modifiers |
| Meta-reward is permanent | Generate region | meta_reward.duration == -1 |
| Research layers = 4 | Generate region | len(research_layers) == 4 |
| Research costs scale | difficulty=1 vs difficulty=6 | difficulty=6 costs are higher |
| Deterministic with same seed | Same seed + params | Identical regions |
| Name from flavor pools | Generate region | Name contains words from adjective/noun pools |

---

## Deliverable 4: Encounter Generator (`simulation/generation/encounters.py`)

### Outcome

Generate individual encounters based on narrative position and difficulty.

```python
def generate_encounter(
    rng: random.Random,
    position: NarrativePosition,
    difficulty: int,
    available_card_ids: list[str],
    flavor: FlavorData,
) -> Encounter:
    """
    Generate a single encounter based on narrative position.

    Approach (position 0):
      - 60% hazard, 40% event (rng roll)
      - Hazard: 1-3 hazard modifiers (FLAT_SUB HP, PCT_SUB Speed/Defense), duration 2-5
      - Event: 2-3 choices, each with effects + costs as modifier arrays

    Settlement (position 1):
      - 70% combat, 30% event
      - Combat: 1-3 non-elite enemies generated via generate_enemy()
      - Event: same generation as approach events but harder trade-offs

    Stronghold (position 2):
      - 100% combat
      - 1 elite enemy + 0-2 non-elite adds, all generated via generate_enemy()

    All encounters get:
      - name: generated from flavor pools
      - description: template-based ("A {adjective} {noun} blocks the path...")
      - narrative_position: from input
    """
```

### Event Generation Helper

```python
def generate_event_choices(
    rng: random.Random,
    difficulty: int,
    num_choices: int = 2,
) -> list[EventChoice]:
    """
    Generate trade-off event choices.
    Each choice has effects (upside modifiers) and cost (downside modifiers).
    Neither upside nor downside should be empty — every choice is a trade-off.
    Higher difficulty = larger values on both sides.
    """
```

### Tests (`simulation/tests/test_generation_encounters.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Approach: hazard or event | Generate 100 approach encounters | ~60% hazard, ~40% event (within ±15%) |
| Approach: never combat | Generate 100 approach encounters | Zero combat encounters |
| Settlement: combat or event | Generate 100 settlement encounters | ~70% combat, ~30% event (within ±15%) |
| Stronghold: always combat | Generate 100 stronghold encounters | 100% combat |
| Stronghold: has elite enemy | Generate stronghold encounter | At least 1 enemy in encounter is elite |
| Hazard has modifiers | Generate hazard encounter | len(hazard_modifiers) >= 1 |
| Hazard duration positive | Generate hazard encounter | hazard_duration > 0 |
| Event has >= 2 choices | Generate event encounter | len(choices) >= 2 |
| Event choices have effects | Generate event encounter | All choices have non-empty effects |
| Combat has enemies | Generate combat encounter | len(enemies) >= 1 |
| Deterministic with same seed | Same seed + params | Identical encounter |

---

## File Structure

```
simulation/
  generation/
    __init__.py
    characters.py    ← generate_character(), evaluate_epithet(), load_flavor_data()
    enemies.py       ← generate_enemy()
    regions.py       ← generate_region()
    encounters.py    ← generate_encounter(), generate_event_choices()
  tests/
    test_generation_characters.py  ← NEW
    test_generation_enemies.py     ← NEW
    test_generation_regions.py     ← NEW
    test_generation_encounters.py  ← NEW
```

Imports: `from generation.characters import generate_character`
Cross-module: `from generation.enemies import generate_enemy` (used by encounter and region generators)

---

## Completion Criteria

1. `pytest simulation/tests/ -v` passes — ALL tests (M1 + M2a existing + M2b new)
2. 100 generated characters all pass `Character(**data)` validation
3. 100 generated regions all pass `Region(**data)` validation with correct narrative arc
4. Approach encounter never produces combat type across 100 generations
5. Stronghold encounter always produces elite combat across 100 generations
6. Same seed produces identical output across 50 runs
7. No floats in any generated stat values — integer arithmetic only
8. Zero modification to any existing files (models, engine, data, existing tests)
9. All generators load from `mods/default/flavor/` and `data/` — no hardcoded content

---

## What This Spec Does NOT Cover

- Campaign loop (region selection, world phase, draft) — M2c
- Player or enemy AI heuristics — M2d
- Monte Carlo simulation runs — M2d
- Data loading and STAT_SCALE normalization of card effects — M2c
- Frontend/React — future phase
