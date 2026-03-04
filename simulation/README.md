<!--
---
title: "Balance Simulation"
description: "Python Monte Carlo simulation for card math validation and balance testing"
author: "CrainBramp"
date: "2026-03-03"
version: "0.1.0"
status: "Pre-Implementation"
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
├── engine/                  # ResolverEngine — universal modifier resolution (planned)
├── agents/                  # AI heuristics: aggressive, defensive, balanced (planned)
├── campaign/                # Campaign generation and macro loop (planned)
├── analysis/                # Output analysis and reporting (planned)
└── requirements.txt         # Python dependencies (planned)
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

## 3. Relationship to React Frontend

The simulation's `ResolverEngine` is the authoritative implementation of combat resolution. The React frontend in `../game/` must produce identical results for the same inputs. Both consume shared JSON definitions from `../data/`.

The engine operates as pure functions — deterministic input/output with no side effects. This makes it testable, portable, and eventually translatable to TypeScript for the frontend.

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [Game Design Document](../docs/game-design-document.md) | Mechanical spec this implements |
| [data/](../data/README.md) | Shared JSON definitions consumed by simulation |
| [game/](../game/README.md) | React frontend that must match resolver behavior |
