# Holdfast Card System Rewrite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the existing PNG-assisted Holdfast card presentation with a data-driven, zero-raster SVG deckbuilder frame while preserving the complete `createHoldfastCard` contract and stabilizing root-path publishing and project records.

**Architecture:** `createHoldfastCard` remains the only consumer-facing factory and continues to compose the vendored `createCard` control. Pure mapping helpers select accents, motifs, palettes, and effect symbols; focused SVG factories render art and badges; consumer-owned CSS lays out the six-region frame. Vitest proves mapping, SVG, contract, and data behavior, while the existing Playwright harness proves the rendered gallery, computed accent inheritance, root-path build, and asset delivery.

**Tech Stack:** TypeScript 5.8, vanilla DOM/SVG, GameUI, CSS custom properties, Vitest with happy-dom, Vite, Python Playwright, Bash/rsync, shared JSON card definitions.

## Global Constraints

- Preserve the `createHoldfastCard(card: Card, opts?: HoldfastCardOptions): HoldfastCardControl` public surface exactly, including every `CardControl` method and `setRare`, `setEnergyAffordable`, and `openInspect`.
- Use only existing `--gui-*` tokens for themeable CSS properties; introduce no hue-named or domain-named tokens.
- The new card art, cost badge, gem, and effect-symbol paths contain SVG only and reference no PNG or WebP.
- All curated Game-icons glyphs are by Lorc under CC BY 3.0 and are credited in `game/assets/card-art-icons/NOTICE`.
- Do not modify `simulation/**`, `data/**`, or vendored GameUI component/token files; only `game/vendor/gameui/VENDORED.md` may change.
- Retire existing PNG card icons by moving them to repository `recycle/`; never delete them.
- Keep Vite base `/`; never restore `/holdfast/`.
- Work only on local branch `agent/holdfast-spec-06-card-system-rewrite`; commit every deliverable with `Co-authored-by`, `Model`, and archived `Spec` trailers; never push or merge.

---

### Task 1: Root-Path Build Acceptance

**Files:**
- Modify: `game/tests/capture.py`
- Modify: `docs/superpowers/plans/2026-08-10-card-system-rewrite.md`

**Interfaces:**
- Consumes: Vite `base: "/"` and generated `game/dist/`.
- Produces: `BASE_PATH = "/"` and root-relative asset probes used by `npm run test:screens:build`.

- [ ] **Step 1: Run the current built-output gate and confirm the stale `/holdfast/` assumption fails.**

  Run: `cd game && npm run test:screens:build`

  Expected: non-zero exit because preview readiness/navigation uses `/holdfast/` while Vite serves at `/`.

- [ ] **Step 2: Repoint the harness to `/` and retain content-type checks.**

  Set `BASE_PATH = "/"`, update comments, and keep probes as relative keys joined to the preview origin. Replace the retiring PNG probe with `assets/card-art-icons/crossed-swords.svg: image/svg+xml` after Task 4 lands; until then use a theme asset so Task 1 can pass independently.

- [ ] **Step 3: Verify the root-path build gate.**

  Run: `cd game && npm run test:screens:build`

  Expected: exit 0, dark-fantasy `--gui-bg` applied, all walk screens found, and every probe returns its expected non-HTML content type.

- [ ] **Step 4: Verify no stale prefixed probes remain.**

  Run: `rg -n '/holdfast/' game/tests/capture.py`

  Expected: no output.

- [ ] **Step 5: Commit Deliverable 1 locally with the three estate trailers.**

  Commit subject: `fix(game): gate root-path build output (D1)`.

### Task 2: Safe, Idempotent Publisher

**Files:**
- Create: `publish.sh`
- Modify: `game/package.json`
- Test: `game/src/systems/publish.test.ts`

**Interfaces:**
- Consumes: `game/dist/` produced by `npm run build` and fixed destination `/opt/agents/www/holdfast`.
- Produces: `npm run publish`, which builds then mirrors only into the validated Holdfast root.

- [ ] **Step 1: Write a failing script behavior test.**

  The test runs `publish.sh --deploy-only --target <temporary holdfast fixture>` with `HOLDFAST_PUBLISH_TEST=1`, verifies an extra destination file is removed, source and destination trees match, and a second run leaves identical hashes. It also verifies a target outside the test fixture is rejected.

