# Game Scripts

Utility scripts for browser build preparation, licensed-asset derivation, and
validation.

- `derive-runic-card-icons.mjs` creates the curated, recoloured SVG vocabulary
  from an authorized Runic Relic RPG Icons 144 source tree and records exact
  source IDs, modes, and paths in the generated manifest. It overwrites only
  the exact known derivatives and fails if the output directory contains an
  unexpected file; an optional second argument selects an isolated output
  directory for verification.
- `prepare-public.mjs` copies shared game JSON, the GameUI skin, and committed
  card-icon derivatives into `game/public/`.
- `check-public.mjs` fails the build early when required generated public files are missing.
