<!--
---
title: "Game Assets"
description: "In-repo asset sources consumed by the build (currently the curated card-icon subset); the public/ tree is generated from these by prepare-public.mjs"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [assets, build]
---
-->

# Game Assets

In-repo source assets that `prepare-public.mjs` stages into the generated `public/` tree (gitignored) for both the dev server and the production build.

| Path | Purpose |
|------|---------|
| `card-icons/` | Curated `neor-rpg-icon-pack` subset the card renderer resolves via `iconMap.ts`; staged to `public/assets/icons/`. See its README. |

The `public/` tree (`public/assets/`, `public/vendor/`) is generated and gitignored; this directory holds the committed sources.