- [ ] **Step 2: Run the focused test and confirm it fails because `publish.sh` does not exist.**

  Run: `cd game && npm test -- src/systems/publish.test.ts`

- [ ] **Step 3: Implement the scoped publisher.**

  `publish.sh` resolves its own repository path, runs `npm run build` in `game/`, validates source and destination, rejects symlinks, permits a target override only when `HOLDFAST_PUBLISH_TEST=1`, then runs `rsync -a --delete --itemize-changes "$SOURCE/" "$TARGET/"`. The production default remains the literal `/opt/agents/www/holdfast`.

- [ ] **Step 4: Add `"publish": "../publish.sh"` and run the behavior test twice.**

  Run: `cd game && npm test -- src/systems/publish.test.ts`

  Expected: pass with source/destination equivalence and idempotence proven.

- [ ] **Step 5: Run the real publish and compare exact trees.**

  Run: `./publish.sh && diff -r game/dist/ /opt/agents/www/holdfast/ && ./publish.sh && diff -r game/dist/ /opt/agents/www/holdfast/`

  Expected: both diffs empty.

- [ ] **Step 6: Commit Deliverable 2 locally with the three estate trailers.**

  Commit subject: `feat(game): add scoped production publisher (D2)`.

### Task 3: Frozen Card Contract and Six-Region Frame

**Files:**
- Create: `game/src/ui/cards/contract.ts`
- Create: `game/src/ui/cards/card.css`
- Modify: `game/src/ui/cards/holdfastCard.ts`
- Modify: `game/src/ui/cards/cards.css`
- Test: `game/src/ui/cards/holdfastCard.test.ts`
- Test: `game/src/ui/cards/contract.test.ts`

**Interfaces:**
- Consumes: `Card`, `UpgradeTree`, `CardControl`, and `createCard`.
- Produces: unchanged `HoldfastCardOptions`, `HoldfastCardControl`, and typed `CreateHoldfastCard`; DOM regions `.hf-card__cost`, `.hf-card__art`, `.hf-card__type`, `.hf-card__rules`, `.hf-card__attack`, `.hf-card__guard`.

- [ ] **Step 1: Write failing contract and frame tests.**

  The contract fixture calls every option (`rare`, `selectable`, `selected`, `disabled`, `onClick`, `onSelect`, `upgradeTree`) and every return method (`setSelected`, `isSelected`, `setDisabled`, `setTitle`, `setSubtitle`, `setBody`, `setTag`, `onClick`, `onSelect`, `setRare`, `setEnergyAffordable`, `openInspect`). The DOM test renders Arcane Strike and asserts all six new regions exist, the title/type/rules come from JSON, attack is `15`, and guard is `0`.

- [ ] **Step 2: Run the focused tests and confirm missing contract/frame selectors fail.**

  Run: `cd game && npm test -- src/ui/cards/contract.test.ts src/ui/cards/holdfastCard.test.ts`

- [ ] **Step 3: Capture the typed contract and compose the frame.**

  Export the existing option/control shapes from `contract.ts` and type the factory as `CreateHoldfastCard`. Continue calling `createCard`; replace only its internal body/footer content with the title/cost/art/type/rules/attack/guard composition. Derive attack from the greatest absolute `HP FLAT_SUB` effect and guard from the greatest positive `Defense` or `HP` effect, defaulting each to `0`.

- [ ] **Step 4: Implement token-only deckbuilder layout.**

  `card.css` owns the 744:1038-inspired aspect ratio and slot proportions. Themeable background, border, text, radius, shadow, glow, timing, and accent values use `--gui-*` or inherited `--card-accent`; numeric SVG/layout coordinates are structural constants.

- [ ] **Step 5: Run focused tests and TypeScript.**

  Run: `cd game && npm test -- src/ui/cards/contract.test.ts src/ui/cards/holdfastCard.test.ts && npx tsc --noEmit`

- [ ] **Step 6: Prove contract mutation detection on a scratch copy.**

  Copy `contract.ts` and its fixture to a temporary directory, remove `setEnergyAffordable` from the copied control type, run the project compiler against the mutation fixture, confirm non-zero, then leave repository files unchanged.

- [ ] **Step 7: Commit Deliverable 3 locally with the three estate trailers.**

  Commit subject: `feat(game): compose SVG deckbuilder card frame (D3)`.

### Task 4: Parametric SVG Art and Curated Glyphs

