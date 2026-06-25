<!--
---
title: "UI Layer"
description: "GameUI factory boundary and DOM screen router for the Holdfast full-DOM frontend"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [ui, design-system, frontend]
  - tech: [typescript, dom, gameui]
related_documents:
  - "[Vendored GameUI Framework](../../vendor/gameui/VENDORED.md)"
  - "[Holdfast Spec 01](../../spec/2026-06-22-holdfast-spec-01-gameui-vendor-dom-shell.md)"
---
-->

# UI Layer

The Holdfast frontend is a full-DOM consumer of the vendored GameUI framework (`vendor/gameui/`) on the dark-fantasy preset. This directory holds the typed factory boundary and the hand-rolled screen router.

| Path | Purpose |
|------|---------|
| `gameui.ts` | Single typed re-export of the vendored framework factories. All game code imports framework controls from here, never from the vendor path directly. |
| `router.ts` | Vanilla DOM screen router exposing `showScreen(name, state)` over one mount node. |
| `screens/` | One placeholder screen module per `CampaignStepperPhase`, each rendered inside GameUI chrome. |

There is no canvas and no UI-framework runtime dependency. The screen router is hand-rolled. The simulation under `src/sim/` is renderer-agnostic and stays untouched.
