# A1.2 — Five-layer card art report

## Status

Implemented on the active card-presentation branch. The required local commit is recorded below.

## RED

Command:

```sh
cd game && npm test -- --run src/ui/cards/cardArt.test.ts src/ui/cards/cardMap.test.ts
```

Observed result before the implementation: 2 test files failed, with 5 failed and 3 passed tests.

- The new card-aware `resolveCardVisual(card)` tests failed with `tags.includes is not a function`, proving the prior resolver accepted only tag arrays.
- The locked layer-order test found the old four art layers and no `.hf-card-art__glow` or `.hf-card-art__motif` layer.
- The motif binding test could not find the renamed `.hf-card-art__motif` element.

These failures matched the missing A1.2 behavior. A test-only matcher correction (`Set#size` and SVG `class` attribute access) was required after the initial RED run; it did not alter production behavior.

## GREEN and verification

Focused tests:

```sh
cd game && npm test -- --run src/ui/cards/cardArt.test.ts src/ui/cards/cardMap.test.ts
```

Result: 2 files passed, 8 tests passed.

Full card subset and production build:

```sh
cd game && npm test -- --run src/ui/cards
cd game && npm run build
git diff --check
git diff --quiet -- data
```

Results:

- Card subset: 6 files passed, 48 tests passed.
- Production build: passed (`tsc -p tsconfig.json && vite build`), including `check:public`.
- `git diff --check`: passed with no whitespace errors.
- `git diff --quiet -- data`: passed: no shared data definitions changed.

## Delivered behavior

- `resolveCardVisual` now takes the card identity plus tags. Its motif and palette come from strict rows for all 21 real cards; its ground category is derived only from the existing tag set.
- Arcane Strike, Immolate, and Shield Bash have distinct palette, ground, and motif values: magic/arcane/swirl, danger/ash/fireball, and info/stone/shield, respectively.
- `createCardArt` emits scene children in the locked paint order: sky, glow, motif, ground, vignette. The new radial glow is the second painted layer.
- Seven tag-derived ground categories select distinct SVG silhouettes. Card chrome stays neutral; color variables are scoped to the art viewport.
- The `createHoldfastCard` call sites now pass the real card to the visual resolver. The frozen public card factory contract and `data/` remain unchanged.

## Commit

`c7785f8eab1a9ab00a90c79443f9a22283e01252` — `feat(game): lock five-layer card art (A1.2)`

## Concerns

No functional blockers. A1.3 will replace the temporary existing icon vocabulary as planned; this task deliberately retains it.

## Fix Round 1 — enforce total visual rows

### RED

Command:

```sh
cd game && npm test -- --run src/ui/cards/cardArt.test.ts src/ui/cards/cardMap.test.ts
```

Output summary: 2 test files ran; 2 tests failed and 8 passed.

- `CARD_VISUAL_IDS is not iterable`: the stable explicit-ID inventory did not yet exist.
- `expected [Function] to throw an error`: `resolveCardVisual` still selected a tag-derived generic fallback for an unknown card ID.

The strengthened direct-child layer assertion already passed against the current SVG tree: it excludes only `<defs>`, so any additional painted direct child (including a classless child) would appear in the received sequence and fail the exact five-layer assertion.

### GREEN and verification

Commands:

```sh
cd game && npm test -- --run src/ui/cards/cardArt.test.ts src/ui/cards/cardMap.test.ts
cd game && npm test -- --run src/ui/cards
cd game && npx tsc --noEmit
cd game && npm run build
git diff --check
git diff --quiet -- data
```

Results:

- Focused tests: 2 files passed, 10 tests passed.
- Full card subset: 6 files passed, 50 tests passed.
- TypeScript check: exit 0 with no diagnostics.
- Production build: passed, including `check:public`.
- Whitespace check and data immutability check: both exit 0.

### Change

- Removed the generic tag motif/palette fallback; `CARD_VISUAL_ROWS` is now the only source of a card's motif and palette.
- Exported frozen `CARD_VISUAL_IDS`; the JSON-backed test checks exact two-way coverage of all 21 current card IDs.
- Unknown IDs now throw `Unmapped card visual: id=<id>` before ground resolution.
- The art-layer lock now removes only the non-painted `<defs>` direct child, then asserts every remaining direct render child in exact order.

### Commit

`af7b45c1b33762977d9939fa1496701d9dbe35a3` — `fix(game): enforce total card art mapping (A1.2)`