**Files:**
- Create: `game/src/ui/cards/cardMap.ts`
- Create: `game/src/ui/cards/cardArt.ts`
- Create: `game/src/ui/cards/cardArt.test.ts`
- Create: `game/src/ui/cards/cardMap.test.ts`
- Create: `game/assets/card-art-icons/README.md`
- Create: `game/assets/card-art-icons/NOTICE`
- Create: `game/assets/card-art-icons/*.svg`
- Modify: `game/scripts/prepare-public.mjs`
- Modify: `game/scripts/check-public.mjs`

**Interfaces:**
- Consumes: card/effect tags and Lorc SVG paths from `game-icons/icons`.
- Produces: `resolveCardVisual(tags)`, `resolveEffectSymbol(modifier)`, `cardArtIconUrl(symbol)`, and `createCardArt({ motif, palette })`.

- [ ] **Step 1: Write failing mapping and SVG-scene tests.**

  Assert all 21 JSON cards resolve a motif/palette, every modifier resolves a nonempty symbol, unknown effect shapes throw `Unmapped card effect`, and `createCardArt` returns one SVG containing `linearGradient`, sky, ground, one `<use>` symbol, and vignette with `fill="currentColor"`.

- [ ] **Step 2: Run the focused tests and confirm missing-module failures.**

  Run: `cd game && npm test -- src/ui/cards/cardMap.test.ts src/ui/cards/cardArt.test.ts`

- [ ] **Step 3: Curate and normalize Lorc glyphs.**

  Fetch only the named Lorc SVG files used for motifs/effects from `https://raw.githubusercontent.com/game-icons/icons/master/lorc/`, convert each outer `<svg>` into an SVG sprite containing `<symbol id="icon" viewBox="0 0 512 512">`, remove background rectangles, set path fill to `currentColor`, and retain no raster file.

- [ ] **Step 4: Write complete attribution.**

  `NOTICE` names every shipped filename, Lorc as author, Game-icons as source, CC BY 3.0 license URL, upstream repository URL, and the transformations (background removed, wrapped as symbol, `currentColor`).

- [ ] **Step 5: Implement pure mappings and the SVG art factory.**

  Card-tag precedence selects dark-fantasy motifs and a palette role composed only from `--gui-*` variables. Effect resolution is explicit and throws when no tag/stat mapping exists. `createCardArt` creates SVG namespace nodes with a unique gradient ID, sky rectangle, ground silhouette path, centered external `<use>`, and radial vignette.

- [ ] **Step 6: Stage and guard the new SVG family.**

  `prepare-public.mjs` copies `assets/card-art-icons/` to `public/assets/card-art-icons/`; `check-public.mjs` requires `crossed-swords.svg` and `NOTICE`; the build probe expects `image/svg+xml`.

- [ ] **Step 7: Run tests, build, and zero-raster checks.**

  Run: `cd game && npm test -- src/ui/cards/cardMap.test.ts src/ui/cards/cardArt.test.ts && npm run build`

  Run: `find game/assets/card-art-icons -type f ! -name '*.svg' ! -name 'README.md' ! -name NOTICE -print` and `rg -n '\.(png|webp)' game/src/ui/cards`

  Expected: tests/build pass and both checks produce no forbidden art reference.

- [ ] **Step 8: Commit Deliverable 4 locally with the three estate trailers.**

  Commit subject: `feat(game): add parametric SVG card art (D4)`.

### Task 5: SVG Cost and Upgrade Badges

**Files:**
- Create: `game/src/ui/cards/cardBadges.ts`
- Create: `game/src/ui/cards/cardBadges.test.ts`
- Modify: `game/src/ui/cards/holdfastCard.ts`
- Modify: `game/src/ui/cards/card.css`
- Test: `game/src/ui/cards/holdfastCard.test.ts`

**Interfaces:**
- Produces: `createCostBadge(cost: number): SVGSVGElement` and `createUpgradeGem(tier: number): SVGSVGElement`.

- [ ] **Step 1: Write failing badge and integration tests.**

  Table-test costs `0..4`, asserting the SVG text equals the input and uses `.hf-card-badge__accent`; table-test tiers `0..3`, asserting `data-upgrade-tier`. Integration tests prove `energy_cost: 3` renders `3`, tier 0 lacks shine, and tier 2 has an active gem plus shine.

