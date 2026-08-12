# Task 5 report — A1.5 parametric card backs

## Scope delivered

- Added `createHoldfastCardBack(): HTMLElement` in `game/src/ui/cards/cardBack.ts`.
- The factory creates a face-down `article` with `.hf-card-back` and the
  complementary `.hf-card-back--magic` palette class. It preserves the front
  card's `--hf-card-width` and `744 / 1200` physical ratio without adding any
  option to the frozen `createHoldfastCard` contract.
- The back is accessible as `role="img"` with the front-distinct label
  `Holdfast card back`.
- Added the required `.hf-card-back__pattern` SVG field and a centered
  `.hf-card-back__emblem`. The pattern/chrome are inline geometry and the
  final emblem loads the manifest-backed vector `arcane_burst.svg`; no raster
  asset is loaded by the back.
- The repeated rune-pattern ID is unique per factory call, so several hidden
  cards can coexist in one deck without fragment-reference collisions.
- Added complementary token-only card-back CSS and documented the separate
  factory in the cards README.

## TDD evidence

### RED

1. Before `cardBack.ts` existed, `npm test -- src/ui/cards/cardBack.test.ts`
   failed at Vite import resolution for the missing `./cardBack` module.
2. After the first GREEN implementation, the added repeated-pattern test
   failed as expected: `hf-card-back-runes` did not match the required unique
   `hf-card-back-runes-<id>` reference.

### GREEN

- The focused `cardBack.test.ts` passed 2 tests after implementing the
  standalone SVG factory and unique pattern IDs.

## Final verification

- `npm test -- src/ui/cards` — 65 tests passed across 9 files
- `npx tsc -p tsconfig.json --noEmit` — passed
- `npm test` — 99 tests passed across 22 files
- `npm run build` — passed (`check:public`, TypeScript, Vite)
- `npm run test:screens:build` — passed: six screen checks, skin/assets,
  zero failed requests, zero non-origin requests

## Concerns

No open implementation concerns. The card back is deliberately standalone and
is not mounted by a screen yet; its consumer belongs to the subsequent combat
and flow-screen work.

## Whole-branch review correction

The initial inline emblem was structurally vector-only but did not actually use
the active Runic asset vocabulary. The final review fix keeps the inline
pattern/chrome and standalone accessible factory, but replaces the self-authored
central rune with an external vector `<image>` bound to the manifest-backed
`arcane_burst.svg` (`rune` mode). Unit and browser gates assert the exact URL
and mode, reject PNG use on the back, verify the asset loads, and compare the
computed back palette against a front card.
