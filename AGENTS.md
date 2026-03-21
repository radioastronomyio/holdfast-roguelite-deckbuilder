# Agent Instructions

## Project Identity

**Holdfast** is a browser-based roguelite deckbuilder where every mechanic runs on a universal modifier engine. The player conquers 6 procedurally generated regions in a finite campaign. Two applications share a data layer — a Python simulation and a React frontend, both consuming shared JSON definitions.

## Key Files

| File | Purpose |
|------|---------|
| [docs/game-design-document.md](docs/game-design-document.md) | Source of truth for all mechanics, systems, and architecture |
| [data/](data/) | Shared JSON definitions — the contract between simulation and frontend |
| [spec/](spec/) | Standalone milestone specs — agent execution targets |
| [docs/research/](docs/research/) | Gemini Deep Research output — reference material, not spec |

## Architecture

```
data/          → Shared JSON (cards, characters, regions, world deck)
simulation/    → Python Monte Carlo balance testing (Phase 1)
game/          → React browser frontend (Phase 2+)
```

Both `simulation/` and `game/` consume `data/`. The simulation's ResolverEngine is authoritative — the React frontend must produce identical results for the same inputs.

## Current State

- **Phase:** M3b complete — deck mechanics, upgrade trees, deep_focus_01 fix, fresh 5000-seed analysis
- **GDD:** v1.1 (flavor system, tags, fixed-point arithmetic)
- **Tests:** 336 passing (`pytest simulation/tests/ -v` from simulation/ dir); 7 pre-existing failures (path issues in test_campaign_telemetry/test_collectors/test_campaign_loop — relative-path CWD bug, not M3b regression)
- **Baseline:** `reports/m3-prep-baseline.json` — 1000 seeds × 3 strategies, all in 40-70% range
- **M3a Analysis (pre-deck):** `reports/m3-analysis-pre-deck-mechanics/` — archived baseline before deck mechanics
- **M3b Analysis (post-deck):** `reports/m3-analysis/` — fresh 5000-seed run with full deck mechanics + upgrade trees
- **Next work:** M3c (balance tuning — scope after human review of `reports/m3-analysis/balance-report.md`)

### M3b Key Findings (5000 seeds × 3 strategies, post-deck-mechanics)

| Strategy | Win Rate | Avg Regions | Avg Turns |
|----------|----------|-------------|-----------|
| aggressive | 34.0% | 3.84 | 59 |
| defensive | 43.6% | 4.20 | 47 |
| balanced | 60.7% | 4.68 | 52 |
| **Spread** | **26.7%** | — | — |

**GDD Degenerate Signal Checklist (post-deck-mechanics):**
- Signal 1 (Win rate in band): ⚠️ PARTIAL — balanced at 60.7% (in band), aggressive at 34.0% (below 40% floor)
- Signal 2 (Upgrade dominance): Now populated — upgrade trees loaded from `upgrade-trees.json`
- Signal 3 (World card auto-accept/skip): Check balance report
- Signal 4 (Speed ceiling): IMPROVED — max ratio 77x (down from 597x); remaining high ratios from stun-loop mechanic (shield_bash PCT_SUB Speed 100%), not energy exploit
- Signal 5 (Card combo win rate): deep_focus_01 fixed (cost 1, value 1 Energy) — energy loop eliminated

**Convergence warning:** All strategies pick same first region >80% of the time (difficulty ordering forced).

### M3b Changes Applied

| Change | Details |
|--------|---------|
| `deck_copies` on Card model | Field added to `models/card.py`; all 15 base cards + 6 hazard cards updated in JSON |
| deep_focus_01 fix | energy_cost 0→1, FLAT_ADD Energy value 3→1 (eliminated infinite energy loop) |
| Deck system | `initialize_deck`, `draw_cards`, `discard_hand`, `discard_card` added to `engine/turn_order.py` |
| Combat loop rewrite | `resolve_combat()` now uses hand/draw/discard mechanics + multi-play per turn + seeded RNG |
| Upgrade tree loader | `loader.py` loads `data/cards/upgrade-trees.json`; `GameData.upgrade_trees` now populated |
| Campaign runner | `run_campaign()` passes seeded `rng` to `resolve_combat()`; fixed `_load_region_adjectives` path |
| Stun deadlock fix | `tick_until_next_turn` handles all-speed-0 case (falls back to list-order, no more RuntimeError) |
| New tests | `test_deck_system.py` (8 tests), `test_upgrade_loader.py` (3 tests), `test_deep_focus_fix.py` (3 tests) |

**Convergence warning:** All strategies pick same first region 100% of the time (likely difficulty=1 forced).

