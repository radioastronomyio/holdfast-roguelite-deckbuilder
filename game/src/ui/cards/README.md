<!--
---
title: "Card Renderer"
description: "Holdfast deckbuilder card component composed over the GameUI createCard primitive: JSON-driven, with five-layer mixed-source art, card backs, energy badge, effect symbols, upgrade gem, shine, and inspect"
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

The Holdfast card is a composition over the GameUI `createCard` primitive (`game/vendor/gameui/components/cards/`). It is data-driven: `createHoldfastCard(card, opts)` renders mapped `Card` records from the shared JSON without gameplay-specific branches. Adding a card requires a matching presentation row in `CARD_VISUAL_ROWS` (motif, palette, and optional art source); the exact JSON-to-presentation coverage test fails loudly when either side is missing.

| Path | Purpose |
|------|---------|
| `contract.ts` | Frozen `createHoldfastCard` options and returned-control types consumed by the combat and flow-screen specs. |
| `holdfastCard.ts` | Factory that composes the six-region frame over `createCard` and binds all real card fields without changing the public contract. |
| `cardBack.ts` | Separate `createHoldfastCardBack()` factory for face-down cards: a front-sized, token-driven, vector-only Runic field with a loaded `arcane_burst.svg` emblem from the active manifest vocabulary and no card-data or front-contract dependency. |
| `cardArt.ts` / `cardMap.ts` | Parametric inline-SVG scene composition and loud tag/effect mapping over the attributed Runic Relic-derived vocabulary. Presentation rows default to SVG motifs; Immolate alone selects its Holdfast-owned PNG inside the same SVG scene. |
| `cardBadges.ts` | Inline-SVG energy badge and `upgrade_tier` gem factories. Shine is reserved for upgraded cards. |
| `iconMap.ts` | Card-tag-to-accent precedence only; legacy PNG mappings are retired in `recycle/2026-08-10-card-icons/`. |
| `card.css` / `cards.css` | Six-region frame, SVG layers, inspect UI, and DEV gallery layout on existing GameUI tokens. |

Composition, not forking: the factory calls `createCard` for the frame and adds Holdfast-specific children to the slots it exposes. It never edits the vendored primitive. Card JSON effect values are at display scale (Arcane Strike shows 15, not 15000) and are rendered as written.

Specs 04 (combat) and 05 (flow screens) consume this component without modification: combat maps energy affordability to `setEnergyAffordable` (→ `setDisabled`) and hand selection to `onSelect`.

`createHoldfastCardBack()` is intentionally not an option on `createHoldfastCard`. It returns an accessible, face-down `article` with the distinct `.hf-card-back__pattern` and `.hf-card-back__emblem` anatomy, making hidden deck, draw-pile, and opponent-card states possible without mutating the frozen front-card API. Its chrome and patterned field are inline SVG; the central vector `<image>` loads the manifest-backed `arcane_burst.svg` rune-mode derivative. It never loads raster chrome.

The DEV gallery is the approval surface for the full contract. It renders all 21 JSON cards exactly once, a base/upgraded pair, the SVG and PNG motif paths, and a face-down card. Its Playwright gate checks the locked five-layer art order, foreground text, tall card and near-square art geometry, semantic clipping, attack-card variety axes, loaded effect/back glyphs, computed complementary back palette, and real selection behavior before capturing the 1440-wide full-height `tests/baseline/08-card-gallery.png` contact sheet.
