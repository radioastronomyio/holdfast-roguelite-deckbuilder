# Game Scripts

Utility scripts for browser build preparation, licensed-asset derivation, and
validation.

- `derive-runic-card-icons.mjs` creates the curated, recoloured SVG vocabulary
  from an authorized Runic Relic RPG Icons 144 source tree and records exact
  source IDs, modes, and paths in the generated manifest.
- `prepare-public.mjs` copies shared game JSON, the GameUI skin, and committed
  card-icon derivatives into `game/public/`.
- `check-public.mjs` fails the build early when required generated public files are missing.