- [ ] **Step 2: Run focused tests and confirm missing factories/selectors fail.**

  Run: `cd game && npm test -- src/ui/cards/cardBadges.test.ts src/ui/cards/holdfastCard.test.ts`

- [ ] **Step 3: Implement inline SVG badges and wire them to JSON fields.**

  SVG shapes use structural coordinates only; CSS fill/stroke/color comes from `--card-accent`, `--gui-surface-*`, and `--gui-text-on-accent`. `rare` may toggle the existing rare class, but shine is determined only by `upgrade_tier > 0` per this rewrite.

- [ ] **Step 4: Run focused tests and TypeScript.**

  Run: `cd game && npm test -- src/ui/cards/cardBadges.test.ts src/ui/cards/holdfastCard.test.ts && npx tsc --noEmit`

- [ ] **Step 5: Commit Deliverable 5 locally with the three estate trailers.**

  Commit subject: `feat(game): render SVG card badges and gems (D5)`.

### Task 6: Full JSON Gallery, Harness Assertions, and Review Surface

**Files:**
- Modify: `game/src/ui/screens/card-gallery.ts`
- Modify: `game/tests/capture.py`
- Modify: `game/tests/baseline/08-card-gallery.png`
- Modify: `game/tests/baseline/08-card-gallery.png.sha1`
- Modify: `game/src/ui/cards/README.md`
- Modify: `game/tests/README.md`
- Create: `/opt/agents/repos/spec/reviews/2026-08-10-holdfast-spec-06-card-review.md`
- Move: `game/assets/card-icons/` to `recycle/2026-08-10-card-icons/`
- Modify: `game/scripts/prepare-public.mjs`
- Modify: `game/scripts/check-public.mjs`

**Interfaces:**
- Consumes: 15 base cards plus 6 hazard cards.
- Produces: gallery metadata `data-gallery-card-count="21"`, one `.hf-card[data-card-id]` per JSON entry plus labeled upgrade exemplars, and Playwright assertions for count/frame/color/assets.

- [ ] **Step 1: Add failing gallery assertions to the harness.**

  After gallery navigation, load both JSON lists and assert exactly 21 unique data-backed cards under `.hf-gallery__catalog`, all six frame regions on a sample, every effect `<use>` has a nonempty href, computed symbol fill equals the computed card accent, and the upgraded exemplar alone has shine.

- [ ] **Step 2: Run the screen harness and confirm the new metadata/assertions fail.**

  Run: `cd game && npm run test:screens`

- [ ] **Step 3: Bind the gallery and renderer to the full catalog.**

  Wrap base/hazard sections in `.hf-gallery__catalog`, set the expected count, render effects via `resolveEffectSymbol`, and keep the upgraded exemplar outside the catalog count.

- [ ] **Step 4: Retire PNG icons recoverably.**

  Move the exact inspected `game/assets/card-icons/` directory to `recycle/2026-08-10-card-icons/card-icons/`, add a note naming Spec 06 and the new SVG replacement, remove PNG staging/guards, regenerate public assets, and verify `game/dist/` has no old icon path.

- [ ] **Step 5: Create the six-question operator review surface.**

  Add stable headings `Q1` through `Q6`, a yes/no checkbox pair for each exact Human Approval Surface question, the gallery command/URL, verification summary, and an explicit note that Spec 04 remains gated on operator approval.

- [ ] **Step 6: Capture and check the new gallery baseline.**

  Run: `cd game && npm run test:screens && npm run test:screens:check`

  Expected: 8 screens captured; 8 checks pass; no console, request, frame, mapping, count, or computed-color failure.

- [ ] **Step 7: Verify old assets are absent.**

  Run: `find game/dist -path '*card-icons*' -print` and `rg -n 'card-icons' game/dist || true`

  Expected: no retired card-icon path; unrelated baseline PNGs are outside `dist`.

- [ ] **Step 8: Commit Deliverable 6 locally with the three estate trailers.**

  Commit subject: `feat(game): bind SVG cards to full gallery (D6)`.

### Task 7: Documentation and Queue Drift Sweep

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `game/README.md`
- Modify: `game/assets/README.md`
- Modify: `game/vendor/gameui/VENDORED.md`
- Modify: `/opt/agents/repos/spec/2026-06-22-holdfast-spec-04-combat-screen.md`
- Modify: `/opt/agents/repos/spec/2026-06-22-holdfast-spec-05-flow-screens.md`

**Interfaces:**
- Produces: truthful project status and resolvable spec references; no runtime interface.

