<!--
---
title: "Vendored GameUI Framework"
description: "Provenance and refresh procedure for the pinned GameUI framework copy consumed by Holdfast"
author: "VintageDon (https://github.com/vintagedon/)"
date: "2026-06-22"
version: "1.0"
status: "Active"
tags:
  - type: directory-readme
  - domain: [design-system, vendoring, dependencies]
  - tech: [css, javascript]
related_documents:
  - "[Framework Source Layer](https://github.com/vintagedon/gameui-browser-gaming-framework)"
  - "[Holdfast Spec 01: GameUI Vendor + Full-DOM Shell](/opt/agents/repos/spec/2026-06/2026-06-22-holdfast-spec-01-gameui-vendor-dom-shell.md)"
---
-->

# Vendored GameUI Framework

Holdfast is a full-DOM consumer of the [GameUI](https://github.com/vintagedon/gameui-browser-gaming-framework) zero-build-step UI framework on the dark-fantasy preset. This directory is a pinned, verbatim copy of the framework's consumable `ui/` tree. It is the **only** runtime dependency Holdfast has on the framework; the game never references the framework repository by path at runtime. To retheme Holdfast, swap the preset `<link>` in `index.html` (see `themes/`).

## Provenance

| Field | Value |
|-------|-------|
| Source repository | `https://github.com/vintagedon/gameui-browser-gaming-framework` |
| Source path (at copy time) | `/opt/agents/repos/gameui-browser-gaming-framework/ui/` |
| Framework version | 1.0 (from `ui/README.md` frontmatter, dated 2026-06-21) |
| Copy date | 2026-06-22 |
| Vendored by | Holdfast Spec 01 — GameUI Vendor + Full-DOM Shell |

## What was copied

A verbatim copy of the framework's consumable layers (structure + skin + contract):

| Tree | Purpose |
|------|---------|
| `tokens/` | The token contract (`tokens.css`) — semantic custom properties binding structure to skin |
| `themes/` | Presets: `dark-fantasy.css` (active in Holdfast), `neon.css`, plus `themes/fonts/` (self-hosted OFL Cinzel/MedievalSharp) and `themes/dark-fantasy-assets/` (webp textures) so a one-link preset swap works |
| `components/` | All 12 component families — structure CSS plus JS factories where interactive |
| `FRAMEWORK-README.md` | The framework's own `ui/README.md`, retained for load-order, factory, and theme-authoring reference |

The framework's own `gallery/` and `tests/` directories are its validation/demo harness, not runtime consumables, and are intentionally **not** vendored. Copying them would add the framework's gallery styles (explicitly "not component skin") and its Playwright baseline PNGs to Holdfast's tree.

Co-located `.d.ts` declarations sit next to each interactive family's `.js` so Holdfast's TypeScript resolves types through `src/ui/gameui.ts`, the single re-export boundary.

## Wiring (load order)

`index.html` loads, in this order: `vendor/gameui/tokens/tokens.css` → `vendor/gameui/themes/dark-fantasy.css` → the component CSS families Holdfast uses → game CSS. The JS factories are imported from TypeScript under `src/ui/` through the `gameui.ts` boundary. See the framework README §4 (Consumption) and §6 (Factory Pattern).

## Refresh procedure

When upgrading the pinned framework version:

1. Re-copy `tokens/`, `themes/`, `components/`, and `FRAMEWORK-README.md` from the updated source `ui/` tree over this directory. Use `cp -r` (verbatim); do not hand-merge. Preserve the co-located `.d.ts` declarations (re-author them only if a factory's public surface changed).
2. Update the version and copy-date rows in the table above from the source `ui/README.md` frontmatter.
3. Re-run the Holdfast Playwright capture harness (`python game/tests/capture.py`) and review the baseline diffs under `game/tests/baseline/`. A framework change that alters component rendering will move the baselines; confirm the diff is intentional.
4. Run `npx tsc --noEmit` and `npm run build` to confirm the factory imports and token references still resolve.
5. Commit the refreshed tree and new baselines together on a feature branch.
