# M2d: AI Heuristics & Monte Carlo Runner

**Status:** Spec
**Date:** 2026-03-17
**Depends on:** M2c (Campaign Loop — must be complete before M2d execution)
**Context:** With the campaign loop executing full campaigns (M2c), this milestone adds the three GDD-specified AI heuristics (aggressive, defensive, balanced), replaces the greedy enemy AI with a more capable version, and builds the Monte Carlo runner that validates balance across thousands of seeds.

---

## Overview

Three modules: player AI strategies that replace M2c placeholder heuristics, enhanced enemy AI that replaces the M2a greedy AI, and a Monte Carlo runner that executes campaigns at scale and outputs balance metrics. This is the capstone of Phase 1 — after M2d, the simulation can answer the core balance questions from the GDD.

All new code lands in `simulation/agents/`. All tests run via `pytest simulation/tests/ -v` from repo root.

---

## Existing Codebase (Reference)

| File | Contains | Modification Allowed? |
|------|----------|-----------------------|
| `simulation/campaign/runner.py` | `run_campaign()` with placeholder heuristics | YES — must accept a strategy parameter |
| `simulation/engine/encounters.py` | `resolve_combat()`, `_player_pick_card()` | YES — `_player_pick_card()` must be replaceable |
| `simulation/engine/enemy_ai.py` | `pick_enemy_action()` (greedy) | YES — swap or extend |
| `simulation/campaign/loader.py` | `load_game_data()`, `GameData` | No |
| `simulation/campaign/state.py` | `CampaignState`, `RegionState` | No |
| `simulation/generation/` | All generators | No |
| `simulation/engine/stats.py` | `calculate_stat()` | No |
| `simulation/engine/turn_order.py` | `CombatEntity`, `get_current_stat()` | No |
| `simulation/models/` | All Pydantic models | No |

**Key modification:** `run_campaign()` and `resolve_combat()` currently use hardcoded placeholder strategies. M2d must refactor these to accept a strategy object so different AI heuristics can be plugged in.

---

## Design Constraints (Non-Negotiable)

1. **Strategy pattern, not inheritance hierarchy.** AI strategies are Protocol-based (structural subtyping). A strategy is any object that implements the required methods. No abstract base classes, no registration, no plugin system.

2. **Strategies are stateless between campaigns.** A strategy instance can track state within a single campaign run but must be re-instantiable for each new seed. No learning, no cross-campaign memory.

3. **The three GDD heuristics must produce meaningfully different behavior.** If all three converge on the same strategy for a given seed, the game lacks meaningful choice (GDD §Balance Simulation).

4. **Monte Carlo runner is parallel-safe.** Each campaign run is independent. The runner should support `multiprocessing` for throughput but must work single-threaded for debugging.

5. **Output format is JSON.** Monte Carlo results are machine-readable for analysis. No CSV, no custom formats.

6. **Enhanced enemy AI replaces greedy AI globally.** The old `pick_enemy_action()` greedy logic becomes a fallback within the new enemy AI, not a separate code path.

---

## Deliverable 1: Player AI Strategy Interface (`simulation/agents/strategy.py`)

### Outcome

A Protocol defining the strategy interface plus three concrete implementations.

```python
from typing import Protocol

class PlayerStrategy(Protocol):
    """Interface for player campaign AI."""

    def select_region(
        self,
        state: CampaignState,
        game_data: GameData,
    ) -> RegionState:
        """Choose which region to assault next."""
        ...

    def select_party(
        self,
        state: CampaignState,
        game_data: GameData,
        region: RegionState,
    ) -> list[Character]:
        """Choose which characters to bring (up to party_size)."""
        ...

    def select_card(
        self,
        caster: CombatEntity,
        available_cards: list[Card],
        allies: list[CombatEntity],
        enemies: list[CombatEntity],
    ) -> tuple[Card, list[CombatEntity]] | None:
        """Choose a card to play during combat (replaces _player_pick_card)."""
        ...

    def evaluate_world_card(
        self,
        card: WorldCard,
        state: CampaignState,
        game_data: GameData,
    ) -> bool:
        """Accept (True) or skip (False) a world card."""
        ...

    def select_event_choice(
        self,
        choices: list[EventChoice],
        state: CampaignState,
    ) -> int:
        """Choose which event option to take (returns index)."""
        ...

    def select_card_upgrade(
        self,
        roster_cards: list[str],
        upgrade_trees: dict[str, dict[str, UpgradeEntry]],
        applied_upgrades: dict[str, list[str]],
        state: CampaignState,
    ) -> tuple[str, str] | None:
        """Choose a card upgrade. Returns (card_id, branch_key) or None."""
        ...

    def select_research(
        self,
        state: CampaignState,
        game_data: GameData,
    ) -> RegionState | None:
        """Choose a region to research (or None to skip research)."""
        ...

    def select_drafted_character(
        self,
        candidates: list[Character],
        state: CampaignState,
    ) -> Character:
        """Pick one character from the draft pool."""
        ...
```

