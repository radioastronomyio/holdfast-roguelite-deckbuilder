# Agent Instructions

## Project Identity

**Holdfast** is a browser-based roguelite deckbuilder where every mechanic runs on a universal modifier engine. The player conquers 6 procedurally generated regions in a finite campaign. Two applications share a data layer — a Python simulation and a React frontend, both consuming shared JSON definitions.

## Key Files

| File | Purpose |
|------|---------|
| [docs/game-design-document.md](docs/game-design-document.md) | Source of truth for all mechanics, systems, and architecture |
| [data/](data/) | Shared JSON definitions — the contract between simulation and frontend |
| [docs/research/](docs/research/) | Gemini Deep Research output — reference material, not spec |

## Architecture

```
data/          → Shared JSON (cards, characters, regions, world deck)
simulation/    → Python Monte Carlo balance testing (Phase 1)
game/          → React browser frontend (Phase 2+)
```

Both `simulation/` and `game/` consume `data/`. The simulation's ResolverEngine is authoritative — the React frontend must produce identical results for the same inputs.

## Current State

- **Phase:** Pre-Implementation
- **GDD:** v1.0 Complete
- **Next work:** Phase 1 — JSON schema definitions in `data/`, Python resolver engine in `simulation/`
- **No runnable code yet**

## Core Concept: Universal Modifier Engine

Everything in the game is modifier arrays on a 5-stat model (HP, Power, Speed, Defense, Energy). Cards, hazards, character passives, outpost upgrades, world events — all resolve through the same engine. Read the GDD modifier tuple format and resolution order before implementing anything.

## Implementation Constraints

- Simulation targets 40-70% win rate across seeds — not 100% solvability
- Card upgrade branches must never pit economy manipulation against flat damage
- Speed percentage modifiers scale exponentially with the CT system — must be capped or taxed
- ResolverEngine must be pure functions — deterministic, no side effects, no UI coupling
- All game state must be serializable as JSON at any point

## Session Pattern

1. Read this file
2. Read the GDD if working on mechanics or data schemas
3. Check directory READMEs for the area you're working in
4. Do work
5. Update this file's "Current State" section if project state changed
