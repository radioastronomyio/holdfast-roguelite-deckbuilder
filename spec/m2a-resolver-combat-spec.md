# M2a: Resolver Engine & Combat System

**Status:** Spec
**Date:** 2026-03-15
**Context:** Builds the simulation engine on top of M1 data schemas. All Pydantic models, JSON data files, and 95 tests exist and pass. This milestone creates the resolver that makes the data do something.

---

## Overview

Three modules delivering the core game loop: stat resolution, turn ordering, and encounter execution. Plus a minimal enemy AI and handlers for 3 special-tagged world deck cards. All code lands in `simulation/`. All tests run via `pytest simulation/tests/ -v` from repo root.

---

## Existing Codebase (Do Not Modify)

Read these before writing any code:

| File | Contains |
|------|----------|
| `simulation/models/enums.py` | `Stat`, `Operation`, `Target`, `Stacking`, `AiHeuristic`, `NarrativePosition`, `EncounterType` |
| `simulation/models/modifier.py` | `Modifier` model, `STAT_SCALE = 1000` |
| `simulation/models/card.py` | `Card`, `UpgradeEntry`, `UpgradeTree` |
| `simulation/models/entity.py` | `Character`, `Enemy`, `CharacterGenerationBounds` |
| `simulation/models/campaign.py` | `Region`, `CombatEncounter`, `HazardEncounter`, `EventEncounter`, `Encounter`, `WorldCard`, `OutpostUpgrade`, `EventChoice` |
| `data/cards/base-cards.json` | 15 base cards with effects as modifier tuples |
| `data/cards/upgrade-trees.json` | Per-card upgrade trees (tiers 1-3, 2 branches per tier) |
| `data/entities/example-enemies.json` | 3 enemies with card_pool references |
| `data/campaign/world-deck.json` | 20 world deck cards, 3 with `resolver_special` tags |
| `pyproject.toml` | `pythonpath = ["simulation"]`, `testpaths = ["simulation/tests"]` |

Import pattern: `from models.modifier import Modifier, STAT_SCALE`

---

## Design Constraints (Non-Negotiable)

These are settled architecture decisions. Do not re-litigate or propose alternatives.

1. **Integer-only arithmetic.** `STAT_SCALE = 1000`. All base stats are pre-scaled (a display value of 140 HP is stored as `140000`). All math uses `//` (integer floor division). No floats anywhere in game math.

2. **Resolution order is fixed:** `(base + flat_sum) * (100 + pct_sum) // 100`, then sequential MULTIPLY. This is the `calculate_stat()` formula. MULTIPLY values in data are stored at display scale (e.g., `1.5×` is stored as `value: 1500` in the modifier with operation MULTIPLY). Apply as: `result = result * value // 1000`.

3. **CT turn order is a priority queue**, not a tick simulation. Each entity has a CT accumulator. Each "tick," add current Speed to CT. When CT ≥ 100000 (100 × STAT_SCALE), entity acts. After acting, subtract 100000 from CT. Tie-break: highest CT overflow first.

4. **200-turn combat cap.** If combat exceeds 200 total turns (across all entities), force-end with a loss. This is a Monte Carlo safety valve.

5. **Minimal greedy enemy AI for M2a.** Enemies pick the card from their pool that deals the most damage to the lowest-HP player character. No combo awareness, no defensive play, no target prioritization beyond lowest HP. Real heuristics are M2b scope.

6. **Flat dispatch dict for resolver_special handlers.** A simple `dict[str, Callable]` mapping tag strings to handler functions. No plugin architecture, no registry pattern, no dynamic loading.

7. **Pure functions.** The resolver engine must be deterministic with no side effects. Given identical inputs, it produces identical outputs. No randomness inside the resolver — all RNG happens in the campaign layer (M2b scope) before the resolver is called.

8. **Stacking rules from Modifier.stacking field:** `stack` = accumulate (multiple instances sum), `replace` = newest replaces oldest of same stat+operation, `max` = keep highest value only.

---

## Deliverable 1: Stat Resolver (`simulation/engine/stats.py`)

### Outcome