---

## Deliverable 2: Three AI Heuristics (`simulation/agents/heuristics.py`)

### AggressiveAI

Behavior profile (GDD §Simulation Framework): "Always picks highest-damage cards. Rushes regions. Minimal research."

```python
class AggressiveAI:
    """
    Aggressive strategy — maximize damage output, rush through campaign.

    Region selection: lowest difficulty first (rush easy regions, snowball)
    Party selection: highest Power characters
    Card selection: highest damage card affordable, targeting lowest-HP enemy
    World card evaluation: accept if Power or Speed upside, regardless of downside
    Event choice: highest offensive effect (most FLAT_SUB HP or PCT_ADD Power)
    Card upgrades: prioritize damage-boosting branches
    Research: never research (waste of time, rush blind)
    Draft: pick highest Power character
    """
```

### DefensiveAI

Behavior profile: "Prioritizes mitigation and healing. Full research before assault."

```python
class DefensiveAI:
    """
    Defensive strategy — survive through attrition, maximize information.

    Region selection: only assault fully researched (level 4) regions.
        If none fully researched, research instead.
        If forced to assault (all partially researched, no resources), pick highest-researched.
    Party selection: highest HP + Defense characters
    Card selection: prioritize healing/defense cards when HP < 70%, damage otherwise.
        Target: buff lowest-HP ally if healing, attack lowest-HP enemy if damaging.
    World card evaluation: accept only if HP or Defense upside AND downside doesn't reduce HP/Defense
    Event choice: lowest cost option (minimize HP loss)
    Card upgrades: prioritize Defense/HP boosting branches
    Research: always research if resources available, cheapest layer first
    Draft: pick highest HP character
    """
```

### BalancedAI

Behavior profile: "Scores cards by context. Moderate research. Adapts party composition."

```python
class BalancedAI:
    """
    Balanced strategy — context-dependent scoring, moderate planning.

    Region selection: moderate — research to level 2 before assault,
        then pick the region whose modifier stack least harms current roster.
    Party selection: score each character against the region's modifier stack.
        High Defense roster vs high-damage region, high Speed vs slow enemies, etc.
    Card selection: score each card by situation:
        - If any ally HP < 40%: weight healing cards 2×
        - If enemies > 2: weight AoE cards 2×
        - If single enemy (boss): weight high single-target damage 2×
        - Otherwise: pick highest damage-per-energy card
    World card evaluation: score net effect. Accept if sum of upside stat gains
        exceeds sum of downside stat losses by > 20% margin.
    Event choice: score each choice by net modifier impact
    Card upgrades: alternate between offense and defense branches
    Research: research to level 2 before assault, don't over-invest
    Draft: pick character whose highest stat fills a gap in the current roster
    """
```

### Tests (`simulation/tests/test_heuristics.py`)

| Test | Setup | Expected |
|------|-------|----------|
| AggressiveAI never researches | Run 10 campaigns | resources_spent_on_research == 0 for all |
| DefensiveAI researches heavily | Run 10 campaigns | resources_spent_on_research > 0 for all |
| AggressiveAI selects high-Power party | Roster with mixed stats | Party has top-N Power characters |
| DefensiveAI selects high-HP party | Roster with mixed stats | Party has top-N HP characters |
| BalancedAI adapts card selection | Low HP scenario | Prefers healing cards |
| BalancedAI adapts card selection | Multi-enemy scenario | Prefers AoE cards |
| AggressiveAI accepts Power world card | World card with +Power upside | Returns True |
| DefensiveAI rejects HP-losing world card | World card with HP downside | Returns False |
| All three produce different region orders | Same seed, 3 strategies | At least 2 different region selection sequences |
| Strategy is deterministic | Same seed + strategy | Identical decisions |
| Protocol conformance | Each AI class | Passes isinstance check via Protocol |

