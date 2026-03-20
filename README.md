<!--
---
title: "Holdfast — Browser-Based Roguelite Deckbuilder"
description: "A finite-campaign roguelite deckbuilder where everything runs on a universal modifier engine"
author: "CrainBramp"
date: "2026-03-03"
version: "0.2.0"
status: "Phase 1 Simulation Complete"
tags:
  - type: project-root
  - domain: [game-dev, card-game, roguelite]
  - tech: [react, python, json]
related_documents:
  - "[Game Design Document](docs/game-design-document.md)"
  - "[GDR Research Output](docs/research/)"
---
-->

# 🃏 Holdfast

[![React](https://img.shields.io/badge/React-Frontend-61DAFB?logo=react&logoColor=white)](https://react.dev)
[![Python](https://img.shields.io/badge/Python-Simulation-3776AB?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

![repo-banner](assets/repo-banner.jpg)

> A finite-campaign roguelite deckbuilder where every mechanic runs on a single universal modifier engine, every card has a trade-off, and the procedural generation can absolutely kill you.

Holdfast is a browser-based card game where the player inherits an outpost on the edge of hostile territory and must conquer 6 procedurally generated regions to win. Combat, exploration, upgrades, and strategy all resolve through the same 5-stat modifier model. Some seeds are brutal. Some are unwinnable. The game's identity lives in that variance — interesting decisions under uncertainty, not guaranteed fairness.

This project is also an experiment in **AI-assisted, spec-driven game development** — building a complete game end-to-end using [OpenSpec](https://github.com/Fission-AI/OpenSpec) for specification management, AI coding agents (KiloCode/GLM, Claude, OpenCode) for implementation, and Monte Carlo simulation for balance validation. The GDD was co-authored with Claude, validated through Gemini Deep Research, and every implementation milestone is spec'd as OpenSpec change proposals that agents execute from. If it works, the methodology is as interesting as the game.

---

## 🔭 Overview

### Design Lineage

The design draws from Soda Dungeon (idle dungeon loop, party roster), Darkest Dungeon (attrition pressure, environmental hazards), Across the Obelisk (card upgrade paths that add effects rather than scale numbers), Legend of Keepers (hazards as pure modifier encounters), Risk (strategic map control, incomplete information), and FTL (procedural maps, resource scarcity).

### Core Concept

Everything in the game — cards, characters, hazards, outpost upgrades, world events — is expressed as modifier arrays on a shared 5-stat model (HP, Power, Speed, Defense, Energy). One resolver engine handles all encounter types. Flavor text is cosmetic. The math is the game.

Character names, attack names, and region names are assembled at generation time from seeded word pools, weighted by the entity's dominant stats. "Mira the Swift, Storm Mage" and "Dusk the Volatile, Void Warden" are the same underlying modifier bundle in different clothes. This creates campaign variety without additional content. The flavor data lives in `mods/default/` — the architecture is mod-ready from day one.

### Why a Card Game

The card game format was chosen because it is the most agent-friendly implementation path. Pure state machines and data — no physics, no real-time input, no animation dependencies. React handles state management and click targets. Python handles balance simulation. Shared JSON definitions tie them together.

### Development Methodology

Each milestone is specified as an [OpenSpec](https://github.com/Fission-AI/OpenSpec) change proposal with detailed specs, design docs, and task checklists. AI coding agents execute against these specs, with human review before every commit. The workflow: Claude orchestrates design and spec authoring → OpenSpec captures the contract → KiloCode/GLM implements against the spec → human reviews and commits. This is a deliberate test of whether spec-driven AI development can produce a complete, balanced game.

---

## 📊 Project Status

| Milestone | Status | Description |
|-----------|--------|-------------|
| Game Design Document | ✅ Complete | Full mechanical spec — [GDD](docs/game-design-document.md) |
| Research Validation | ✅ Complete | Gemini Deep Research (NSB-bounded) |
| Repo & Tooling Setup | ✅ Complete | Repository, OpenSpec, GitHub milestones/issues |
| M1: Data Schemas | ✅ Complete | Pydantic models, JSON data files, 95 tests |
| M2a: Resolver Engine & Combat | ✅ Complete | Stat resolver, CT turn order, encounter resolution, enemy AI, special handlers |
| M2b: Procedural Generation | ✅ Complete | Character/enemy/region/encounter generators from seeded RNG |
| M2c: Campaign Loop | ✅ Complete | Data loader, campaign state machine, full macro loop |
| M2d: AI Heuristics & Monte Carlo | ✅ Complete | 3 player AIs, enhanced enemy AI, Monte Carlo runner |
| M3: Balance Tuning | ⬜ Planned | Run Monte Carlo at scale, tune card/region/upgrade values |
| M4: Minimal Playable Frontend | ⬜ Planned | React browser game — ugly but functional |
| M5: Visual Polish | ⬜ Planned | Asset integration, animations, effects |

**295 tests passing** across the full simulation stack. Run: `pytest simulation/tests/ -v` from repo root.

---

## 🏗️ Architecture

Two applications sharing a data layer — a Python simulation and a React frontend, both consuming the same JSON card/region/character definitions.

![alt text](assets/architecture-section-infographic.jpg)

### Key Design Decisions

The ResolverEngine operates independently of React — it calculates full turns synchronously and outputs ActionTuple arrays. React is a dumb renderer consuming tuples with CSS transitions. This prevents UI state desynchronization.

The simulation targets 40-70% win rate across seeds. It validates card math and decision quality, not seed solvability. Three AI heuristics (aggressive, defensive, balanced) play thousands of campaigns — if they converge on the same strategy, the game lacks meaningful choice.

---

## 📁 Repository Structure

```
holdfast-roguelite-deckbuilder/
├── 📂 assets/                # Game art (2D Pixel Quest UI pack — local only, gitignored)
├── 📂 mods/                  # Mod-ready content layer — game always loads from here
│   └── default/flavor/       # Word pools, epithet conditions, element-stat maps
├── 📂 data/                  # Shared JSON definitions (cards, characters, regions, world deck)
├── 📂 docs/                  # Design documentation and research
│   ├── game-design-document.md
│   └── research/             # GDR output, reference material
├── 📂 game/                  # React frontend (M4+)
├── 📂 spec/                  # Standalone milestone specs (agent execution targets)
├── 📂 openspec/              # OpenSpec metadata and archived change proposals
├── 📂 simulation/            # Python Monte Carlo simulation (Phase 1)
│   ├── models/               # Pydantic data models (M1)
│   ├── engine/               # Resolver engine — stats, turn order, encounters (M2a)
│   ├── generation/           # Procedural generators — characters, enemies, regions (M2b)
│   ├── campaign/             # Campaign loop — loader, state, runner (M2c)
│   ├── agents/               # AI heuristics and Monte Carlo runner (M2d)
│   └── tests/                # 295 tests
├── 📂 scratch/               # Temporary working files (gitignored)
├── 📄 AGENTS.md              # Agent context and session pattern
├── 📄 README.md              # This file
└── 📄 [config]               # .gitignore, cspell, markdownlint, .vscode, pyproject.toml
```

---

## 🎮 Game Summary

### Campaign Loop

Start with an outpost, one character, and a fog-covered map of 6 regions. Research reveals region details in layers. Assault regions by selecting a party (max 3-4 from roster) and progressing through 3 narrative encounters (Approach → Settlement → Stronghold). Conquer a region to earn meta-upgrades, card upgrades, and a new character draft. Between regions, face 3 rounds of world deck cards — every card has both an upside and a downside.

### The Universal Modifier Engine

Every effect resolves as a modifier tuple: stat, operation, value, duration, target. Resolution follows strict priority: base → flat → percentage → multiplicative. One engine, one resolution path, applied everywhere.

### Procedural Characters

No fixed classes. Characters are procedurally generated with randomized stat distributions across the 5-stat model and an innate passive modifier. High HP/Defense/low Speed naturally produces a tank. High Power/Speed/low HP produces a glass cannon. Party composition against region modifiers is the core strategic decision.

### The Unwinnable Seed

The procedural generator does not guarantee solvable campaigns. This is the game's identity. The simulation validates that the distribution is healthy, not that every seed is fair.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- `pip install -r simulation/requirements.txt` (pydantic, pytest)

### Run the Tests

```bash
pytest simulation/tests/ -v
```

### Run a Campaign

```python
from campaign.loader import load_game_data
from campaign.runner import run_campaign
from agents.heuristics import BalancedAI

game_data = load_game_data()
result = run_campaign(seed=42, game_data=game_data, strategy=BalancedAI())
print(f"Victory: {result.victory}, Regions cleared: {result.regions_cleared}")
```

### Run Monte Carlo

```python
from campaign.loader import load_game_data
from agents.monte_carlo import run_monte_carlo, MonteCarloConfig, monte_carlo_to_json
from pathlib import Path

game_data = load_game_data()
config = MonteCarloConfig(seed_start=1, seed_count=100)
result = run_monte_carlo(config, game_data)
monte_carlo_to_json(result, Path("monte_carlo_results.json"))
```

### Read the Design

The [Game Design Document](docs/game-design-document.md) is the source of truth for all mechanics, systems, and architecture decisions.

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [2D Pixel Quest Vol.3 — The UI/GUI](https://barely-games.itch.io/2d-pixel-quest-the-uigui) — UI and card art assets
- [Gemini Deep Research](https://deepmind.google/technologies/gemini/) — Design validation via NSB-bounded research
- Design lineage: Soda Dungeon, Darkest Dungeon, Across the Obelisk, Legend of Keepers, FTL, Risk

---

Last Updated: 2026-03-19 | Status: Phase 1 Simulation Complete — 295 Tests Passing
