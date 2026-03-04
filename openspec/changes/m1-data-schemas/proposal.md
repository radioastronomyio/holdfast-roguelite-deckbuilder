## Why

The simulation engine (M2) and React frontend (M4) both depend on shared JSON data definitions that don't exist yet. Every game element — cards, characters, enemies, regions, encounters, world deck cards, outpost upgrades — is expressed as modifier arrays on the 5-stat model (GDD: "Core Design Principle"). Without validated schemas and reference data, no downstream code can be written. This is the foundation layer.

## What Changes

- Define the modifier tuple schema and all supporting enums (stat, operation, target, duration)
- Define the resolution order specification with deterministic test fixtures
- Define card base schema and upgrade tree schema with branching rules
- Create initial card set (10-15 base cards with upgrade trees from GDD)
- Define character and enemy entity schemas with innate passives as modifier tuples
- Define character generation bounds and example entities
- Define region, encounter (combat/hazard/event), world deck card, and outpost upgrade schemas
- Create initial world deck (20 cards from GDD)
- Implement Pydantic validation models for all schemas
- Create comprehensive test fixtures (valid + intentionally invalid) for every schema

## Non-goals

- No resolver engine logic (M2 scope — `calculate_stat()`, CT system, combat loop)
- No simulation harness or balance testing (M3 scope)
- No React components or frontend state (M4 scope)
- No procedural generation algorithms — only the schemas and bounds they'll use
- No AI heuristic logic — only the `ai_heuristic_tag` field on enemy schemas

## Capabilities

### New Capabilities

- `modifier-schema`: Modifier tuple format, stat/operation/target/duration enums, resolution order spec
- `card-schema`: Card base schema, upgrade tree schema with branching/exclusionary rules, initial card set data
- `entity-schema`: Character schema, enemy schema, generation bounds, innate passives as modifiers
- `campaign-schema`: Region schema, encounter schemas (type discriminator), world deck card schema, outpost upgrade schema, initial world deck data
- `schema-validation`: Pydantic models for all data types, pytest fixtures (valid + invalid)

### Modified Capabilities

(none — greenfield)

## Impact

- `data/` — All JSON schema definitions and example data files land here
- `simulation/` — Pydantic models and pytest fixtures for validation
- `AGENTS.md` — Current State updated from "Pre-Implementation" to "M1 In Progress"