- [ ] **Step 1: Apply the bounded drift edits.**

  Replace `radioastronomyio` with `vintagedon` in the three named repository identity files; describe the central queue at `/opt/agents/repos/spec/`; set Current State to completed Spec 06 SVG card gallery and Next work to Spec 04 then Spec 05. In Specs 04/05, add Spec 06 to related docs/preconditions and replace dead external framework paths with existing `game/vendor/gameui/` paths only.

- [ ] **Step 2: Refresh touched interior READMEs.**

  Document `cardArt.ts`, `cardBadges.ts`, `cardMap.ts`, `card.css`, `card-art-icons/`, the retired PNG path, gallery assertions, and root-path build probe.

- [ ] **Step 3: Run drift and path checks.**

  Run: `rg -n 'radioastronomyio' AGENTS.md README.md game/vendor/gameui/VENDORED.md`

  Run: `rg -n 'gameui-browser-gaming-framework' /opt/agents/repos/spec/2026-06-22-holdfast-spec-0{4,5}-*.md`

  Run: `rg -n 'spec-06|game/vendor/gameui/' /opt/agents/repos/spec/2026-06-22-holdfast-spec-0{4,5}-*.md`

  Expected: first two commands have no output; third shows both preconditions/related docs and only paths that resolve.

- [ ] **Step 4: Commit Deliverable 7 locally with the three estate trailers.**

  Commit subject: `docs: reconcile card-system project state (D7)`.

  Note: central queue files are outside this Git repository and are recorded in the worklog rather than this commit.

### Task 8: Full Verification and Lifecycle Closeout

**Files:**
- Create: `/opt/agents/repos/work-logs/2026-08-10-holdfast-worklog-06-card-system-rewrite.md`
- Modify: `/opt/agents/repos/work-logs/work-registry.csv`
- Move: `/opt/agents/repos/spec/2026-08-10-holdfast-spec-06-card-system-rewrite.md` to `/opt/agents/repos/spec/2026-08/2026-08-10-holdfast-spec-06-card-system-rewrite.md`
- Modify: project docs only if the closeout consistency pass finds a factual stale reference.

**Interfaces:**
- Produces: evidence-linked local commit chain, completed worklog, one registry row, archived spec, and no push.

- [ ] **Step 1: Invoke verification-before-completion and run every required gate fresh.**

  Run from `game/`: `npx tsc --noEmit`, `npm test`, `npm run test:screens:check`, `npm run test:screens:build`, `npm run build`.

  Run from repository root: `pytest simulation/tests/ -v`.

  Run publish/live checks: `diff -r game/dist/ /opt/agents/www/holdfast/`, then request the built JS URL and verify HTTP 200 plus JavaScript content type.

- [ ] **Step 2: Review the full diff against all eight deliverables and constraints.**

  Confirm no changes under `simulation/**`, `data/**`, or vendored component/token files; no reference-pack asset entered the repo; all mappings cover 21 cards; all old PNG icons are recoverable under `recycle/`; every themeable style uses an existing token role.

- [ ] **Step 3: Request a code review and resolve only verified findings.**

  Use `superpowers:requesting-code-review`; because subagents are disabled for this run, perform its fallback self-review against the base commit and rerun affected tests after corrections.

- [ ] **Step 4: Run the documented `spec-closeout` fallback.**

  Refresh touched orientation docs, run consistency checks, create the final closeout commit with all three trailers, then write the worklog with every gate SHA, runtime `Codex`, model `GPT-5`, host `ml01`, starting branch `main`, and base SHA `1d0aa69d86d1303b58f91efaf9b5aae846bada53`.

- [ ] **Step 5: Append exactly one registry row and archive the spec without deleting it.**

  Preserve all 23 registry columns, use category `frontend`, status `completed`, `token_usage_source=unavailable`, and leave token/cost fields empty. Move the active spec into `spec/2026-08/` and verify the archived path matches every commit `Spec:` trailer.

- [ ] **Step 6: Verify final state.**

  Run: `git status --short --branch`, `git log --format=full -9`, registry CSV parsing/count check, worklog/spec existence checks, and `git remote -v` without any remote mutation.

  Expected: clean local working tree on the startup branch, eight deliverable commits (D8 may be an empty evidence commit), all trailers present, no push, completed records, and the active queue file absent because it was moved to the month archive.
