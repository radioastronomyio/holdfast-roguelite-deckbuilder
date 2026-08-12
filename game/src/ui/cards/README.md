<!--
---
title: "Card Renderer"
description: "Holdfast deckbuilder card component composed over the GameUI createCard primitive: JSON-driven, with SVG art, energy badge, effect symbols, upgrade gem, shine, and inspect"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [ui, design-system, card-game]
  - tech: [typescript, dom, gameui, css]
related_documents:
  - "[Holdfast Spec 06](/opt/agents/repos/spec/2026-08/2026-08-10-holdfast-spec-06-card-system-rewrite.md)"
  - "[GameUI Factory Bridge](../gameui.ts)"
  - "[Card Gallery Screen](../screens/card-gallery.ts)"
---
-->

# Card Renderer

The Holdfast card is a composition over the GameUI `createCard` primitive (`game/vendor/gameui/components/cards/`). It is data-driven: `createHoldfastCard(card, opts)` renders any `Card` from the shared JSON with no per-card hardcoding. Adding a card to the JSON is the only step required to render a new card.

| Path | Purpose |
|------|---------|
| `contract.ts` | Frozen `createHoldfastCard` options and returned-control types consumed by the combat and flow-screen specs. |
| `holdfastCard.ts` | Factory that composes the six-region frame over `createCard` and binds all real card fields without changing the public contract. |
| `cardArt.ts` / `cardMap.ts` | Parametric inline-SVG scene composition and loud tag/effect-to-image mapping over the attributed Runic Relic-derived vocabulary. |
| `cardBadges.ts` | Inline-SVG energy badge and `upgrade_tier` gem factories. Shine is reserved for upgraded cards. |
| `iconMap.ts` | Card-tag-to-accent precedence only; legacy PNG mappings are retired in `recycle/2026-08-10-card-icons/`. |
| `card.css` / `cards.css` | Six-region frame, SVG layers, inspect UI, and DEV gallery layout on existing GameUI tokens. |

Composition, not forking: the factory calls `createCard` for the frame and adds Holdfast-specific children to the slots it exposes. It never edits the vendored primitive. Card JSON effect values are at display scale (Arcane Strike shows 15, not 15000) and are rendered as written.

Specs 04 (combat) and 05 (flow screens) consume this component without modification: combat maps energy affordability to `setEnergyAffordable` (→ `setDisabled`) and hand selection to `onSelect`.