---

## Deliverable 3: Enhanced Enemy AI (`simulation/agents/enemy_ai_v2.py`)

### Outcome

Replace the M2a greedy enemy AI with a context-aware version.

```python
def pick_enemy_action_v2(
    enemy: CombatEntity,
    available_cards: list[Card],
    party: list[CombatEntity],
    allies: list[CombatEntity],
    turn_number: int,
) -> tuple[Card, list[CombatEntity]] | None:
    """
    Enhanced enemy AI with behavior modes based on ai_heuristic.

    Aggressive enemies (ai_heuristic == "aggressive"):
      - Same as M2a greedy: highest damage card, lowest HP target
      - NEW: if a buff card is available AND turn 1, play buff first (setup combo)

    Defensive enemies (ai_heuristic == "defensive"):
      - If own HP < 50% and a healing/defense card is affordable: play it on self
      - Otherwise: attack lowest-HP party member
      - NEW: prefer Defense buff cards when outnumbered

    Balanced enemies (ai_heuristic == "balanced"):
      - Turn 1: play buff/debuff card if available (setup)
      - Turn 2+: attack, preferring AoE if 2+ targets, single-target if 1 target
      - Target selection: lowest HP party member, but switch to highest-threat
        (highest Power) if that target is under 60% HP (focus fire the carry)
      - NEW: if an AoE debuff (Defense PCT_SUB) is available and 2+ enemies alive, prefer it

    All modes:
      - Respect energy budget
      - Skip turn (return None) if no affordable card
      - Fallback to M2a greedy logic if no heuristic-specific card is found
    """
```

### Wiring

The enhanced enemy AI must replace `pick_enemy_action` in `resolve_combat()`. Options:
- Modify `resolve_combat()` to call `pick_enemy_action_v2()` instead of `pick_enemy_action()`
- OR add an `enemy_ai` parameter to `resolve_combat()` with a default

Choose the approach that requires the least disruption to existing tests. The M2a tests for `pick_enemy_action()` must still pass — either by keeping the old function as a wrapper or by ensuring v2 with "aggressive" heuristic produces equivalent behavior.

### Tests (`simulation/tests/test_enemy_ai_v2.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Aggressive: highest damage card | 3 cards, aggressive enemy | Picks highest damage |
| Aggressive: buff on turn 1 | Buff card available, turn 1 | Plays buff before attacking |
| Defensive: heals when low | HP < 50%, heal card available | Plays heal on self |
| Defensive: attacks when healthy | HP > 80%, attack cards | Attacks lowest HP target |
| Balanced: debuffs turn 1 | Debuff card available, turn 1 | Plays debuff |
| Balanced: AoE when multiple targets | 3 party members alive | Prefers AoE card |
| Balanced: focus fire carry | One high-Power party member low HP | Targets that character |
| All: respects energy budget | Best card too expensive | Falls back to affordable card |
| All: no card returns None | All cards too expensive | Returns None |
| Backward compatible | Same inputs as M2a tests | Same outputs for aggressive mode |

---

## Deliverable 4: Campaign Runner Refactor

### Outcome

Refactor `run_campaign()` to accept a `PlayerStrategy` and wire the enhanced enemy AI.

```python
def run_campaign(
    seed: int,
    game_data: GameData,
    strategy: PlayerStrategy | None = None,
) -> CampaignResult:
    """
    Execute a campaign with a given strategy.
    If strategy is None, use BalancedAI as default (preserving M2c test compatibility).
    """
```

The refactor must:
- Replace all placeholder heuristic calls with `strategy.method()` calls
- Wire `pick_enemy_action_v2` into combat resolution
- Add strategy name to CampaignResult for analysis
- Keep `run_campaign(seed, game_data)` working with no strategy arg (backward compatible)

---

## Deliverable 5: Monte Carlo Runner (`simulation/agents/monte_carlo.py`)

### Outcome

Run campaigns at scale across seed ranges and AI heuristics, collecting balance metrics.

