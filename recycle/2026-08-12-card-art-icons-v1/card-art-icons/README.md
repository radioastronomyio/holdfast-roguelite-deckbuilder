<!--
---
title: "Holdfast Card Art Icons"
description: "Curated, attributed, zero-raster Game-icons symbols used by the parametric Holdfast card renderer"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-08-10"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [ui, game-dev, card-game, assets]
  - tech: [svg, game-icons]
related_documents:
  - "[Attribution](NOTICE)"
  - "[Card Renderer](../../src/ui/cards/README.md)"
---
-->

# Card Art Icons

This directory contains the 14-symbol SVG vocabulary used by Holdfast card art
and modifier rows. Every glyph is by Lorc from Game-icons under CC BY 3.0; see
`NOTICE` for the exact source revision, filenames, license, and transformations.

Each file is an external SVG sprite with a single `<symbol id="icon">`. The
renderer references it with `<use href="...svg#icon">`; foreground paths use
`currentColor`, so the symbol inherits the card's semantic accent. There are no
raster files in this path.
