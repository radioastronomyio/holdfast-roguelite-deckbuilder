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

## Fix Round 1 — validate Runic icon semantics

### RED

Command:

```sh
cd game && npm test -- src/ui/cards/cardMap.test.ts src/ui/cards/cardArt.test.ts src/ui/cards/holdfastCard.test.ts src/ui/cards/cardAssetHygiene.test.ts scripts/derive-runic-card-icons.test.ts
```

Observed result: 2 test files failed, with 4 failed and 37 passed tests.

- `RUNIC_ICON_MODES` did not exist, so both card motifs and semantic tag/stat
  selections had no executable mode contract.
- The manifest-backed inventory could not be compared to a committed literal
  mode inventory.
- The initial active-tree hygiene test identified its own unsplit retired pack
  wording; this was corrected before GREEN by constructing the prohibited
  tokens and scanning the entire active `src/`, `scripts/`, and `assets/`
  trees. Recycle and Git history are outside that scan.

The upgrade-tree fixture loaded 90 `added_effects`; all were exercised during
RED and happened to resolve through existing companion tags. The strengthened
GREEN mapping adds explicit entries for upgrade-only semantics (`bleed`,
`party`, `regen`, `stun`, and `weaken`) so those tags also have standalone
mode-backed meanings.

The derivation regression was moved under `src/` after RED because the Vitest
configuration intentionally collects tests from `src/`, not `scripts/`.

### GREEN

Focused command:

```sh
cd game && npm test -- src/ui/cards/cardMap.test.ts src/ui/cards/cardArt.test.ts src/ui/cards/holdfastCard.test.ts src/ui/cards/cardAssetHygiene.test.ts src/ui/cards/cardAssetDerivation.test.ts
```

Result: 5 files passed, 42 tests passed.

Derivation, staging, public validation, full suite, and build:

```sh
cd game && node scripts/derive-runic-card-icons.mjs /opt/agents/repos/html5-game-ui-framework/reference-files-ui/runic-relic-rpg-icons-144
cd game && npm run prepare:public
cd game && npm run check:public
cd game && npm test
cd game && npm run build
```

Results:

- Derivation regenerated exactly 22 SVGs.
- Public staging and checks passed.
- Full game suite: 21 files passed, 92 tests passed.
- Production build passed (`tsc -p tsconfig.json && vite build`).

### Changes

- Added a literal, exhaustive `RUNIC_ICON_MODES` inventory matching the
  committed derived manifest exactly.
- Every card-subtype motif, effect tag, and tagless stat fallback now calls a
  runtime mode guard. A selected asset with the wrong expected Runic mode
  throws during mapping initialization.
- Tests independently lock the meaningful tag/stat modes and exact manifest
  modes, so nonsense metadata or a wrong-mode symbol fails.
- Modifier coverage now includes all 90 `added_effects` across every branch in
  `data/cards/upgrade-trees.json`, in addition to base and hazard effects.
- Added an active-tree stale-reference regression for retired source names and
  URLs, excluding the separate `recycle/` archive and repository history by
  scope.
- The derivation script now refuses unexpected files in its output inventory,
  overwrites only exact known outputs, and accepts an isolated output path for
  its regression test. It never recursively deletes the asset directory.

### Concerns

None.

## Fix Round 2 — hermetic card asset guards

### RED

Command:

```sh
cd game && npm test -- src/ui/cards/cardAssetHygiene.test.ts src/ui/cards/cardAssetDerivation.test.ts src/ui/cards/cardMap.test.ts
```

Observed result: the new hygiene suite failed to load the wished-for
`findStaleCardAssetReferences` scanner; the other 2 files passed with 14 tests.
This was the expected failure proving the active-tree scanning contract did not
yet exist. The rewritten derivation test was already GREEN against the existing
configurable source/output arguments, confirming no production script change
was needed to remove its external test dependency.

### GREEN

Focused command:

```sh
cd game && npm test -- src/ui/cards/cardAssetHygiene.test.ts src/ui/cards/cardAssetDerivation.test.ts src/ui/cards/cardMap.test.ts
```

Result: 3 files passed, 16 tests passed.

Full verification:

```sh
cd game && npm test
cd game && npm run build
```

Results:

- Full game suite: 21 files passed, 93 tests passed.
- Production build passed, including `check:public`, TypeScript, and Vite.

### Changes

- Added a reusable active-tree scanner over `game/src/`, `game/scripts/`,
  `game/assets/`, and `game/tests/`.
- The scanner includes Python harnesses such as `tests/capture.py`, while
  excluding `tests/baseline/`, `__pycache__/`, and non-text binaries by explicit
  directory and extension rules. Recycle and Git history remain out of scope.
- A temporary-game regression proves a restored `/assets/card-art-icons/` URL
  in `tests/capture.py` is returned as stale.
- The derivation regression now builds a complete minimal Runic manifest and
  tiny source SVG set beneath `mkdtemp`, invokes the script with that fixture,
  proves palette derivation, and proves stale-output rejection.
- The hermetic test contains no external reference-pack path and removes its
  entire temporary fixture in `finally`, on both success and failure.

### Concerns

None.
