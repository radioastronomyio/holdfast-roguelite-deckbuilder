<!--
---
title: "Game Frontend"
description: "Full-DOM GameUI dark-fantasy frontend for Holdfast"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [frontend, game-ui, card-game, design-system]
  - tech: [typescript, dom, gameui, vite]
related_documents:
  - "[Vendored GameUI Framework](vendor/gameui/VENDORED.md)"
  - "[UI Layer](src/ui/README.md)"
  - "[Screen Capture Harness](tests/README.md)"
---
-->

# Game Frontend

Full-DOM GameUI dark-fantasy frontend for Holdfast. A pinned copy of the [GameUI](https://github.com/radioastronomyio/gameui-browser-gaming-framework) zero-build-step framework is vendored under `vendor/gameui/`; the dark-fantasy preset is the single styling source. A hand-rolled vanilla DOM screen router (`src/ui/router.ts`) exposes `showScreen(name, state)` over one mount node and transitions between placeholder screens, one per `CampaignStepperPhase`, each rendered inside GameUI chrome. There is no canvas, no game-engine runtime, and no UI-framework dependency; the frontend is a renderer and input shell over the browser-safe TypeScript simulation in `src/sim/`.

## Commands

```bash
npm run prepare:public   # copy shared JSON data + assets into public/
npm test                 # sim/parity unit tests (vitest)
npm run test:screens     # capture dark-fantasy Playwright baselines
npm run test:screens:check  # regression check against committed baselines
npm run build            # tsc + vite production build
npm run dev              # vite dev server
```

`prepare:public` copies shared JSON data and normalized licensed assets into `public/` for Vite. The build checks for required generated files before compiling.

## Runtime Shape

```
src/sim/        # Browser-safe resolver and stepper state machines (frozen)
src/ui/         # GameUI factory boundary + vanilla DOM screen router
src/ui/screens/ # One placeholder screen module per campaign-stepper phase
src/data.ts     # Browser data loader (fetches public/data/ JSON into GameData)
src/systems/    # Browser save/load helpers
vendor/gameui/  # Pinned, verbatim GameUI framework (tokens, dark-fantasy, components)
tests/          # Playwright screen-capture harness + dark-fantasy baselines
```

Game math and state mutation stay in `src/sim/`. The router reads stepper state through its existing public surface and re-routes to the phase the stepper returns. The simulation is renderer-agnostic and untouched by the frontend migration.
