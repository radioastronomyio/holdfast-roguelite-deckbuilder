<!--
---
title: "Holdfast — Browser-Based Roguelite Deckbuilder"
description: "A finite-campaign roguelite deckbuilder where everything runs on a universal modifier engine"
author: "CrainBramp"
date: "2026-03-03"
version: "0.1.0"
status: "Pre-Implementation"
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
| M1: Data Schemas & Foundations | 🔄 In Progress | JSON schemas, Pydantic validation, test fixtures — [spec](openspec/changes/m1-data-schemas/) |
| M2: Simulation Engine | ⬜ Planned | Resolver engine, combat system, campaign generator, AI heuristics |
| M3: Simulation Validation & Tuning | ⬜ Planned | Monte Carlo harness, balance analysis, tuning iteration |
| M4: Minimal Playable Frontend | ⬜ Planned | React browser game — ugly but functional |
| M5: Visual Polish | ⬜ Planned | Asset integration, animations, effects |

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
├── 📂 data/                  # Shared JSON definitions (cards, characters, regions)
├── 📂 docs/                  # Design documentation and research
│   ├── game-design-document.md
│   └── research/             # GDR output, reference material
├── 📂 game/                  # React frontend (M4+)
├── 📂 openspec/              # Spec-driven development — change proposals and specs
│   ├── changes/              # Active and archived change proposals
│   └── specs/                # Accumulated capability specs
├── 📂 simulation/            # Python Monte Carlo (M1-M3)
├── 📂 scratch/               # Temporary working files (gitignored)
├── 📄 AGENTS.md              # Agent context and session pattern
├── 📄 README.md              # This file
└── 📄 [config]               # .gitignore, cspell, markdownlint, .vscode, openspec
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

> M1 (Data Schemas & Foundations) is in progress. No runnable code yet.

### Read the Design

The [Game Design Document](docs/game-design-document.md) is the source of truth for all mechanics, systems, and architecture decisions.

### Current Work

M1 defines JSON schemas and Pydantic validation for every data type in the game. The active spec is at [`openspec/changes/m1-data-schemas/`](openspec/changes/m1-data-schemas/). Once M1 lands, M2 builds the resolver engine and combat system on top of these schemas.

---

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [2D Pixel Quest Vol.3 — The UI/GUI](https://barely-games.itch.io/2d-pixel-quest-the-uigui) — UI and card art assets
- [Gemini Deep Research](https://deepmind.google/technologies/gemini/) — Design validation via NSB-bounded research
- Design lineage: Soda Dungeon, Darkest Dungeon, Across the Obelisk, Legend of Keepers, FTL, Risk

---

Last Updated: 2026-03-04 | Status: M1 In Progress
