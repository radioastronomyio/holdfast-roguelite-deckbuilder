<!--
---
title: "Game Frontend"
description: "React browser-based card game frontend for Holdfast"
author: "CrainBramp"
date: "2026-03-03"
version: "0.1.0"
status: "Pre-Implementation"
tags:
  - type: directory-readme
  - domain: [frontend, game-ui, card-game]
  - tech: [react, tailwind, typescript]
---
-->

# Game Frontend

React browser-based frontend for Holdfast. Phase 2 deliverable — this directory is empty until the Python simulation (Phase 1) validates card math and balance.

---

## 1. Contents

```
game/
├── README.md               # This file
├── src/                     # React application source (planned)
│   ├── engine/              # TypeScript port of ResolverEngine
│   ├── components/          # Card, encounter, map, outpost UI
│   ├── state/               # Redux-style reducer, game state machine
│   └── input/               # Keyboard/controller/mouse handlers
├── public/                  # Static assets (planned)
└── package.json             # Dependencies (planned)
```

---

## 2. Design Intent

The frontend is a dumb renderer. The ResolverEngine calculates full turns synchronously and outputs ActionTuple arrays. React consumes tuples sequentially with CSS transitions. No game logic lives in components.

### Why React, Not a Game Engine

A card game is state management and click targets. No physics, no collision, no sprite animation, no real-time game loop. React handles this natively. Browser deployment means instant sharing. The 2D Pixel Quest UI pack renders identically in CSS/Canvas.

### Universal Card Interface

All game phases use the same interaction model — a horizontal hand of cards, hotkeys 1-N to select, effects resolve. Combat, world phase, outpost, events — one UI pattern everywhere.

---

## 3. Phase 2 vs Phase 3

| Phase | Goal | Visual Quality |
|-------|------|---------------|
| Phase 2: Minimal Playable | Cards as rectangles with text, map as clickable nodes, combat log | Functional, ugly |
| Phase 3: Visual Polish | 2D Pixel Quest integration, card art, animations, sound | Game-quality |

Phase 2 validates whether human decisions feel engaging. Phase 3 makes it look and sound like a game.

---

## 4. Related

| Document | Relationship |
|----------|--------------|
| [Repository Root](../README.md) | Parent directory |
| [Game Design Document](../docs/game-design-document.md) | UI specs, component architecture, input model |
| [data/](../data/README.md) | Shared JSON definitions consumed by frontend |
| [simulation/](../simulation/README.md) | Authoritative ResolverEngine this must match |
| [assets/](../assets/README.md) | 2D Pixel Quest UI pack for Phase 3 |
