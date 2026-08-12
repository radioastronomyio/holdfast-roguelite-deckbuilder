# A1.1 — Layout v2 report

## Status

Implemented and committed locally as `0dfaa8182c9a1a129d8bb6ad992812a65348eb1c` (`feat(game): repair card layout hierarchy (A1.1)`).

## RED

Command:

```sh
cd game && npm test -- src/ui/cards/holdfastCard.test.ts src/ui/cards/contract.test.ts
```

Output summary:

```text
Test Files  2 failed (2)
Tests  3 failed | 22 passed (25)

contract.test.ts > keeps the frozen factory signature while exposing the v2 card anatomy
expected [] to have a length of 3 but got 0

holdfastCard.test.ts > orders the cost, centered name, and effect glyph across the header
expected header order [cost, hf-card__header-name, hf-card__header-glyph]
but received the primitive title wrapper followed by the cost tag

holdfastCard.test.ts > uses foreground text roles and a gem-plus-three-pip footer
expected .hf-card__type.hf-card__foreground not to be null
```

The failures were the expected missing A1.1 hierarchy: no glyph slot, no foreground roles, and no three-pip footer.

## GREEN

Command:

```sh
cd game && npm test -- src/ui/cards/holdfastCard.test.ts src/ui/cards/contract.test.ts
```

Output:

```text
Test Files  2 passed (2)
Tests  25 passed (25)
```

Command:

```sh
cd game && npx tsc --noEmit
```

Output: exit 0 with no diagnostics.

Additional check:

```sh
git diff --check
```

Output: exit 0 with no whitespace errors.

## Files committed

- `game/src/ui/cards/holdfastCard.test.ts`
- `game/src/ui/cards/contract.test.ts`
- `game/src/ui/cards/holdfastCard.ts`
- `game/src/ui/cards/card.css`
- `game/src/ui/cards/cards.css`
- `docs/superpowers/plans/2026-08-12-card-presentation-v2.md`

## Implementation notes

- Reordered the vendored primitive's existing header slots into cost, centered name, and top-right semantic effect glyph without changing the frozen factory API.
- Added foreground-role classes to type, rules, and stat values; the CSS role uses `var(--gui-text)`.
- Added a central upgrade gem and exactly three tier pips; filled pips represent the current upgrade tier.
- Changed the front geometry to `744 / 1200`, used a near-square art window, split type/rules regions, and rendered attack/guard as unboxed footer corners.
- Kept the existing inspect control API and keyboard/click behavior; it is visually hidden so it does not compete with the locked footer composition.

## Self-review

- The updated DOM tests exercise the real factory and would fail if the header order, foreground roles, stat/footer slots, or pip count regressed.
- `createHoldfastCard` and `HoldfastCardOptions` retain the frozen signature; no data, simulation, or vendored GameUI files changed.
- CSS uses existing `--gui-*` tokens for the new card chrome and text contrast.

## Concerns

No functional blockers. This A1.1 gate deliberately leaves the accepted-gallery visual baseline work to A1.6; no screenshot baseline was refreshed here.

## Fix Round 1 — header and footer anchoring

### Covered files

- `game/src/ui/cards/holdfastCard.test.ts`
- `game/src/ui/cards/card.css`

### RED

Command:

```sh
cd game && npm test -- src/ui/cards/holdfastCard.test.ts
```

Output:

```text
Test Files  1 failed (1)
Tests  1 failed | 23 passed (24)

createHoldfastCard rendering > uses symmetric header tracks and lower-corner footer stat anchors
expected card.css to match the equal left/right header track rule;
received `... 1fr var(--gui-space-xl)` for the right track.
```

The regression reads the authored layout rules because happy-dom does not calculate CSS grid geometry. It asserts equal header side tracks, the glyph's end anchor, and explicit lower/start and lower/end anchors for attack and guard.

### GREEN

Commands:

```sh
cd game && npm test -- src/ui/cards/holdfastCard.test.ts
cd game && npx tsc --noEmit
git diff --check
```

Output:

```text
Test Files  1 passed (1)
Tests  24 passed (24)

npx tsc --noEmit: exit 0, no diagnostics
git diff --check: exit 0, no whitespace errors
```

### Change

- Made the header's outer grid tracks identical: `calc(var(--gui-space-xl) + var(--gui-space-sm))` on both sides of the centered title.
- Anchored the glyph to the end of the equal right track.
- Anchored `.hf-card__attack` at the footer's lower/start corner and `.hf-card__guard` at its lower/end corner, retaining the grid footer's bottom alignment.

### Commit

`a27269755b0a9aacb9dd10a06f9857e8cc26718b` — `fix(game): anchor card header and stats (A1.1)`.
