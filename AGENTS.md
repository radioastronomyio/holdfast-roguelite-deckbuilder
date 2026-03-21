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

- **Phase:** M3c complete — speed cap, AggressiveAI fix, collector fix; some balance targets remain for M3d
- **GDD:** v1.1 (flavor system, tags, fixed-point arithmetic)
- **Tests:** 351 passing (`pytest simulation/tests/ -v` from simulation/ dir); 7 pre-existing failures (path issues in test_campaign_telemetry/test_collectors/test_campaign_loop — relative-path CWD bug, not regression)
- **M3a Analysis (pre-deck):** `reports/m3-analysis-pre-deck-mechanics/` — archived before deck mechanics
- **M3b Analysis (pre-M3c):** `reports/m3-analysis-pre-m3c/` — archived before M3c tuning
- **M3c Analysis (current):** `reports/m3-analysis/` — 5000-seed run post all M3c changes
- **Next work:** M3d (further tuning to hit aggressive 40% floor; stun loop mitigation; combat duration)

### M3c Key Findings (5000 seeds × 3 strategies, post-speed-cap-and-AI-fix)

| Strategy | Win Rate | Avg Regions | Avg Turns |
|----------|----------|-------------|-----------|
| aggressive | 31.4% | 3.74 | 61 |
| defensive | 42.7% | 4.18 | 50 |
| balanced | 57.2% | 4.58 | 54 |
| **Spread** | **25.8%** | — | — |

**GDD Degenerate Signal Checklist (post-M3c):**
- Signal 1 (Win rate in band): ⚠️ PARTIAL — defensive (43%) and balanced (57%) in band; aggressive (31%) still below 40% floor
- Signal 2 (Upgrade dominance): ✅ NOW POPULATED — 10 cards with non-zero A/B pick rates; arcane_strike_01 A:9675 B:4710
- Signal 3 (World card auto-accept/skip): Check balance report
- Signal 4 (Speed ceiling): ⚠️ Speed cap (+75%) applied; max ratio 109x still from stun loops (shield_bash 100% speed debuff)
- Signal 5 (Card combo win rate): ✅ deep_focus_01 fixed in M3b; no anomaly

**Convergence warning:** All strategies pick same first region >80% of the time (difficulty ordering forced).

**Remaining M3d work:**
- AggressiveAI still at 31.4% — needs further improvements (focus-fire logic, debuff card scoring)
- Stun loop ratio 109x — shield_bash PCT_SUB Speed 100% duration 1 enables repeated stunlocking; reduce duration or value
- Median combat duration 4 turns (target 8-12) — enemy HP budget insufficient without tanking win rates
- Win rate spread 25.8% (target < 20%) — aggressive/balanced gap too wide

### M3c Changes Applied

| Change | Details |
|--------|---------|
| Speed PCT cap | `SPEED_PCT_CAP = 75` in `engine/stats.py`; Speed bonus capped at +75% from pct modifiers |
| Adrenaline stacking | `adrenaline_01` stacking: "stack" → "replace" (prevents double-stacking +30% speed) |
| AggressiveAI fix | Emergency heal at <25% HP; overkill prevention; AoE preference with 2+ enemies; buff value scoring |
| Enemy HP budget | `100 + difficulty * 25` (up from `90 + difficulty * 25`); defense cap 20→25 normal, 30→40 elite |
| Collector branch fix | `_classify_branch()` in collectors.py; branch keys "1A"/"2A_from_1A" etc. now correctly mapped to A/B families |
| New tests | `test_speed_cap.py` (5), `test_aggressive_ai.py` (3), `test_collector_fix.py` (7) — 15 total |
| Archives | `reports/m3-analysis-pre-m3c/` — snapshot of M3b analysis before M3c tuning |

### M3b Changes Applied (still current)

| Change | Details |
|--------|---------|
| `deck_copies` on Card model | Field added to `models/card.py`; all 15 base cards + 6 hazard cards updated in JSON |
| deep_focus_01 fix | energy_cost 0→1, FLAT_ADD Energy value 3→1 (eliminated infinite energy loop) |
| Deck system | `initialize_deck`, `draw_cards`, `discard_hand`, `discard_card` added to `engine/turn_order.py` |
| Combat loop rewrite | `resolve_combat()` now uses hand/draw/discard mechanics + multi-play per turn + seeded RNG |
| Upgrade tree loader | `loader.py` loads `data/cards/upgrade-trees.json`; `GameData.upgrade_trees` now populated |
| Campaign runner | `run_campaign()` passes seeded `rng` to `resolve_combat()`; fixed `_load_region_adjectives` path |
| Stun deadlock fix | `tick_until_next_turn` handles all-speed-0 case (falls back to list-order, no more RuntimeError) |

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
| **M3c** | `staging/m3c-balance-tuning-spec.md` | Speed PCT cap (+75%), AggressiveAI fix, enemy HP budget tuning, collector branch key fix, adrenaline stacking fix, 15 new tests |

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
