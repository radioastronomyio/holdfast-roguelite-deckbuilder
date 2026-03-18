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

- **Phase:** M2a Complete — M2b/M2c/M2d specs ready for execution
- **GDD:** v1.1 (flavor system, tags, fixed-point arithmetic)
- **M1 delivered:** All data schemas, Pydantic models, JSON data files, and 95 passing tests
- **M2a delivered:** Stat resolver, CT turn order, combat/hazard/event resolution, greedy enemy AI, resolver special handlers — 192 total tests passing

### Next Work (Sequential Dependency Chain)

| Milestone | Spec | Scope | Depends On |
|-----------|------|-------|------------|
| **M2b** | `spec/m2b-procedural-generation-spec.md` | Character/enemy/region/encounter generators | M2a (complete) |
| **M2c** | `spec/m2c-campaign-loop-spec.md` | Data loader, campaign state, full macro loop | M2b |
| **M2d** | `spec/m2d-ai-heuristics-spec.md` | 3 player AIs, enhanced enemy AI, Monte Carlo runner | M2c |

**Execute in order.** Each spec lists its own completion criteria. Run `pytest simulation/tests/ -v` after each milestone — all previous tests must still pass.

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