### M3-Prep Balance Fixes Applied (branch: m3-prep-balance-fixes)

Six compounding bugs caused 0% win rate. All fixed:

| Bug | Fix | File(s) |
|-----|-----|---------|
| Enemy hazard cards | Filter "hazard"-tagged cards before building enemy pool | `enemies.py`, `encounters.py`, `regions.py`, `runner.py` |
| Player hazard cards | Exclude hazard-tagged cards from `all_card_ids` in runner | `runner.py` |
| Enemy Energy on combat budget | Remove Energy from stat distribution; set fixed 2-5 / 3-6 range | `enemies.py` |
| Enemy Defense invulnerability | Cap Defense at 20 (normal) / 30 (elite); redirect overflow to HP | `enemies.py` |
| Difficulty 1 budget too high | Base budget 90 (down from 150); slope 25; redistributed role weights | `enemies.py` |
| 1 starting character vs 1-3 enemies | Start with 2 characters (5 candidates, pick best 2) | `runner.py` |
| AI world card evaluation bugs | Fix operation-type check and catastrophic-loss guard (both AIs) | `heuristics.py` |
| DefensiveAI region selection | Free intel on hard region caused early difficult assault; now sorts by difficulty first | `heuristics.py` |
| DefensiveAI combat targeting | 70% HP heal threshold wasted turns; now heals only at <30% and targets highest-Power enemy | `heuristics.py` |

### Final Baseline (1000 seeds)

| Strategy | Win Rate | Avg Regions | Avg Turns |
|----------|----------|-------------|-----------|
| aggressive | 45.2% | 4.27 | 76.0 |
| defensive | 40.2% | 4.11 | 113.6 |
| balanced | 51.1% | 4.42 | 118.0 |
| **Spread** | **0.109** | — | — |

### Delivered Milestones

| Milestone | Spec | Delivered |
|-----------|------|-----------|
| **M1** | `openspec/changes/archive/2026-03-17-m1-data-schemas/` | Pydantic models, JSON data files, 95 tests |
| **M2a** | `spec/m2a-resolver-combat-spec.md` | Stat resolver, CT turn order, encounter resolution, greedy enemy AI, special handlers |
| **M2b** | `spec/m2b-procedural-generation-spec.md` | Character/enemy/region/encounter generators |
| **M2c** | `spec/m2c-campaign-loop-spec.md` | Data loader (STAT_SCALE normalization), campaign state, full macro loop |
| **M2d** | `spec/m2d-ai-heuristics-spec.md` | AggressiveAI/DefensiveAI/BalancedAI, enhanced enemy AI, Monte Carlo runner |
| **M3a** | `staging/m3a-balance-analysis-spec.md` | Combat+campaign telemetry, analysis package, 5000-seed run, 15 plots, 9 JSON exports, balance report |
| **M3b** | `staging/m3b-deck-mechanics-spec.md` | deck_copies field, hand/draw/discard system, multi-play per turn, upgrade tree loader, deep_focus_01 fix, 15 new tests, fresh analysis |

## Critical: STAT_SCALE Awareness

`STAT_SCALE = 1000`. Entity `base_stats` in JSON are pre-scaled (HP 140 stored as 140000). **Card effect values in JSON are at display scale** (Arcane Strike FLAT_SUB value: 15, not 15000). The M2c data loader scales FLAT card values by STAT_SCALE at load time. PCT and MULTIPLY values are NOT scaled. Read the M2c spec "Critical: Card Value Scaling" section before touching the campaign loop.

Generation bounds (`data/entities/generation-bounds.json`) are at display scale. M2b generators handle their own scaling.

## Core Concept: Universal Modifier Engine

Everything in the game is modifier arrays on a 5-stat model (HP, Power, Speed, Defense, Energy). Cards, hazards, character passives, outpost upgrades, world events — all resolve through the same engine. Read the GDD modifier tuple format and resolution order before implementing anything.

## Implementation Constraints

- Simulation targets 40-70% win rate across seeds — not 100% solvability
- Card upgrade branches must never pit economy manipulation against flat damage
- Speed percentage modifiers scale exponentially with the CT system — must be capped or taxed
- ResolverEngine must be pure functions — deterministic, no side effects, no UI coupling
- All game state must be serializable as JSON at any point
- All generators use `random.Random(seed)` instances, never global `random`
- Integer-only arithmetic in all game math — no floats

## Session Pattern

1. Read this file
2. Read the spec for the milestone you're working on (in `spec/`)
3. Read the GDD if working on mechanics or data schemas
4. Check directory READMEs for the area you're working in
5. Do work
6. Run `pytest simulation/tests/ -v` — all tests must pass
7. Update this file's "Current State" section if project state changed
