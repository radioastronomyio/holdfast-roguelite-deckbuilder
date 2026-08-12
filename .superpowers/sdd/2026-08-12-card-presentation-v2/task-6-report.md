# Task 6 implementer report — A1.6

## Outcome

The DEV card-gallery is the renewed Amendment 1 approval surface. It renders the 21-card JSON catalog once, a base/upgraded exemplar pair, both SVG and PNG motif paths, and the token-driven zero-raster card back. The Playwright harness now verifies the presentation contract in the rendered browser before capturing the baseline.

## RED / GREEN evidence

- RED — `npm test -- src/ui/screens/card-gallery.test.ts`: 2 failures. The five-layer assertion initially included SVG `<defs>` and the gallery had no card-back specimen. The test was corrected to count only named paint layers; the missing card-back failure remained and drove the gallery change.
- GREEN — focused gallery: 3/3 tests passed after adding the card-back specimen.
- RED — `npm run test:screens:check`: the strengthened browser gate rejected the v1 zero-PNG assumption, missing back, baseline drift, and real rule-content clipping across the catalog. After source/back expectations landed, long two-effect cards still lost 29–49 px of rules content; this was not the 1–3 px font line-box scroll rounding seen in footer text.
- GREEN — compact effect rows and fixed-width centered gallery columns removed real clipping and horizontal overflow. `npm run test:screens:check` then reported `GALLERY-OK` and `INTERACT-OK`; after the intentional recapture, all eight baselines matched.

## Browser QA

The flow under test was: app loads -> `window.__holdfast.showCardGallery()` -> complete v2 gallery renders -> first catalog card selection toggles on and back off -> semantic/geometry checks pass -> baseline capture.

Browser plugin classification: **Browser plugin not available**. The approved fallback was regular repository Playwright with Chromium headless.

| Check | Result |
|---|---|
| 1440x900 page identity / meaningful content | Pass — `Holdfast`, `card-gallery`, `Base Cards (15)` |
| Console/page health | Pass — no warning, error, or pageerror |
| Catalog identity | Pass — 21 cards, 21 unique IDs |
| Art sources | Pass — 20 SVG motifs, 1 PNG motif |
| Five paint layers | Pass — sky, glow, motif, ground, vignette in exact order on every card |
| Foreground roles | Pass — type, rules, and stat values resolve to `--gui-text`, not accent |
| Geometry | Pass — width:height 0.60–0.64; art ratio 0.88–1.12; no semantic or horizontal clipping |
| Attack variety axes | Pass — Arcane Strike and Immolate differ in palette, ground, and motif |
| Effect glyphs | Pass — all mapped SVG glyphs loaded (`naturalWidth > 0`) |
| Upgraded exemplar / card back | Pass — one tier-2 shine; patterned/emblem back with no image nodes |
| Interaction | Pass — `aria-pressed`: false -> true -> false |
| Mobile sanity (390x844) | Pass — no horizontal overflow, no card outside gallery, no console/page errors |

Temporary evidence: `/tmp/holdfast-card-v2-desktop.png`, `/tmp/holdfast-card-v2-mobile.png`.

## Fidelity ledger

Reference: `/opt/agents/repos/spec/reviews/2026-08-10-holdfast-card-v2-target.html` rendered at `/tmp/holdfast-card-v2-target.png`.

| Reference evidence | Rendered evidence | Disposition |
|---|---|---|
| Tall card near 0.62 | Every catalog card browser-asserted 0.60–0.64 | Matched |
| Near-square art window | Every art window browser-asserted 0.88–1.12 | Matched |
| Neutral dark surface; color isolated to art | Gallery uses dark GameUI chrome and per-card colored art band | Matched |
| Five identical art layers | Exact structural assertion for all 21 cards | Matched |
| High-contrast corner stats | Bold foreground values anchored at lower corners | Matched |
| Compact rules row | Real modifier rows remain explicit and may wrap | Intentional: mechanics stay legible rather than collapsing to target shorthand |
| Placeholder enamel silhouettes | Self-coloured Runic Relic-derived medallions | Intentional source-system replacement required by A1.3 |

## Verification

- `cd game && npx tsc --noEmit` — pass.
- `cd game && npm test` — 100/100 pass.
- `cd game && npm run test:screens:check` — eight baselines pass; gallery semantic/geometry and interaction gates pass; zero non-origin requests.
- `cd game && npm run test:screens:build` — build gate pass; skin, font, webp, and card SVG probes pass; zero failed assets and zero non-origin requests.
- `pytest simulation/tests/ -v` — 367/367 pass; one pre-existing Pydantic serialization warning.
- `bash publish.sh` twice — both builds/publishes pass; second run is idempotent in content. (`publish.sh` is not executable in the inherited v1 tree, so Bash was invoked explicitly.)
- `diff -r game/dist/ /opt/agents/www/holdfast/` — no differences.
- Live HEAD probes — `/` returns `200 text/html`; built bundle returns `200 application/javascript`.
- `git diff --name-only 6fb8a7b -- data simulation` — empty.

## Review document

`/opt/agents/repos/spec/reviews/2026-08-10-holdfast-spec-06-card-review.md` now preserves the historical v1 No/No/unanswerable decision and resets Amendment 1 Q1–Q6 to awaiting operator answers.

## Unresolved issues

- Operator approval remains outstanding by design; task 04 stays gated.
- The inherited `publish.sh` file lacks its executable bit. The production publish succeeded twice through `bash publish.sh`; changing that v1-deliverable mode was not necessary to A1.6 behavior and is reported for controller triage.
