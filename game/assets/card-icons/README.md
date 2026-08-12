<!--
---
title: "Holdfast Runic Card Icons"
description: "Holdfast-owned SVG derivatives of the Runic Relic RPG Icons 144 vocabulary"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-12"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [ui, game-dev, card-game, assets]
  - tech: [svg, png]
related_documents:
  - "[License Notice](NOTICE)"
  - "[Derived Asset Manifest](manifest.json)"
  - "[Card Renderer](../../src/ui/cards/README.md)"
---
-->

# Holdfast Runic Card Icons

This directory contains the self-coloured SVG vocabulary used by Holdfast card
art and modifier rows. Each file is a palette-derived adaptation of one Runic
Relic RPG Icons 144 source file, not a byte-identical copy. The exact source ID,
mode, path, and output filename are recorded in `manifest.json`.

Regenerate the derivatives from an authorized local copy of the reference pack:

```bash
node game/scripts/derive-runic-card-icons.mjs /path/to/runic-relic-rpg-icons-144
```

The SVGs render as external image assets because the source artwork contains
its own multicolour gradients. A1.4 adds one Holdfast-owned PNG motif,
`immolate-fireball.png`, selected only by the Immolate presentation row inside
the otherwise inline-SVG art scene. It is not used for card chrome, badges,
upgrade gems, pips, or effect glyphs.
