# M2c: Campaign Loop

**Status:** Spec
**Date:** 2026-03-17
**Depends on:** M2b (Procedural Generation — must be complete before M2c execution)
**Context:** With generators (M2b) and resolvers (M2a) working, this milestone wires them together into a full campaign execution: generate a map, select regions, run encounters, handle world phases, and produce a win/loss result. This is the simulation's spine.

---

## Overview

Three modules: a data loader that normalizes JSON for engine consumption, a campaign state machine, and a campaign runner that executes the full macro loop. The runner produces a `CampaignResult` with enough data for AI heuristics (M2d) to analyze.

All new code lands in `simulation/campaign/`. All tests run via `pytest simulation/tests/ -v` from repo root.

---

## Critical: Card Value Scaling

**This must be understood before implementing anything.**

Card effect values in JSON are at display scale (`"value": 15` for Arcane Strike's FLAT_SUB HP). Entity `base_stats` are at STAT_SCALE (`"HP": 140000` = 140 × 1000). The resolver engine (`calculate_stat`, `play_card`) expects ALL values at STAT_SCALE.

The data loader in this milestone is responsible for scaling card effect values at load time:

- `FLAT_ADD` and `FLAT_SUB` values: multiply by `STAT_SCALE` (15 → 15000)
- `PCT_ADD` and `PCT_SUB` values: do NOT scale (they're whole-number percentages, e.g., 30 means 30%)
- `MULTIPLY` values: do NOT scale (already at 1000× per spec, e.g., 1500 means 1.5×)

This scaling applies to: base card effects, upgrade tree added_effects, hazard card effects, world card upside/downside modifiers, outpost upgrade effects, region modifier stacks, encounter hazard modifiers, and event choice effects/costs.

Entity `base_stats` are already pre-scaled in JSON. Do not double-scale them.

Generation bounds in `generation-bounds.json` are at display scale — the M2b generators handle their own scaling.

---

## Existing Codebase (Reference — Do Not Modify)

| File | Contains |
|------|----------|
| `simulation/engine/encounters.py` | `resolve_combat()`, `resolve_hazard()`, `resolve_event()`, `CombatResult`, `HazardResult`, `EventResult` |
| `simulation/engine/turn_order.py` | `CombatEntity`, `get_current_stat()` |
| `simulation/generation/characters.py` | `generate_character()`, `load_flavor_data()` |
| `simulation/generation/enemies.py` | `generate_enemy()` |
| `simulation/generation/regions.py` | `generate_region()` |
| `simulation/generation/encounters.py` | `generate_encounter()` |
| `simulation/models/campaign.py` | `Region`, `WorldCard`, `OutpostUpgrade`, `EventChoice`, `ResearchLayer` |
| `simulation/models/entity.py` | `Character`, `Enemy`, `CharacterGenerationBounds` |
| `simulation/models/card.py` | `Card`, `UpgradeEntry` |
| `simulation/models/modifier.py` | `Modifier`, `STAT_SCALE` |
| `simulation/models/enums.py` | All enums |
| `data/` | All JSON data files |
| `mods/default/flavor/` | Flavor pools |

---

## Design Constraints (Non-Negotiable)

1. **Seed-based determinism.** A single integer seed determines the entire campaign. Same seed → identical campaign result. Use `random.Random(seed)` exclusively, never global `random`.

2. **Pure function campaign runner.** `run_campaign(seed)` takes a seed, returns a result. No side effects, no file I/O during execution (data loading happens once before the run).

3. **Integer-only arithmetic.** All game math uses `STAT_SCALE` integers. The loader scales values once at load time; after that, everything is integer math.

4. **Placeholder strategies for M2c.** Region selection, world card evaluation, and card upgrade selection use simple placeholder heuristics. Real AI is M2d scope.

5. **Research uses flat economics.** Fixed cost per layer (from ResearchLayer.cost), flat resource income per conquest (50 resources per region cleared). Starting resources: 0. Research is optional — regions can be assaulted without research.

6. **Party size defaults to 3.** Unless an outpost upgrade with `special_effect="party_size+1"` is active, in which case party size is 4.

---

## Deliverable 1: Data Loader (`simulation/campaign/loader.py`)

### Outcome

Load all game data from JSON files and produce a normalized `GameData` container with all values at STAT_SCALE where needed.

```python
@dataclass
class GameData:
    """All game data loaded and normalized for engine consumption."""
    cards_by_id: dict[str, Card]          # base cards + hazard cards, effects scaled
    upgrade_trees: dict[str, dict[str, UpgradeEntry]]  # card_id → branch → entry, effects scaled
    characters: list[Character]            # example characters (for initial roster)
    enemies_by_id: dict[str, Enemy]        # example enemies
    generation_bounds: CharacterGenerationBounds
    regions: list[Region]                  # example regions (effects scaled)
    world_deck: list[WorldCard]            # all 20 cards (effects scaled)
    outpost_upgrades: list[OutpostUpgrade]  # all upgrades (effects scaled)
    flavor: FlavorData                     # from M2b loader

def load_game_data(
    data_path: Path = Path("data"),
    mods_path: Path = Path("mods/default/flavor"),
) -> GameData:
    """
    Load all JSON data files and normalize values.

    Scaling rules applied to every Modifier encountered:
    - FLAT_ADD, FLAT_SUB: value *= STAT_SCALE
    - PCT_ADD, PCT_SUB: no change
    - MULTIPLY: no change

    This applies recursively to: Card.effects, UpgradeEntry.added_effects,
    WorldCard.upside/downside, OutpostUpgrade.effects, Region.modifier_stack,
    HazardEncounter.hazard_modifiers, EventChoice.effects/cost,
    Region.meta_reward.
    """

def scale_modifier(mod: Modifier) -> Modifier:
    """Scale a single modifier's value if it's a FLAT operation."""
```

### Tests (`simulation/tests/test_loader.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Cards loaded and scaled | Load base-cards.json | Arcane Strike FLAT_SUB value = 15 × 1000 = 15000 |
| PCT values not scaled | Load card with PCT_ADD | Value unchanged |
| MULTIPLY values not scaled | Load card with MULTIPLY | Value unchanged |
| All 15 base cards loaded | Load game data | len(cards_by_id) >= 15 |
| World deck loaded and scaled | Load world-deck.json | FLAT values scaled, PCT values unchanged |
| Outpost upgrades scaled | Load outpost-upgrades.json | FLAT effects scaled |
| Region modifiers scaled | Load example-regions.json | Region modifier_stack FLAT values scaled |
| Entity stats NOT double-scaled | Load example-characters.json | HP values match JSON (already pre-scaled) |
| Upgrade tree effects scaled | Load upgrade-trees.json | Added effect FLAT values scaled |
| Round-trip integrity | Load, check card count | All data files loaded without error |

---

## Deliverable 2: Campaign State (`simulation/campaign/state.py`)

### Outcome

A mutable state container tracking all campaign progress.

```python
@dataclass
class RegionState:
    """Tracking state for a single region."""
    region: Region
    conquered: bool = False
    research_level: int = 0       # 0-4 (0 = unrevealed)
    assigned_difficulty: int = 1   # 1-6

@dataclass
class CampaignState:
    """Full mutable campaign state."""
    seed: int
    rng: random.Random
    turn_number: int = 0                # macro turns (region assaults completed)
    resources: int = 0                   # flat resource pool for research
    roster: list[Character] = field(default_factory=list)
    region_states: list[RegionState] = field(default_factory=list)
    skip_tokens: int = 0                 # earned from conquest
    active_world_modifiers: list[Modifier] = field(default_factory=list)
    active_outpost_upgrades: list[OutpostUpgrade] = field(default_factory=list)
    card_upgrades_applied: dict[str, list[str]] = field(default_factory=dict)  # card_id → [branch_keys]
    drafted_characters: list[str] = field(default_factory=list)  # IDs of drafted characters
    game_over: bool = False
    victory: bool = False
    campaign_log: list[str] = field(default_factory=list)

    @property
    def party_size(self) -> int:
        """Base 3, +1 if War Room upgrade active."""
        base = 3
        for upgrade in self.active_outpost_upgrades:
            if upgrade.special_effect == "party_size+1":
                base += 1
        return min(base, len(self.roster))  # can't exceed roster size

    @property
    def conquered_count(self) -> int:
        return sum(1 for rs in self.region_states if rs.conquered)

    @property
    def unconquered_regions(self) -> list[RegionState]:
        return [rs for rs in self.region_states if not rs.conquered]
```

---

## Deliverable 3: Campaign Runner (`simulation/campaign/runner.py`)

### Outcome

Execute a full campaign from seed to result.

```python
@dataclass
class CampaignResult:
    """Output of a complete campaign run."""
    seed: int
    victory: bool
    regions_cleared: int
    total_turns: int                          # sum of all combat turns across encounters
    final_roster: list[Character]
    world_cards_drawn: int
    world_cards_skipped: int
    resources_spent_on_research: int
    campaign_log: list[str]
    encounter_results: list[CombatResult | HazardResult | EventResult]

def run_campaign(seed: int, game_data: GameData) -> CampaignResult:
    """
    Execute one full campaign.

    Macro loop (GDD §Campaign Structure):
    1. INIT:
       a. Create RNG from seed
       b. Generate 6 regions via generate_region() at difficulties 1-6
       c. Start with 1 character from game_data.characters (random selection)
         OR generate 3 characters and pick the best (placeholder: highest total stats)
       d. Reveal 1 random region at research level 1 (free initial intel)
       e. resources = 0, skip_tokens = 0

    2. RESEARCH PHASE (optional, before each assault):
       a. For each unrevealed/partially revealed region:
          Check if resources >= next research layer cost
       b. Placeholder strategy: research the cheapest available layer
       c. Deduct cost from resources
       d. Increment region's research_level

    3. REGION SELECTION:
       a. Placeholder heuristic: pick lowest-difficulty unconquered region
       b. If all regions conquered → victory
       c. Select party: first N characters from roster (N = party_size)

    4. ASSAULT (3 encounters per region):
       a. For each encounter in region.encounters:
          - Convert roster Characters → CombatEntity instances
          - If combat: load enemy data, call resolve_combat()
          - If hazard: call resolve_hazard()
          - If event: call resolve_event() with placeholder choice (index 0)
          - If party wiped → game over (loss)
          - Carry damage/modifier state between encounters within a region
       b. Party state persists across all 3 encounters (HP doesn't reset)

    5. POST-CONQUEST:
       a. Apply meta_reward to all participating characters (add to their base_stats or active modifiers as appropriate)
       b. Mark region as conquered
       c. Earn skip_tokens += 1
       d. Earn resources += 50
       e. Card upgrades: N upgrades where N = party_size
          - Placeholder greedy: for each upgrade slot, find the first available highest-tier upgrade across all cards, apply it
       f. Character draft: generate 3 characters, pick the one with highest total stats
          - Add drafted character to roster

    6. WORLD PHASE (3 rounds after each conquest):
       a. Shuffle world deck (seeded)
       b. Draw 3 cards (or remaining if < 3)
       c. For each drawn card:
          - Placeholder evaluation: accept if net stat impact is positive, skip otherwise
          - If skip_tokens > 0, can skip (decrement skip_tokens)
          - If accepted: apply upside and downside modifiers to all roster characters
       d. Used/skipped cards are removed from the world deck for this campaign

    7. REPEAT from step 2 until victory or game_over

    8. RETURN CampaignResult
    """
```

### Character-to-CombatEntity Conversion

```python
def character_to_combat_entity(
    character: Character,
    active_world_mods: list[Modifier],
    active_outpost_mods: list[Modifier],
) -> CombatEntity:
    """
    Convert a Character model to a CombatEntity for combat resolution.
    - base_stats from character
    - active_modifiers includes: innate_passive + active world mods + active outpost mods
    - card_pool: all base card IDs (shared pool)
    - is_player = True
    """

def enemy_data_to_combat_entity(
    enemy: Enemy,
    region_difficulty: int,
) -> CombatEntity:
    """
    Convert an Enemy model to a CombatEntity for combat resolution.
    - base_stats from enemy (already scaled in JSON)
    - is_player = False
    - card_pool from enemy.card_pool
    - ai_heuristic from enemy.ai_heuristic_tag
    """
```

### Card Upgrade Application

```python
def apply_card_upgrade(
    card: Card,
    branch_key: str,
    upgrade_trees: dict[str, dict[str, UpgradeEntry]],
) -> Card:
    """
    Apply an upgrade branch to a card.
    - Look up the card's upgrade tree
    - Find the branch entry
    - Append added_effects to card.effects
    - Increment upgrade_tier
    - Return new Card instance (don't mutate)
    """

def pick_greedy_upgrade(
    roster_cards: list[str],
    upgrade_trees: dict[str, dict[str, UpgradeEntry]],
    applied_upgrades: dict[str, list[str]],
) -> tuple[str, str] | None:
    """
    Placeholder greedy upgrade selection.
    Find the highest-tier available upgrade across all cards.
    Returns (card_id, branch_key) or None if no upgrades available.
    Respects prerequisites and exclusions.
    """
```

### Tests (`simulation/tests/test_campaign_loop.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Campaign completes | Run with known easy seed | Returns CampaignResult (win or loss, no crash) |
| Deterministic | Run seed=42 twice | Identical CampaignResult |
| Victory path | Run with very strong starting roster | victory=True, regions_cleared=6 |
| Loss path | Run with very weak roster vs hard regions | victory=False |
| Skip tokens increment | Conquer 3 regions | skip_tokens >= 3 |
| Resources increment | Conquer 2 regions | resources >= 100 (50 per conquest) |
| World cards drawn | Complete one world phase | world_cards_drawn >= 1 |
| Character drafted | Complete one conquest | roster size increases by 1 |
| Meta-reward applied | Conquer a region | Participating characters have meta_reward modifier |
| Card upgrade applied | Complete one conquest | card_upgrades_applied is non-empty |
| Party HP carries between encounters | Region with hazard then combat | Combat starts with hazard-reduced HP |
| Region selection works | Multiple unconquered regions | Lowest difficulty selected |
| Research deducts resources | Research a region | resources decreased by layer cost |
| Data loader integration | Load game data, run campaign | No scaling errors (combat damage is reasonable) |
| Entity conversion | Convert Character → CombatEntity | base_stats match, innate_passive in active_modifiers |

---

## File Structure

```
simulation/
  campaign/
    __init__.py
    loader.py        ← load_game_data(), scale_modifier(), GameData
    state.py         ← CampaignState, RegionState
    runner.py        ← run_campaign(), character_to_combat_entity(), apply_card_upgrade()
  tests/
    test_loader.py           ← NEW
    test_campaign_loop.py    ← NEW
```

Imports: `from campaign.loader import load_game_data, GameData`
Cross-module: `from engine.encounters import resolve_combat, resolve_hazard, resolve_event`
Cross-module: `from generation.characters import generate_character, load_flavor_data`

---

## Completion Criteria

1. `pytest simulation/tests/ -v` passes — ALL tests (M1 + M2a + M2b existing + M2c new)
2. `run_campaign(42, game_data)` completes without error and returns a CampaignResult
3. Same seed produces identical CampaignResult across 10 runs
4. Combat damage values are reasonable (not 15 damage against 140000 HP — confirms scaling works)
5. A campaign with a strong roster can achieve victory (6 regions cleared)
6. A campaign with a weak roster hits game_over before clearing all regions
7. World phase draws and evaluates world cards without error
8. Character draft adds a new Character to roster after each conquest
9. No floats in any game math
10. Zero modification to any existing files (models, engine, generation, data, existing tests)

---

## What This Spec Does NOT Cover

- Real player AI strategies (region selection, world card evaluation, upgrade selection) — M2d
- Real enemy AI heuristics (combo awareness, defensive play) — M2d
- Monte Carlo simulation runner — M2d
- Balance tuning — M3
- Frontend/React — future phase
