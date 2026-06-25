# AGENTS.md

Entry point for AI coding agents working on this repository.

## Project Identity

**Domain:** Game Development / Card Game / Roguelite
**Repository:** https://github.com/radioastronomyio/holdfast-roguelite-deckbuilder
**Purpose:** A browser-based roguelite deckbuilder where every mechanic runs on a universal modifier engine. The player conquers 6 procedurally generated regions in a finite campaign. Two applications share a data layer: a Python simulation and a full-DOM GameUI frontend, both consuming shared JSON definitions.

## Key Files

| File | Purpose |
|------|---------|
| [docs/game-design-document.md](docs/game-design-document.md) | Source of truth for all mechanics, systems, and architecture |
| [data/](data/) | Shared JSON definitions: cards, characters, regions, world deck |
| [spec/](spec/) | Standalone milestone specs: agent execution targets |
| [docs/research/](docs/research/) | Gemini Deep Research output: reference material, not spec |

## Architecture

```
data/          → Shared JSON (cards, characters, regions, world deck)
simulation/    → Python Monte Carlo balance testing (Phase 1)
game/          → Full-DOM GameUI frontend (Phase 2+)
```

Both `simulation/` and `game/` consume `data/`. The simulation's ResolverEngine is authoritative; the GameUI frontend must produce identical results for the same inputs.

## Current State

- **Phase:** M4b first playable; full-DOM GameUI dark-fantasy frontend (shell + placeholder screens) on the M4a TypeScript resolver port
- **GDD:** v1.1 (flavor system, tags, fixed-point arithmetic)
- **Tests:** 367 passing (`pytest simulation/tests/` from repo root); 53 passing (`cd game && npm test`); 8 dark-fantasy screen baselines (`cd game && npm run test:screens:check`)
- **M3a Analysis (pre-deck):** `reports/m3-analysis-pre-deck-mechanics/` archived before deck mechanics
- **M3b Analysis (pre-M3c):** `reports/m3-analysis-pre-m3c/` archived before M3c tuning
- **M3c Analysis (pre-M3d):** `reports/m3-analysis-pre-m3d/` archived before M3d tuning
- **M3d Analysis (current):** `reports/m3-analysis/` 5000-seed run post all M3d changes
- **Next work:** M4b hardening: real screen content (combat spec 03, flow screens spec 04 — both consume the spec 02 card renderer), richer reward UX, full browser QA, and a sim-side fix for the world-modifier `tags` parity gap flagged by the screen harness

### M3d Key Findings (5000 seeds x 3 strategies, post-stun-fix-and-AI-rework)

| Strategy | Win Rate | Avg Regions | Avg Turns |
|----------|----------|-------------|-----------|
| aggressive | 49.9% | 4.29 | 67 |
| defensive | 42.2% | 4.17 | 52 |
| balanced | 51.3% | 4.40 | 61 |
| **Spread** | **9.1%** | | |

**GDD Degenerate Signal Checklist (post-M3d):**
- Signal 1 (Win rate in band): ✅ All three strategies in 40-55% band
- Signal 2 (Upgrade dominance): ✅ Upgrade randomization added; RNG tie-breaking
- Signal 3 (World card auto-accept/skip): ✅ AggressiveAI now accepts net-positive world cards
- Signal 4 (Speed ceiling): ✅ Stun loop fixed; SPEED_MIN_FLOOR=10 prevents 0-Speed stun locks
- Signal 5 (Card combo win rate): ✅ deep_focus_01 fixed in M3b; no anomaly

**Convergence warning:** All strategies pick same first region >80% of the time (difficulty ordering forced).

### M3d Changes Applied

| Change | Details |
|--------|---------|
| Stun fix | `shield_bash_01` Speed PCT_SUB 100 to 50; `SPEED_MIN_FLOOR=10` added to `engine/stats.py` |
| AggressiveAI v2 | Tank guarantee, combo-aware scoring, focus-fire on lowest HP, net-positive world card acceptance |
| Upgrade randomization | `_pick_greedy_upgrade` and `pick_greedy_upgrade` both accept `rng`; tied candidates chosen randomly |
| New tests | `test_speed_floor.py` (5), `test_aggressive_ai_v2.py` (5), `test_upgrade_picker.py` (5) |
| Archives | `reports/m3-analysis-pre-m3d/` snapshot before M3d tuning |

### M3c Changes Applied

| Change | Details |
|--------|---------|
| Speed PCT cap | `SPEED_PCT_CAP = 75` in `engine/stats.py`; capped at +75% from pct modifiers |
| Adrenaline stacking | "stack" to "replace" (prevents double-stacking +30% speed) |
| AggressiveAI fix | Emergency heal at <25% HP; overkill prevention; AoE preference with 2+ enemies |
| Enemy HP budget | `100 + difficulty * 25` (up from `90 + difficulty * 25`); defense caps raised |
| Collector branch fix | Branch keys correctly mapped to A/B families |
| New tests | `test_speed_cap.py` (5), `test_aggressive_ai.py` (3), `test_collector_fix.py` (7) |

### M3b Changes Applied

| Change | Details |
|--------|---------|
| `deck_copies` on Card model | Field added; all 15 base cards + 6 hazard cards updated in JSON |
| deep_focus_01 fix | energy_cost 0 to 1, FLAT_ADD Energy value 3 to 1 (eliminated infinite energy loop) |
| Deck system | `initialize_deck`, `draw_cards`, `discard_hand`, `discard_card` added |
| Combat loop rewrite | Uses hand/draw/discard mechanics + multi-play per turn + seeded RNG |
| Upgrade tree loader | `loader.py` loads `data/cards/upgrade-trees.json`; `GameData.upgrade_trees` populated |

### Delivered Milestones

