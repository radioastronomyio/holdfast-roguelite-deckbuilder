<!--
---
title: "Screen Capture Harness"
description: "Playwright regression harness for the Holdfast GameUI dark-fantasy frontend"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [testing, regression, ui]
  - tech: [playwright, python, chromium]
related_documents:
  - "[capture.py](capture.py)"
  - "[Holdfast Spec 01](../../spec/2026-06-22-holdfast-spec-01-gameui-vendor-dom-shell.md)"
---
-->

# Screen Capture Harness

A Playwright (Chromium headless) regression harness that boots the game, walks every placeholder screen off the real `CampaignStepper`, captures a dark-fantasy baseline screenshot per screen, and asserts zero console errors and zero non-origin network requests (the vendored framework is self-contained).

## Running

```bash
# from the game/ directory
npm run test:screens         # capture baselines (python3 tests/capture.py)
npm run test:screens:check   # regression check against committed .sha1 sidecars
```

The harness starts the Vite dev server itself on an isolated port, so no manual `npm run dev` is required. Playwright must be installed (`pip3 install playwright`) with the Chromium browser available.

## Baselines

Baselines live in `baseline/`: one PNG per screen plus a `.sha1` sidecar. Capture mode writes both; `--check` mode recomputes the sha1 and reports `REGRESSION` on any mismatch.

## Walk model

The router marks the active screen with a `data-screen` attribute on the shell main viewport and bumps a `data-render` nonce on every tear-down + mount. Every non-terminal screen carries a `gui-btn[data-advance]` that drives the real `CampaignStepper` and re-routes to the phase it returns. The harness clicks that button, waits for the nonce to change, and captures the first occurrence of each screen.

The terminal `game-over` screen is reached via the `window.__holdfast.showGameOver()` dev hook (a fresh stepper driven to defeat through the real stepper API), mirroring the proven Within Parameters harness pattern. The natural walk only reaches game-over after a full campaign.

## Extension points (specs 02–04)

| Hook | What to change |
|------|----------------|
| `SCREENS` | Append `(step, filename)` for each new screen (card renderer, combat, flow screens). |
| `VERIFY` | Add a GameUI selector per new screen to assert the framework component rendered. |
| `walk` / `capture_game_over` | Add drivers for screens reached outside the linear advance path. |

## Known limitation

The TS sim has a parity gap with the Python sim: world-deck modifiers are not normalised with `tags: []`, so an accepted world modifier active during combat trips `modifier.tags is not iterable` in `specialHandlers.ts`. This blocks the natural walk from completing a full campaign, which is why game-over is captured via the dev hook. The sim is frozen for this presentation spec; the fix is flagged for a sim-side patch.
