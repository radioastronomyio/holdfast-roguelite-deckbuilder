<!--
---
title: "Card Icon Source"
description: "In-repo source copy of the curated neor-rpg-icon-pack subset the Holdfast card renderer depends on, staged into public/assets/icons/ by prepare-public.mjs so the build is hermetic on any host"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [assets, build, design-system]
  - tech: [png]
related_documents:
  - "[Holdfast Spec 03: Asset Foundation and Build-Output Correctness](../../spec/2026-06-22-holdfast-spec-03-asset-foundation-build-correctness.md)"
  - "[prepare-public.mjs](../../scripts/prepare-public.mjs)"
  - "[Card Renderer iconMap](../../src/ui/cards/iconMap.ts)"
---
-->

# Card Icon Source

The normalized, in-repo copy of the curated RPG icon subset the Holdfast card renderer resolves through `iconMap.ts`. This directory is the single source `prepare-public.mjs` reads card icons from; it stages them verbatim into `public/assets/icons/` (gitignored, generated) for the dev server and the production build.

## Why this exists

Before spec 03, `prepare-public.mjs` read these icons from an out-of-repo absolute path (`/opt/agents/repos/retro-gaming-html5/.../neor-rpg-icon-pack`) and applied filename normalization at staging time (collapsing the pack's doubled `.png.png` extension and the `ui-watrer-drop` typo). That made the build non-hermetic: a fresh clone on any host without that pack could not build. Spec 03 vendored the curated subset in-repo under the clean kebab names the renderer already expects, so staging is a straight file copy with no out-of-repo dependency and no normalization step.

## Provenance

Subset of the `neor-rpg-icon-pack` (armors, items, magics, spells, UI symbols), curated to exactly the icons `iconMap.ts` resolves — one per effect tag, stat fallback, and the default. Filenames are the clean destination names the previous staging step produced, so the staged output in `public/assets/icons/` is byte-for-byte identical to before spec 03.

## The dependency contract

The manifest of which icons the renderer depends on lives in `prepare-public.mjs` (`stageCardIcons`'s `icons` list), not here. Adding a tag to `iconMap.ts` means adding its filename both there and dropping the source file into this directory. `check-public.mjs` guards a representative icon (`icon-attack.png`) at prebuild time, and the build-output harness probes it from the preview server.
