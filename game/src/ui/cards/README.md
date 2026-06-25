<!--
---
title: "Card Renderer"
description: "Holdfast deckbuilder card component composed over the GameUI createCard primitive: JSON-driven, with energy badge, effect icons, accent tint, upgrade pips, shine, and inspect"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [ui, design-system, card-game]
  - tech: [typescript, dom, gameui, css]
related_documents:
  - "[Holdfast Spec 02](../../spec/2026-06-22-holdfast-spec-02-card-renderer.md)"
  - "[GameUI Factory Bridge](../gameui.ts)"
  - "[Card Gallery Screen](../screens/card-gallery.ts)"
---
-->

# Card Renderer

The Holdfast card is a composition over the GameUI `createCard` primitive (`game/vendor/gameui/components/cards/`). It is data-driven: `createHoldfastCard(card, opts)` renders any `Card` from the shared JSON with no per-card hardcoding. Adding a card to the JSON is the only step required to render a new card.

| Path | Purpose |
|------|---------|
| `holdfastCard.ts` | `createHoldfastCard(card, opts)` factory: name + energy-cost badge (via the createCard tag slot), one effect row per modifier (icon + operation-aware signed value + target), upgrade-tier pips, a rare/upgraded shine overlay, and an inspect affordance that opens a detail modal. Passes `selectable`/`selected`/`disabled`/`onClick`/`onSelect` straight through to `createCard`. |
| `iconMap.ts` | Tag→icon and card-tag→accent resolution maps with documented precedence and fallbacks. The single source of truth for which icons and accents the renderer depends on. |
| `cards.css` | Holdfast-specific card composition (energy badge, effect rows, pips, shine) and the DEV card-gallery layout, on GameUI tokens. Structure-only; the primitive's frame and selection ring are untouched. |

Composition, not forking: the factory calls `createCard` for the frame and adds Holdfast-specific children to the slots it exposes. It never edits the vendored primitive. Card JSON effect values are at display scale (Arcane Strike shows 15, not 15000) and are rendered as written.

Specs 03 (combat hand) and 04 (reward/world-deck choices) consume this component without modification: combat maps energy affordability to `setEnergyAffordable` (→ `setDisabled`) and hand selection to `onSelect`.
