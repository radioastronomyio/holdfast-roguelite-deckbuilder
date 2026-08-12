# Holdfast Card Presentation v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repair the rejected spec-06 card presentation with the approved tall deckbuilder layout, Runic Relic-derived art, pluggable SVG/PNG motifs, card backs, and a renewed full-gallery approval surface without changing the frozen `createHoldfastCard` contract.

**Architecture:** `createHoldfastCard` remains the only front-card adapter over vendored `createCard`. A strict presentation map keyed by card ID selects semantic palette, ground, motif, glyph, and optional image source; `cardArt.ts` renders the same sky/glow/motif/ground/vignette scene for SVG and PNG motifs. `cardBack.ts` owns the additive back face, while Playwright checks real computed styles and geometry at 1440px width and captures the complete gallery as a full-height contact sheet.

**Tech Stack:** TypeScript 5.9, vanilla DOM, inline SVG, Vite 6, Vitest/happy-dom, Python Playwright with Chromium headless.

## Global Constraints

- Preserve `createHoldfastCard(card: Card, opts?: HoldfastCardOptions): HoldfastCardControl` and every existing option/control member exactly; specs 04 and 05 must compile without new arguments.
- Use existing `--gui-*` tokens for chrome, badge, gem, text, spacing, radius, shadow, and motion roles; add no hue-named or domain-named tokens.
- Card chrome, cost badges, upgrade gems, and card backs remain zero-raster. The art motif source may be a derived SVG or PNG selected only by the presentation map.
- Derive assets from Runic Relic RPG Icons 144 into Holdfast-owned assets; never ship the raw reference tree. Keep the required license notice.
- `simulation/**`, `data/**`, and vendored GameUI component/token files are read-only.
- Unknown effect semantics fail loudly. A known stat fallback is permitted only when an effect has no tags; unknown non-empty tags must throw.
- Use test-first red/green cycles for behavior changes. One local, unpushed commit per A1 gate with ML01 trailers.

---

### Task 1: A1.1 — Layout v2

**Files:**
- Modify: `game/src/ui/cards/holdfastCard.test.ts`
- Modify: `game/src/ui/cards/contract.test.ts`
- Modify: `game/src/ui/cards/holdfastCard.ts`
- Modify: `game/src/ui/cards/card.css`
- Modify: `game/src/ui/cards/cards.css`
- Include: `docs/superpowers/plans/2026-08-12-card-presentation-v2.md`

**Interfaces:**
- Consumes: frozen `CreateHoldfastCard`, `createCostBadge`, `createUpgradeGem`.
- Produces: header glyph slot `.hf-card__header-glyph`, foreground text roles, bottom footer with `.hf-card__pips`, and tall front geometry used by later tasks.

- [x] Add tests requiring the cost/name/glyph header order, foreground classes for type/rules/stat values, attack/guard plus tier gem and three pips, and absence of the v1 header emblem/overlaid text.
- [x] Run `npm test -- src/ui/cards/holdfastCard.test.ts src/ui/cards/contract.test.ts` and record the expected failures.
- [x] Recompose the DOM and CSS to match the target: centered name, top-right effect glyph, near-square art region, separate type/rules rows, bottom-corner stats, central gem/pips, aspect ratio `744 / 1200` (~0.62), and high-contrast stat values using `var(--gui-text)`.
- [x] Run the focused tests and `npx tsc --noEmit`; both must pass.
- [x] Commit as `feat(game): repair card layout hierarchy (A1.1)` with the required trailers.

### Task 2: A1.2 — Five-layer art and variety axes

**Files:**
- Modify: `game/src/ui/cards/cardArt.test.ts`
- Modify: `game/src/ui/cards/cardMap.test.ts`
- Modify: `game/src/ui/cards/cardArt.ts`
- Modify: `game/src/ui/cards/cardMap.ts`
- Modify: `game/src/ui/cards/card.css`

**Interfaces:**
- Produces: `CardVisual` with a card-ID-selected motif/palette and tag-derived `ground`; `createCardArt` emits `.hf-card-art__sky`, `__glow`, `__motif`, `__ground`, `__vignette` in that order.

- [x] Add tests that every JSON card resolves, every art tree has exactly the locked five layer classes in order, and Arcane Strike/Immolate/Shield Bash differ in palette, ground, and motif while `data/` remains unchanged.
- [x] Run the two focused test files and record the expected failures.
- [x] Implement strict per-card visual rows and category ground paths derived from existing tags; add the radial glow as the second layer and keep the colored art band isolated from neutral card chrome.
- [x] Run focused tests and the full card test subset.
- [x] Commit as `feat(game): lock five-layer card art (A1.2)` with trailers.

### Task 3: A1.3 — Runic Relic derived vocabulary

**Files:**
- Replace directory contents: `game/assets/card-art-icons/` with `game/assets/card-icons/`
- Modify: `game/scripts/prepare-public.mjs`
- Modify: `game/scripts/check-public.mjs`
- Modify: `game/src/ui/cards/cardMap.ts`
- Modify: `game/src/ui/cards/cardMap.test.ts`
- Modify: `game/src/ui/cards/cardArt.ts`
- Modify: `game/src/ui/cards/holdfastCard.test.ts`
- Modify: `game/tests/capture.py`