```python
@dataclass
class MonteCarloConfig:
    seed_start: int = 1
    seed_count: int = 1000
    strategies: list[str] = field(default_factory=lambda: ["aggressive", "defensive", "balanced"])
    workers: int = 1             # multiprocessing workers (1 = single-threaded)

@dataclass
class StrategyMetrics:
    strategy_name: str
    total_runs: int
    wins: int
    losses: int
    win_rate: float              # wins / total_runs
    avg_regions_cleared: float
    avg_total_turns: float
    world_cards_accepted_rate: float
    world_cards_skipped_rate: float
    avg_resources_spent: float

@dataclass
class MonteCarloResult:
    config: MonteCarloConfig
    strategy_results: list[StrategyMetrics]
    per_seed_results: dict[int, dict[str, CampaignResult]]  # seed → {strategy_name → result}
    # Balance signals
    win_rate_spread: float       # max win rate - min win rate across strategies
    convergence_warning: bool    # True if all strategies produce same region order >80% of time

def run_monte_carlo(config: MonteCarloConfig, game_data: GameData) -> MonteCarloResult:
    """
    Execute Monte Carlo simulation.

    1. For each seed in range(seed_start, seed_start + seed_count):
       For each strategy in config.strategies:
         result = run_campaign(seed, game_data, strategy_instance)
         Store result
    2. Aggregate metrics per strategy
    3. Compute balance signals:
       - Win rate per strategy
       - Win rate spread (max - min) — healthy: < 30 percentage points
       - Convergence check: do all strategies select same first region >80%?
       - Avg regions cleared per strategy
    4. Return MonteCarloResult
    """

def monte_carlo_to_json(result: MonteCarloResult, output_path: Path) -> None:
    """Serialize results to JSON for analysis."""
```

### Tests (`simulation/tests/test_monte_carlo.py`)

| Test | Setup | Expected |
|------|-------|----------|
| Single seed runs | config with seed_count=1 | Completes without error |
| 10-seed run | config with seed_count=10 | All 30 campaign results present (10 × 3 strategies) |
| Win rate computed | 10-seed run | win_rate between 0.0 and 1.0 for each strategy |
| Deterministic | Run 10-seed twice | Identical MonteCarloResult |
| JSON output | Run and serialize | Valid JSON file, parseable back |
| Different strategies produce different win rates | 50-seed run | At least 2 strategies have different win_rate |
| Convergence detection | Rigged scenario | convergence_warning=True when all strategies identical |
| Per-seed results indexed | 10-seed run | per_seed_results has all 10 seeds |
| Metrics aggregation | 10-seed run | avg_regions_cleared is reasonable (1-6) |

---

## File Structure

```
simulation/
  agents/
    __init__.py
    strategy.py         ← PlayerStrategy Protocol
    heuristics.py       ← AggressiveAI, DefensiveAI, BalancedAI
    enemy_ai_v2.py      ← pick_enemy_action_v2()
    monte_carlo.py       ← MonteCarloConfig, MonteCarloResult, run_monte_carlo()
  tests/
    test_heuristics.py       ← NEW
    test_enemy_ai_v2.py      ← NEW
    test_monte_carlo.py      ← NEW
```

### Modified Files (M2d is the ONLY milestone that modifies existing files)

| File | Change |
|------|--------|
| `simulation/campaign/runner.py` | Add `strategy` parameter to `run_campaign()`, wire strategy calls |
| `simulation/engine/encounters.py` | Make player card selection pluggable (accept callback or strategy), wire `pick_enemy_action_v2` |

**Backward compatibility:** `run_campaign(seed, game_data)` with no strategy must still work (defaults to BalancedAI). All M2c tests must continue to pass without modification.

---

## Completion Criteria

1. `pytest simulation/tests/ -v` passes — ALL tests (M1 + M2a + M2b + M2c existing + M2d new)
2. All three AI heuristics conform to `PlayerStrategy` Protocol
3. `run_campaign(42, game_data, AggressiveAI())` completes and returns CampaignResult
4. Same for DefensiveAI and BalancedAI
5. 10-seed Monte Carlo run completes for all 3 strategies (30 total campaigns)
6. At least 2 strategies produce measurably different win rates over 50 seeds
7. Enhanced enemy AI backward-compatible with M2a test expectations
8. Monte Carlo results serialize to valid JSON
9. All M2c tests pass without modification (backward compatibility)
10. No floats in game math (float only in post-hoc metric aggregation like win_rate)

---

## What This Spec Does NOT Cover

- Balance tuning (adjusting card values, region difficulty curves) — M3
- Frontend/React — M4
- Prestige system, cross-campaign progression — future
- Speed collapse detection beyond basic speed ceiling metric — future
- Card combo detection (2-card combo win rate) — could extend MonteCarloResult but deferred