A `calculate_stat()` function that takes a base value and a list of active modifiers for a single stat, and returns the resolved integer value.

### Signature

```python
def calculate_stat(base: int, modifiers: list[Modifier]) -> int:
    """
    Resolve a single stat value from base + active modifiers.
    
    All values are STAT_SCALE integers. Returns STAT_SCALE integer.
    Resolution: base → flat mods → percentage mods → multiplicative mods.
    """
```

### Resolution Steps

1. Filter modifiers to only those matching the target stat
2. Apply stacking rules to collapse the modifier list (stack/replace/max)
3. Sum all FLAT_ADD values, sum all FLAT_SUB values → `flat_sum = flat_adds - flat_subs`
4. Sum all PCT_ADD values, sum all PCT_SUB values → `pct_sum = pct_adds - pct_subs` (these are whole-number percentages, e.g., 30 means 30%)
5. Apply: `result = (base + flat_sum) * (100 + pct_sum) // 100`
6. For each MULTIPLY modifier in order: `result = result * value // 1000` (value is at 1000× scale, so 1.5× = 1500)
7. Floor at 0 for all stats except HP (HP can be negative to signal death)
8. Return result

### Supporting Function

```python
def apply_stacking(modifiers: list[Modifier]) -> list[Modifier]:
    """
    Collapse a modifier list according to stacking rules.
    Group by (stat, operation). Within each group:
    - 'stack': keep all
    - 'replace': keep only the most recently added (last in list)
    - 'max': keep only the highest value
    """
```

### Tests (`simulation/tests/test_stats.py`)

| Test | Input | Expected |
|------|-------|----------|
| Base only, no mods | `base=100000, mods=[]` | `100000` |
| Single FLAT_ADD | `base=100000, mods=[FLAT_ADD 20000]` | `120000` |
| Single PCT_ADD | `base=100000, mods=[PCT_ADD 50]` | `150000` |
| FLAT then PCT | `base=100000, mods=[FLAT_ADD 20000, PCT_ADD 50]` | `180000` |
| Zero base + PCT | `base=0, mods=[PCT_ADD 50]` | `0` |
| FLAT + PCT + MULTIPLY | `base=100000, mods=[FLAT_ADD 10000, PCT_ADD 20, MULTIPLY 1500]` | `198000` |
| FLAT_SUB | `base=100000, mods=[FLAT_SUB 30000]` | `70000` |
| PCT_SUB | `base=100000, mods=[PCT_SUB 25]` | `75000` |
| Floor at 0 (Defense) | `base=10000, mods=[FLAT_SUB 50000]` | `0` |
| HP goes negative | `base=10000, mods=[FLAT_SUB 50000]`, stat=HP | `-40000` |
| Stacking: replace | Two FLAT_ADD replace mods, same stat | Only last one applies |
| Stacking: stack | Two FLAT_ADD stack mods, same stat | Both sum |
| Stacking: max | Two FLAT_ADD max mods, values 10000 and 20000 | 20000 applies |
| Multiple MULTIPLY | `base=100000, mods=[MULTIPLY 1500, MULTIPLY 2000]` | `300000` (100000 × 1.5 × 2.0) |
| Mixed operations + stacking | Combine all operation types with various stacking rules | Verify full pipeline |

---

## Deliverable 2: CT Turn Order (`simulation/engine/turn_order.py`)

### Outcome

A turn order system that determines which entity acts next based on Speed stats, using a CT (Charge Time) accumulator.

### Core Types

```python
@dataclass
class CombatEntity:
    """Runtime combat state for a character or enemy."""
    id: str
    name: str
    base_stats: dict[Stat, int]          # Pre-scaled base stats
    active_modifiers: list[Modifier]      # Currently active modifiers
    ct: int = 0                           # Charge Time accumulator
    is_player: bool = True
    card_pool: list[str] = field(default_factory=list)  # Card IDs (enemies only)
    ai_heuristic: AiHeuristic | None = None              # Enemies only
    is_alive: bool = True

def get_current_stat(entity: CombatEntity, stat: Stat) -> int:
    """Calculate current value of a stat using calculate_stat()."""

def tick_until_next_turn(entities: list[CombatEntity]) -> CombatEntity:
    """
    Advance CT for all living entities until one reaches threshold.
    Returns the entity that acts next.
    Tie-break: highest CT overflow. Secondary tie-break: Speed. Tertiary: list position.
    """

def process_turn_start(entity: CombatEntity) -> list[str]:
    """
    Called when entity's turn begins:
    1. Tick down durations on active_modifiers (decrement >0 durations)
    2. Remove expired modifiers (duration reached 0)
    3. Apply DoT/HoT from instant-effect modifiers (duration 0 means apply-and-discard)
    4. Refresh Energy to calculated base (not carried over)
    5. Return list of log messages describing what happened
    """
```