| Milestone | Spec | Delivered |
|-----------|------|-----------|
| **M1** | `openspec/changes/archive/2026-03-17-m1-data-schemas/` | Pydantic models, JSON data files, 95 tests |
| **M2a** | `spec/m2a-resolver-combat-spec.md` | Stat resolver, CT turn order, encounter resolution |
| **M2b** | `spec/m2b-procedural-generation-spec.md` | Character/enemy/region/encounter generators |
| **M2c** | `spec/m2c-campaign-loop-spec.md` | Data loader, campaign state, full macro loop |
| **M2d** | `spec/m2d-ai-heuristics-spec.md` | 3 player AIs, enhanced enemy AI, Monte Carlo runner |
| **M3a** | `staging/m3a-balance-analysis-spec.md` | Telemetry, analysis package, 5000-seed run, balance report |
| **M3b** | `staging/m3b-deck-mechanics-spec.md` | Deck system, upgrade tree loader, deep_focus_01 fix |
| **M3c** | `staging/m3c-balance-tuning-spec.md` | Speed cap, AI fixes, enemy HP tuning |
| **M3d** | (inline fixes) | Stun fix, AggressiveAI v2, upgrade randomization |
| **M4a** | (TypeScript resolver port) | Browser-safe sim package, parity fixtures, seeded RNG |
| **M4b** | `spec/m4b-phaser-frontend-spec-v3.md` | Phaser 4 first playable, steppers, scenes, Pixel Quest public prep |
| **M4b-GUI** | `spec/2026-06-22-holdfast-spec-01-gameui-vendor-dom-shell.md` | GameUI vendored (dark-fantasy), Phaser removed, vanilla DOM screen router + placeholder screens, Playwright baselines |
| **M4b-GUI-02** | `spec/2026-06-22-holdfast-spec-02-card-renderer.md` | Data-driven `createHoldfastCard` over `createCard` (energy badge, effect icons, accent tint, upgrade pips, shine, inspect modal), RPG icon staging, DEV-gated card-gallery route + 8th dark-fantasy baseline |

## Critical: STAT_SCALE Awareness

`STAT_SCALE = 1000`. Entity `base_stats` in JSON are pre-scaled (HP 140 stored as 140000). **Card effect values in JSON are at display scale** (Arcane Strike FLAT_SUB value: 15, not 15000). The M2c data loader scales FLAT card values by STAT_SCALE at load time. PCT and MULTIPLY values are NOT scaled. Read the M2c spec "Critical: Card Value Scaling" section before touching the campaign loop.

Generation bounds (`data/entities/generation-bounds.json`) are at display scale. M2b generators handle their own scaling.

## Core Concept: Universal Modifier Engine

Everything in the game is modifier arrays on a 5-stat model (HP, Power, Speed, Defense, Energy). Cards, hazards, character passives, outpost upgrades, world events all resolve through the same engine. Read the GDD modifier tuple format and resolution order before implementing anything.

## Implementation Constraints

- Simulation targets 40-70% win rate across seeds, not 100% solvability
- Card upgrade branches must never pit economy manipulation against flat damage
- Speed percentage modifiers scale exponentially with the CT system; must be capped or taxed
- ResolverEngine must be pure functions: deterministic, no side effects, no UI coupling
- All game state must be serializable as JSON at any point
- All generators use `random.Random(seed)` instances, never global `random`
- Integer-only arithmetic in all game math, no floats

## Execution Environment

**Primary execution:** ML01 (`/opt/repos/holdfast-roguelite-deckbuilder/`)
**Agent runtime:** OpenCode (global config at `~/.config/opencode/opencode.json`)
**Session management:** aoe (Agent of Empires)
**Strategic work:** Claude.ai Projects
**Agentic coding:** Claude Code, OpenCode

## Repository Structure

```
holdfast-roguelite-deckbuilder/
├── assets/                         # Game art (licensed asset pack, gitignored)
├── data/                           # Shared JSON definitions
├── docs/
│   ├── documentation-standards/    # Templates, tagging strategy
│   ├── research/                   # GDR output, reference material
│   └── game-design-document.md     # Source of truth for all mechanics
├── game/                           # Full-DOM GameUI frontend (Phase 2+)
├── internal-files/                 # Working documents
├── mods/
│   └── default/flavor/             # Word pools, epithet conditions
├── openspec/                       # OpenSpec metadata and archived change proposals
├── reports/                        # Monte Carlo analysis outputs
├── scripts/                        # Helper scripts
├── shared/                         # Cross-project utilities
├── simulation/                     # Python Monte Carlo simulation
│   ├── models/                     # Pydantic data models
│   ├── engine/                     # Resolver engine
│   ├── generation/                 # Procedural generators
│   ├── campaign/                   # Campaign loop
│   ├── agents/                     # AI heuristics and Monte Carlo runner
│   └── tests/                      # 377 tests
├── spec/                           # Milestone specs (agent execution targets)
├── staging/                        # Staged work (gitignored)
├── AGENTS.md                       # This file
├── CLAUDE.md                       # Pointer to AGENTS.md
├── LICENSE                         # MIT
└── README.md
```

## Conventions

- **Documentation:** Use templates from `docs/documentation-standards/`
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `test:`)
- **Tests:** `pytest simulation/tests/ -v` must pass before every commit
- **Frontmatter:** YAML frontmatter with tags from `docs/documentation-standards/tagging-strategy.md`
- **Interior READMEs:** Every directory has one

## Session Pattern

1. Read this file
2. Read the spec for the milestone you're working on (in `spec/`)
3. Read the GDD if working on mechanics or data schemas
4. Check directory READMEs for the area you're working in
5. Do work
6. Run `pytest simulation/tests/ -v`; all tests must pass
7. Update this file's "Current State" section if project state changed