**Interfaces:**
- Produces: derived SVG files with stable Holdfast names, `cardIconUrl(name, format)` URLs, and Runic modes covering motif and effect semantics.

- [x] Add tests for every real modifier, unknown non-empty tags on a known stat throwing, no stale Game-icons URLs, and required NOTICE/source files.
- [x] Run focused tests and record the expected failures.
- [x] Derive/recolour the selected Runic Relic assets into Holdfast-owned SVGs, replace NOTICE/README, update staging/build probes, and map all card/effect semantics using manifest modes.
- [x] Run `npm run prepare:public`, focused tests, `npm run check:public`, and verify source derivatives differ byte-for-byte from reference files.
- [x] Commit as `feat(game): derive Runic Relic card icons (A1.3)` with trailers.

### Task 4: A1.4 — Pluggable SVG/PNG art source

**Files:**
- Modify: `game/src/ui/cards/cardMap.ts`
- Modify: `game/src/ui/cards/cardMap.test.ts`
- Modify: `game/src/ui/cards/cardArt.ts`
- Modify: `game/src/ui/cards/cardArt.test.ts`
- Modify: `game/src/ui/cards/card.css`
- Add: one derived PNG under `game/assets/card-icons/`
- Modify: `game/scripts/check-public.mjs`

**Interfaces:**
- `CardVisual.artSource` is presentation-only and defaults to `"svg"`; `createCardArt` accepts it without changing `HoldfastCardOptions`.

- [x] Add tests proving an unflagged card uses an SVG motif node, Immolate's presentation row opts into an `<image>` PNG motif, and no JSON or public factory option carries the flag.
- [x] Run focused tests and record the expected failures.
- [x] Add the art-source branch inside the shared five-layer scene, derive the PNG exemplar, and preserve vector-only chrome.
- [x] Run focused tests, contract typecheck, and public-asset checks.
- [x] Commit as `feat(game): support pluggable card art sources (A1.4)` with trailers.

### Task 5: A1.5 — Card backs

**Files:**
- Add: `game/src/ui/cards/cardBack.ts`
- Add: `game/src/ui/cards/cardBack.test.ts`
- Modify: `game/src/ui/cards/card.css`
- Modify: `game/src/ui/cards/README.md`

**Interfaces:**
- Produces: `createHoldfastCardBack(): HTMLElement`, a token-driven zero-raster back with `.hf-card-back__pattern` and `.hf-card-back__emblem`.

- [x] Write a failing test requiring a complementary palette class, patterned SVG field, central Runic-derived vector emblem, no raster asset, and front-distinct accessible label.
- [x] Run the focused test and record the expected failure.
- [x] Implement the focused factory and styles without adding options to the front-card contract.
- [x] Run focused tests and typecheck.
- [x] Commit as `feat(game): add parametric card backs (A1.5)` with trailers.

### Task 6: A1.6 — Gallery, visual verification, review reset, and amendment closeout

**Files:**
- Modify: `game/src/ui/screens/card-gallery.ts`
- Modify: `game/src/ui/screens/card-gallery.test.ts`
- Modify: `game/tests/capture.py`
- Refresh: `game/tests/baseline/08-card-gallery.png` and `.sha1`
- Modify: `game/src/ui/cards/README.md`, `game/assets/README.md`, `game/scripts/README.md`, `AGENTS.md`
- Modify: `/opt/agents/repos/spec/reviews/2026-08-10-holdfast-spec-06-card-review.md`
- Modify: `/opt/agents/repos/spec/spec-defect-register.md`
- Append: `/opt/agents/repos/work-logs/2026-08-10-holdfast-worklog-06-card-system-rewrite.md`
- Append: `/opt/agents/repos/work-logs/work-registry.csv`
- Move at closeout: `/opt/agents/repos/spec/2026-08-10-holdfast-spec-06-card-system-rewrite.md` to `/opt/agents/repos/spec/2026-08/`

**Interfaces:**
- Gallery renders the 21-card catalog, upgraded exemplar, both SVG/PNG art paths, and a card back; Playwright returns semantic/geometry evidence used by the approval document.

- [x] Add failing gallery/harness assertions for 21 unique catalog cards, one upgraded exemplar, one SVG and one PNG art motif, five layers per card, foreground text colors distinct from accent, ratio 0.60–0.64, near-square art, no overflow/clipping, distinct attack-card axes, and visible card back.
- [x] Run focused Vitest and `npm run test:screens:check`; record expected failures/regression before refreshing.
- [x] Complete gallery composition and reset Q1–Q6 to Awaiting operator approval, preserving the historical v1 No/No/unanswerable result.
- [x] Recapture the 1440-wide full-height baseline, inspect it beside `/opt/agents/repos/spec/reviews/2026-08-10-holdfast-card-v2-target.html`, and write the fidelity ledger in the implementer report.
- [x] Run `npx tsc --noEmit`, `npm test`, `npm run test:screens:check`, `npm run test:screens:build`, `pytest simulation/tests/ -v`, publish twice, compare `game/dist/` to `/opt/agents/www/holdfast/`, and verify the live bundle content type.
- [x] Run `spec-closeout`: append Amendment 1 to the existing worklog, append one registry row, record the two authored defects plus icon-source scope note, archive the active spec, and commit as `chore: close out card presentation v2 (A1.6)` with trailers. Never push.