### Tests (`simulation/tests/test_turn_order.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Faster entity goes first | Entity A: Speed 120000, Entity B: Speed 80000 | A acts first |
| Speed ratio determines frequency | A: Speed 150000, B: Speed 50000 | A gets ~3 turns per B turn over 10 cycles |
| CT tie-break by overflow | A and B both cross threshold same tick | Higher overflow acts first |
| Dead entities skip | Kill entity A | A never gets another turn |
| Speed buff changes turn frequency | Entity gets PCT_ADD Speed 50 modifier | Turn frequency increases |
| Modifier duration ticking | 3-turn modifier | Gone after 3 of that entity's turns |
| Permanent modifier persists | Duration -1 modifier | Still active after 10 turns |
| Energy refreshes each turn | Entity with base Energy 3000 | Energy recalculated fresh each turn start |
| DoT damage applies at turn start | FLAT_SUB HP duration 3 | HP reduced at start of each of affected entity's turns |
| Entity dies from DoT | HP low enough that DoT kills | Entity marked dead, turn skipped |

---

## Deliverable 3: Encounter Resolution (`simulation/engine/encounters.py`)

### Outcome

Functions that execute each encounter type from start to finish, returning a result object.

### Combat Resolution

```python
@dataclass
class CombatResult:
    player_won: bool
    turns_taken: int
    survivors: list[str]           # IDs of surviving player entities
    combat_log: list[str]          # Human-readable log entries
    final_state: list[CombatEntity]  # Final state of all entities

def resolve_combat(
    party: list[CombatEntity],
    enemies: list[CombatEntity],
    region_modifiers: list[Modifier] | None = None,
    world_modifiers: list[Modifier] | None = None,
) -> CombatResult:
    """
    Execute a full combat encounter.
    
    1. Apply region_modifiers and world_modifiers to all entities
    2. Loop: tick_until_next_turn → entity acts → check win/loss
    3. Player turn: pick card (in sim, use placeholder strategy — lowest cost card targeting lowest HP enemy)
    4. Enemy turn: greedy AI (see enemy_ai.py)
    5. Win: all enemies dead. Loss: all party dead OR 200-turn cap exceeded.
    """
```

### Card Play Resolution

```python
def play_card(
    card: Card,
    caster: CombatEntity,
    targets: list[CombatEntity],
    all_entities: list[CombatEntity],
) -> list[str]:
    """
    Resolve a card being played.
    
    1. Deduct energy_cost from caster's current Energy
    2. For each effect in card.effects:
       a. Resolve target selection based on effect.target
       b. For damage effects (FLAT_SUB on HP): add caster's Power to value
       c. Apply modifier to target(s) — if duration 0, apply instantly and discard
       d. If duration > 0 or -1, add to target's active_modifiers
    3. Apply stacking rules when adding modifiers
    4. Return log messages
    """
```

### Hazard Resolution

```python
@dataclass
class HazardResult:
    survived: bool
    damage_taken: dict[str, int]    # entity_id → total HP lost
    combat_log: list[str]
    final_state: list[CombatEntity]

def resolve_hazard(
    party: list[CombatEntity],
    hazard_modifiers: list[Modifier],
    hazard_duration: int,
    region_modifiers: list[Modifier] | None = None,
    world_modifiers: list[Modifier] | None = None,
) -> HazardResult:
    """
    Execute a hazard encounter.
    
    One-sided: hazard applies modifiers each turn for hazard_duration turns.
    Party can play mitigation cards (in sim, placeholder: play highest-defense card each turn).
    No enemy HP to deplete — survive and move on.
    Survived = at least 1 party member alive at end.
    """
```

