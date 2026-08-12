# Task 4 report — A1.4 pluggable SVG/PNG art source

## Scope delivered

- Added presentation-only `CardVisual.artSource`, defaulting to `"svg"`.
- Opted only `immolate_01` into `"image"`; it resolves to
  `assets/card-icons/immolate-fireball.png` within the existing inline SVG
  sky/glow/motif/ground/vignette scene.
- Kept `HoldfastCardOptions` unchanged. Card JSON has no `artSource`; source
  selection remains in the card presentation map.
- Added source data attributes on the SVG scene and motif node for DOM and
  harness inspection. Chrome, badges, gem, pips, and effect glyphs continue to
  use vector-only markup/assets.
- Made the public prebuild inventory require the staged Immolate PNG. The
  existing directory staging copies it alongside the derived SVG vocabulary.

## TDD evidence

### RED

Before production changes, `npm test -- src/ui/cards/cardMap.test.ts
src/ui/cards/cardArt.test.ts` produced three expected behavior failures:

1. An unflagged card had no `artSource` default (`undefined`, expected `svg`).
2. The default SVG art scene had no `data-art-source` marker.
3. The Immolate image branch had no `data-art-source` marker or PNG motif URL.

The JSON/frozen-factory guard already passed, demonstrating that the public
card contract did not expose the new presentation flag.

### GREEN

After the minimal presentation mapping and shared-scene branch,
`npm test -- src/ui/cards/cardMap.test.ts src/ui/cards/cardArt.test.ts` passed
20 tests. A locked paint-order assertion then detected an added motif class;
the implementation was narrowed to preserve the identical five-layer wrapper
and use semantic `data-art-source` markers instead.

## PNG provenance

`game/assets/card-icons/immolate-fireball.png` was supplied as a required
built-in image-edit workflow output and was not regenerated or overwritten in
this task. It is a project-bound 512×512 RGBA PNG with transparent corners.
The edit preserved the Runic fireball motif and recoloured it to ember orange,
muted brass, oxblood, soot, and bone.

## Verification run

- `npm run prepare:public`
- `npm run check:public`
- `npm test -- src/ui/cards` — 63 tests passed
- `npm test` — 97 tests passed
- `npx tsc --noEmit`
- `npm run build`
