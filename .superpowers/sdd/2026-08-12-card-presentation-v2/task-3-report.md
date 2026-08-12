# A1.3 — Runic Relic derived vocabulary report

## Status

Implemented on the active card-presentation branch from base `af7b45c`. The
five-layer A1.2 scene and frozen `createHoldfastCard` contract remain intact.

## RED

Command:

```sh
cd game && npm test -- src/ui/cards/cardMap.test.ts src/ui/cards/cardArt.test.ts src/ui/cards/holdfastCard.test.ts
```

Observed result before implementation: 3 test files failed, with 9 failed and
30 passed tests.

- Card identity rows still returned the former Game-icons vocabulary.
- Unknown non-empty tags on a known HP stat incorrectly used the stat fallback.
- The Runic URL builder and derived asset inventory did not exist.
- Art, header, and effect nodes still emitted external `<use>` sprite links
  under `/assets/card-art-icons/` rather than self-coloured Runic SVG images.

The failures matched the missing A1.3 behavior. The later full-suite run also
found the gallery integration assertion still requiring the retired `<use>`
shape; that assertion was updated to exercise the new real image URL boundary.

## GREEN

Focused command after implementation:

```sh
cd game && npm run prepare:public
cd game && npm test -- src/ui/cards/cardMap.test.ts src/ui/cards/cardArt.test.ts src/ui/cards/holdfastCard.test.ts
cd game && npm run check:public
```

Results: public staging passed, 3 test files passed with 39 tests, and the
public asset check passed.

Full verification:

```sh
cd game && npm test
cd game && npm run build
cd game && npm run test:screens:build
```

Results:

- Full game suite: 19 files passed, 89 tests passed.
- Production build: passed (`tsc -p tsconfig.json && vite build`).
- Built-output screen gate: passed; Runic probe returned HTTP 200 with
  `image/svg+xml`, zero failed requests, and zero non-origin requests.

Additional acceptance checks:

- All 22 derived SVGs differ byte-for-byte from their manifest-listed Runic
  source files.
- No stale `card-art-icons`, `cardArtIconUrl`, or Game-icons source/runtime
  references remain under `game/` (generated `public/` and `dist/` excluded).
- No PNG files ship in `game/assets/card-icons/` for A1.3.
- `git diff --check` passed; `data/` and `simulation/` are unchanged.

## Delivered behavior

- Card-specific motifs and effect tags now resolve to exact Runic Relic IDs.
- A known-stat fallback is available only for modifiers with zero tags;
  unknown non-empty tag sets throw with stat and tag context.
- `cardIconUrl(name, format)` creates stable `/assets/card-icons/<name>.<format>`
  URLs for current SVGs and the future A1.4 PNG path.
- The five-layer card art keeps sky, glow, motif, ground, and vignette in its
  sealed order. Its motif is now a self-coloured SVG `<image>`; compact header
  and effect glyphs are `<img>` elements using the same derived vocabulary.
- `prepare:public`, `check:public`, and the production capture probe stage and
  validate the new asset family and provenance files.
- The prior tracked Game-icons tree was moved intact to
  `recycle/2026-08-12-card-art-icons-v1/` with a retirement note.

## Derived asset manifest

The committed `game/assets/card-icons/manifest.json` is authoritative. The
selected source IDs and modes are:

| ID | Mode | Holdfast use |
|---|---|---|
| `arcane_burst` | rune | arcane/control/buff motif |
| `barrier_spell` | barrier | defense motif/effect |
| `black_bomb` | bomb | acid flask motif |
| `crescent_blade` | sword | physical attack motif/effect |
| `fireball` | flame | fire motif/effect |
| `frostbite` | frost | ice/cold motif/effect |
| `healing_light` | heart | heal effect/tagless HP fallback |
| `health_potion` | potion | heal potion motif |
| `holy_ray` | sun | cleanse/blind vocabulary |
| `life_drain` | skull | dark/lifesteal motif/effect |
| `mana_orb` | gem | energy/utility motif/effect |
| `poison_cloud` | poison | poison/shred motif/effect |
| `rage_surge` | claw | power motif/effect |
| `root_snare` | root | trap/control motif/effect |
| `rune_hammer` | hammer | pressure motif/effect |
| `stone_spike` | earth | stone wall motif |
| `swift_boots` | boots | speed/slow motif/effect |
| `thunder_arc` | bolt | lightning motif/effect |
| `tidal_surge` | wave | miasma/AoE motif/effect |
| `tower_shield` | shield | shield bash motif |
| `warning` | warning | hazard/debuff/blinding hazard motif |
| `wind_cut` | wind | freezing wind motif |

The deterministic derivation command was:

```sh
node game/scripts/derive-runic-card-icons.mjs /opt/agents/repos/html5-game-ui-framework/reference-files-ui/runic-relic-rpg-icons-144
```

It applies the Holdfast dark-fantasy palette, embeds source ID/mode metadata,
and writes the source-to-output manifest. `NOTICE` records Template Foundry,
the Runic Relic RPG Icons 144 pack/version, purchaser license facts, and the
prohibition on redistributing the raw pack.

## Concerns

No functional blocker. A1.4 will add the first PNG exemplar; this task
deliberately keeps the vocabulary SVG-only.
