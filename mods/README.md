# Holdfast Mod System

This directory contains mod content for Holdfast. The game loads all subdirectories as mods and merges their data pools.

## Architecture

- `default/` — Base content provided with the game
- Additional mod directories can be added alongside `default/`
- Mods are loaded in directory order (alphabetical)
- Later mods override earlier mods for conflicting entries

## Mod Structure

Each mod directory should contain:
- `flavor/` — Flavor text and name generation pools
  - `given_names.json` — First name pool
  - `archetypes.json` — Character archetype labels
  - `action_verbs.json` — Attack action verbs
  - `region_adjectives.json` — Region name adjectives
  - `region_nouns.json` — Region name nouns
  - `element-stat-map.json` — Stat to element pool mapping
  - `epithet-conditions.json` — Condition-based epithet rules

## Loading

The game loads all mods from this directory and merges their pools. No code changes required to add new words or override existing ones.

## Future Extensions

Future versions may support:
- Mod manifest files
- Conflicting mod resolution strategies
- Schema versioning
- Card and entity definitions in mods
