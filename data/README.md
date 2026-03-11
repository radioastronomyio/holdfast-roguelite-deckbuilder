<!--
---
title: "Shared Game Data"
description: "JSON definitions consumed by both the React frontend and Python simulation"
author: "CrainBramp"
date: "2026-03-03"
version: "0.1.0"
status: "Pre-Implementation"
tags:
  - type: directory-readme
  - domain: [game-data, schema]
  - tech: json
---
-->

# Shared Game Data

JSON definitions for all game entities — cards, characters, regions, encounters, and world deck. This is the shared contract between the React frontend and Python simulation. Both consume these files directly; neither owns them.

---

## 1. Contents

```
data/
├── README.md                 # This file
├── cards/                    # Card definitions with upgrade trees
│   ├── base-cards.json     # 15 base cards
│   ├── upgrade-trees.json    # Upgrade paths for each card
│   └── hazard-cards.json     # 5 hazard cards (region-played)
├── entities/                  # Character and enemy definitions
│   ├── example-characters.json  # 3 GDD example characters
│   ├── example-enemies.json     # 4 example enemies
│   └── generation-bounds.json  # Stat bounds for procedural generation
├── campaign/                  # Campaign structures
│   ├── example-regions.json     # 2 GDD example regions
│   ├── world-deck.json         # 20 world phase cards
│   └── outpost-upgrades.json    # 5 outpost upgrades
└── enums.json                # Shared enum definitions
mods/                            # Flavor and name generation pools
├── README.md                   # Mod architecture documentation
└── default/
    ├── README.md                 # Default mod structure
    └── flavor/                 # Flavor data files
        ├── given_names.json          # 60+ first names
        ├── archetypes.json           # 20+ character class labels
        ├── action_verbs.json         # 30+ attack action verbs
        ├── region_adjectives.json    # 30+ region name adjectives
        ├── region_nouns.json         # 30+ region name nouns
        ├── element-stat-map.json     # Stat to element pools
        └── epithet-conditions.json   # 20+ condition-based epithets
```

---

## 2. Design Principles

All game data follows the universal modifier model defined in the [GDD](../docs/game-design-document.md). Every entity — whether a card, a hazard, a character passive, or an outpost upgrade — is expressed as an array of modifier tuples on the 5-stat model (HP, Power, Speed, Defense, Energy).

The modifier tuple format:

```json
{
  "stat": "HP | Power | Speed | Defense | Energy",
  "operation": "FLAT_ADD | FLAT_SUB | PCT_ADD | PCT_SUB | MULTIPLY",
  "value": 15,
  "duration": 0,
  "target": "SELF | ALLY_SINGLE | ALLY_ALL | ENEMY_SINGLE | ENEMY_ALL | GLOBAL"
}
```

---

## 3. Consumers

| System | How It Uses Data | Path |
|--------|-----------------|------|
| Python Simulation | Loads JSON directly for Monte Carlo runs | `../simulation/` |
| React Frontend | Imports JSON for game rendering and state | `../game/` |
| JSON Schema | Validates all definitions against the modifier contract | `schema/` |

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [Game Design Document](../docs/game-design-document.md) | Source of truth for all data structures |
| [simulation/](../simulation/README.md) | Python consumer |
| [game/](../game/README.md) | React consumer |