### Event Resolution

```python
@dataclass
class EventResult:
    choice_index: int
    effects_applied: list[Modifier]
    costs_applied: list[Modifier]
    combat_log: list[str]
    final_state: list[CombatEntity]

def resolve_event(
    party: list[CombatEntity],
    choices: list[EventChoice],
    choice_index: int,
    region_modifiers: list[Modifier] | None = None,
    world_modifiers: list[Modifier] | None = None,
) -> EventResult:
    """
    Execute an event encounter.
    
    Apply the selected choice's effects and costs to the party.
    No combat loop — immediate resolution.
    """
```

### Tests (`simulation/tests/test_encounters.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Combat: party wins | 3 strong characters vs 1 weak enemy | `player_won=True`, enemy dead |
| Combat: party loses | 1 weak character vs 3 strong enemies | `player_won=False`, all party dead |
| Combat: 200-turn cap | Two defensive entities that can't kill each other | `player_won=False`, `turns_taken=200` |
| Combat: Power adds to damage | Character Power=10000, card FLAT_SUB HP 5000 | Actual damage = 15000 (before Defense) |
| Combat: Defense mitigates | Enemy HP FLAT_SUB 20000 vs target Defense 8000 | Actual HP loss = 12000 |
| Combat: region modifier applies | Region: all enemies +PCT_ADD Defense 15 | Enemy defense is 15% higher throughout |
| Card: energy cost deducted | Card costs 2000 Energy, entity has 5000 | Entity Energy becomes 3000 after play |
| Card: insufficient energy | Card costs 5000, entity has 3000 | Card cannot be played |
| Card: AoE targeting | Card target=ENEMY_ALL, 3 enemies alive | All 3 take damage |
| Card: DoT applied | FLAT_SUB HP duration 3 | Modifier added to target's active list |
| Hazard: survive | Party HP high enough | `survived=True` |
| Hazard: party wipe | Hazard too strong | `survived=False` |
| Event: choice applied | Select choice 0 | Effects and costs from choice 0 applied |
| Stacking in combat | Two replace-type Defense buffs on same target | Only most recent active |

---

## Deliverable 4: Enemy AI (`simulation/engine/enemy_ai.py`)

### Outcome

Minimal greedy AI that picks a valid card for enemies to play on their turn.

```python
def pick_enemy_action(
    enemy: CombatEntity,
    available_cards: list[Card],
    party: list[CombatEntity],
) -> tuple[Card, list[CombatEntity]] | None:
    """
    Greedy enemy AI (M2a — minimal viable).
    
    1. Filter cards to those the enemy can afford (energy_cost <= current Energy)
    2. Score each card: sum of FLAT_SUB HP values in effects (raw damage potential)
    3. Pick highest-scoring card
    4. Target: lowest-HP living party member (for single-target), all (for AoE)
    5. Return (card, targets) or None if no affordable card
    """
```

### Tests (`simulation/tests/test_enemy_ai.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Picks highest damage card | 3 cards with different damage values | Returns highest damage card |
| Respects energy budget | Best card costs 5, enemy has 3 Energy | Picks affordable card |
| Targets lowest HP | 3 party members at different HP | Target is lowest HP |
| No valid card returns None | All cards too expensive | Returns None |
| AoE card targets all | Card target=ENEMY_ALL | All living party members in target list |

---

## Deliverable 5: Resolver Special Handlers (`simulation/engine/special_handlers.py`)

### Outcome

Handlers for the 3 `resolver_special` tagged world deck cards. Dispatched via flat dict lookup.

### The 3 Tags

**`no_refresh_turn_2`** (Overclocked)
- GDD: "Energy does not refresh Turn 2"
- Implementation: On turn 2 of the encounter, skip the Energy refresh step for affected entities. The modifier already has `FLAT_SUB Energy 999000 duration 2` which effectively zeros Energy, but the handler must also suppress the normal Energy refresh at turn start. After duration expires, normal refresh resumes.

