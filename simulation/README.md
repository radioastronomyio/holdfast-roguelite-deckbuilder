<!--
---
title: "Balance Simulation"
description: "Python Monte Carlo simulation for card math validation and balance testing"
author: "CrainBramp"
date: "2026-03-17"
version: "0.2.0"
status: "M2a Complete — Resolver Engine & Combat System delivered"
tags:
  - type: directory-readme
  - domain: [simulation, balance, monte-carlo]
  - tech: python
---
-->

# Balance Simulation

Python Monte Carlo simulation that validates card math, detects degenerate combos, and tunes modifier values across thousands of procedurally generated campaigns. This is Phase 1 — the first code written for the project.

---

## 1. Contents

```
simulation/
├── README.md               # This file
├── __init__.py
├── requirements.txt        # Python dependencies (pydantic, pytest)
├── engine/                 # ResolverEngine — stat resolution, combat, encounters
│   ├── __init__.py
│   ├── stats.py            # calculate_stat(), apply_stacking()
│   ├── turn_order.py       # CombatEntity, CT turn order, process_turn_start()
│   ├── encounters.py       # resolve_combat(), resolve_hazard(), resolve_event(), play_card()
│   ├── enemy_ai.py         # pick_enemy_action() — greedy AI (M2a minimal)
│   └── special_handlers.py # SPECIAL_HANDLERS dispatch dict, 3 resolver_special handlers
├── models/                 # Pydantic data models (M1)
│   ├── __init__.py
│   ├── enums.py            # Stat, Operation, Target, Stacking, AiHeuristic, etc.
│   ├── modifier.py         # Modifier model, STAT_SCALE = 1000
│   ├── card.py             # Card, UpgradeEntry, UpgradeTree
│   ├── entity.py           # Character, Enemy, CharacterGenerationBounds
│   ├── campaign.py         # Region, Encounter types, WorldCard, OutpostUpgrade
│   └── flavor.py           # EpithetCondition, ElementStatMap, FlavorPools
└── tests/                  # 192 passing tests (M1 + M2a)
    ├── __init__.py
    ├── fixtures/            # Valid/invalid JSON test fixtures
    ├── test_modifier.py
    ├── test_card.py
    ├── test_entity.py
    ├── test_flavor.py
    ├── test_campaign.py
    ├── test_integration.py
    ├── test_stats.py
    ├── test_turn_order.py
    ├── test_encounters.py
    ├── test_enemy_ai.py
    └── test_special_handlers.py
```

---

## 2. Purpose

The simulation answers balance questions before a playable game exists:

| Metric | Healthy Range | Degenerate Signal |
|--------|--------------|-------------------|
| Win rate across 10K seeds | 40-70% | <30% or >80% |
| Upgrade path pick rate | No branch >70% in winning runs | Any branch >85% = false choice |
| World card skip rate | Varies by context | Always skipped >90% or always picked |
| Speed stat ceiling | Characters act ≤3× per enemy cycle | 5×+ = Speed collapse |
| Card combo win rate | No 2-card combo >90% | Degenerate combo detected |

Three AI heuristics play thousands of campaigns. If all three converge on the same strategy, the game lacks meaningful choice. If one dominates (>80% vs others <40%), the balance is off.

---

## 3. Milestone Status

| Milestone | Status | Delivered |
|-----------|--------|-----------|
| M1 — Data Schemas | Complete | Pydantic models, JSON data files, 95 tests |
| M2a — Resolver Engine & Combat | Complete | Stat resolver, CT turn order, encounter resolution, enemy AI, special handlers (+97 tests) |
| M2b — Procedural Generation | Planned | Character gen, region gen, encounter gen from flavor pools and generation bounds |
| M2c — Campaign Loop | Planned | Full campaign execution: region selection, world phase, draft, upgrades |
| M2d — AI Heuristics | Planned | Aggressive/defensive/balanced player AI, real enemy AI |

---

## 4. Relationship to React Frontend

The simulation's `ResolverEngine` is the authoritative implementation of combat resolution. The React frontend in `../game/` must produce identical results for the same inputs. Both consume shared JSON definitions from `../data/`.

The engine operates as pure functions — deterministic input/output with no side effects. This makes it testable, portable, and eventually translatable to TypeScript for the frontend.

---

## 5. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [Game Design Document](../docs/game-design-document.md) | Mechanical spec this implements |
| [data/](../data/README.md) | Shared JSON definitions consumed by simulation |
| [game/](../game/README.md) | React frontend that must match resolver behavior |
