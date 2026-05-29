<!--
---
title: "Game Frontend"
description: "Phaser browser frontend for Holdfast"
author: "CrainBramp"
date: "2026-05-02"
version: "0.2.0"
status: "First Playable"
tags:
  - type: directory-readme
  - domain: [frontend, game-ui, card-game]
  - tech: [phaser, typescript, vite]
---
-->

# Game Frontend

Phaser 4 browser frontend for Holdfast. The frontend is a renderer and input shell over the browser-safe TypeScript simulation in `src/sim/`.

## Commands

```bash
npm run prepare:public
npm test
npm run build
npm run dev
```

`prepare:public` copies shared JSON data and normalized licensed Pixel Quest assets into `public/` for Vite. The build checks for required generated files before compiling.

## Runtime Shape

```
src/sim/      # Browser-safe resolver and stepper state machines
src/scenes/   # Phaser scene lifecycle and transitions
src/ui/       # Reusable Pixel Quest + BitmapText widgets
src/assets/   # Semantic asset manifest
src/systems/  # Browser save/load helpers
```

Game math and state mutation stay in `src/sim/`. Phaser scenes consume stepper state and typed events for rendering and animation.