**`status_duration_multiply_2`** (Hyper-Metabolism)
- GDD: "Status effect duration ×2"
- Implementation: When a new modifier is applied to an entity that has this tag active, double the incoming modifier's duration (if duration > 0). Duration -1 (permanent) and 0 (instant) are unaffected.

**`delayed_start_turn_2`** (Temporal Shift)
- GDD: "+100% Speed Turn 1, -50% Speed Turns 2-4"
- Implementation: The -50% Speed modifier should not apply on Turn 1. The handler delays activation of the downside modifier until Turn 2 of the encounter. The upside (+100% Speed Turn 1) is a normal duration-1 modifier and needs no special handling.

### Dispatch

```python
SPECIAL_HANDLERS: dict[str, Callable] = {
    "no_refresh_turn_2": handle_no_refresh,
    "status_duration_multiply_2": handle_duration_multiply,
    "delayed_start_turn_2": handle_delayed_start,
}

def check_special_tags(modifier: Modifier) -> str | None:
    """Return the first resolver_special-associated tag found, or None."""

def apply_special_handler(tag: str, context: SpecialHandlerContext) -> None:
    """Look up and call the handler for a given tag."""
```

### Tests (`simulation/tests/test_special_handlers.py`)

| Test | Setup | Expected |
|------|-------|----------|
| no_refresh: turn 1 refreshes | Entity with tag, turn 1 | Energy refreshes normally |
| no_refresh: turn 2 suppressed | Entity with tag, turn 2 | Energy stays at 0 |
| no_refresh: turn 3 resumes | Entity with tag, turn 3 | Energy refreshes normally |
| duration_multiply: doubles duration 3 | Incoming modifier dur=3, entity has tag | Applied with dur=6 |
| duration_multiply: ignores permanent | Incoming modifier dur=-1, entity has tag | Applied with dur=-1 |
| duration_multiply: ignores instant | Incoming modifier dur=0, entity has tag | Applied with dur=0 |
| delayed_start: turn 1 no downside | Entity with tag, turn 1 | Speed debuff not active |
| delayed_start: turn 2 active | Entity with tag, turn 2 | Speed debuff applies |
| dispatch: unknown tag ignored | Tag "nonexistent_tag" | No error, no effect |
| dispatch: correct handler called | Tag "no_refresh_turn_2" | `handle_no_refresh` called |

---

## File Structure

All new files go under `simulation/engine/`. Create the directory and `__init__.py`.

```
simulation/
  engine/
    __init__.py
    stats.py              ← calculate_stat(), apply_stacking()
    turn_order.py          ← CombatEntity, tick_until_next_turn(), process_turn_start()
    encounters.py          ← resolve_combat(), resolve_hazard(), resolve_event(), play_card()
    enemy_ai.py            ← pick_enemy_action()
    special_handlers.py    ← SPECIAL_HANDLERS dict, 3 handler functions
  models/                  ← EXISTS, do not modify
  tests/
    test_stats.py          ← NEW
    test_turn_order.py     ← NEW
    test_encounters.py     ← NEW
    test_enemy_ai.py       ← NEW
    test_special_handlers.py ← NEW
```

Imports from models use: `from models.modifier import Modifier, STAT_SCALE`
Imports within engine use: `from engine.stats import calculate_stat`

---

## Completion Criteria

1. `pytest simulation/tests/ -v` passes — ALL tests (M1 existing + M2a new)
2. `calculate_stat()` produces correct results for all test vectors above
3. A combat encounter between GDD example characters and enemies resolves to completion
4. 200-turn cap terminates infinite loops with a loss
5. All 3 resolver_special handlers produce correct behavior per test cases
6. No floats in any game math — integer arithmetic only
7. Zero modification to any existing M1 files (models, data, existing tests)

---

## What This Spec Does NOT Cover

- Campaign loop (region selection, world phase, draft) — M2b
- Real enemy AI heuristics (defensive play, combo awareness) — M2b
- Procedural generation of characters, regions, encounters — M2b
- Player AI for simulation (currently uses placeholder: lowest-cost-card strategy) — M2b
- Frontend/React — M4
- Balance tuning — M3