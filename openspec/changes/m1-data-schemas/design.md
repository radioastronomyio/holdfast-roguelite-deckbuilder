## Context

Holdfast is a roguelite deckbuilder where every game element is a modifier array on a 5-stat model. The project has a complete GDD but no code yet. Two consumers will read the data layer: a Python simulation engine (M2) and a React frontend (M4). This milestone creates the shared data contract both depend on.

The repo structure is already scaffolded:
- `data/` — JSON schema definitions and example data (output of this milestone)
- `simulation/` — Python code including Pydantic models and tests (output of this milestone)
- `game/` — React frontend (future, not this milestone)

## Goals / Non-Goals

**Goals:**
- Define every data type as both a JSON schema (in `data/schemas/`) and a Pydantic model (in `simulation/models/`)
- Create reference data files (cards, world deck, example characters/enemies/regions) in `data/`
- Establish a test suite that validates all reference data against schemas
- Distill enough GDD context into the schemas themselves (via field descriptions, enum values, constraints) that downstream implementors don't need to re-read the full GDD for data structure questions

**Non-Goals:**
- No resolver logic (`calculate_stat()`, CT system, combat loop) — that's M2
- No procedural generation algorithms — only the bounds and schemas they'll populate
- No frontend types or TypeScript — Python/JSON only for now
- No simulation harness or balance metrics

## Decisions

### 1. JSON files as source of truth, Pydantic as validator

JSON schema files in `data/schemas/` define the canonical structure. Pydantic models in `simulation/models/` mirror them for Python-side validation and type safety. The JSON files are what both consumers (Python sim, React frontend) read at runtime.

**Why not Pydantic-only?** The React frontend needs a language-agnostic format. JSON schemas serve both consumers. Pydantic models are the Python convenience layer, not the source of truth.

**Why not JSON Schema (the formal spec)?** Formal JSON Schema is verbose and agent-unfriendly. We use Pydantic models that can export to JSON Schema if needed later, but the hand-written JSON data files are validated by Pydantic directly.

### 2. Directory structure under `data/`

```
data/
├── schemas/          # Pydantic model definitions live in simulation/models/
│                     # but data/ holds the reference JSON files
├── cards/
│   ├── base-cards.json        # 10-15 base cards
│   └── upgrade-trees.json     # upgrade paths for each base card
├── entities/
│   ├── example-characters.json
│   └── example-enemies.json
├── campaign/
│   ├── example-regions.json
│   ├── world-deck.json        # 20 world cards
│   └── outpost-upgrades.json
└── enums.json                 # shared enum definitions
```

```
simulation/
├── models/
│   ├── __init__.py
│   ├── enums.py               # Stat, Operation, Target, Duration enums
│   ├── modifier.py            # Modifier tuple model
│   ├── card.py                # Card + UpgradeTree models
│   ├── entity.py              # Character + Enemy models
│   ├── campaign.py            # Region, Encounter, WorldCard, OutpostUpgrade
│   └── generation.py          # CharacterGenerationBounds
├── tests/
│   ├── __init__.py
│   ├── test_modifier.py
│   ├── test_card.py
│   ├── test_entity.py
│   ├── test_campaign.py
│   └── fixtures/
│       ├── valid/              # known-good data per schema
│       └── invalid/            # intentionally broken data per schema
└── __init__.py
```

**Why this split?** `data/` is the shared contract (consumed by both Python and React). `simulation/models/` is Python-only validation. Tests live next to the code that uses them.

### 3. Modifier tuple as the atomic type

Every schema composes from the modifier tuple. Cards have `effects: list[Modifier]`. Characters have `innate_passive: Modifier`. Regions have `modifier_stack: list[Modifier]`. World cards have `upside: list[Modifier]` and `downside: list[Modifier]`. This uniformity is the game's core design principle — enforce it at the schema level.

### 4. Enums as string literals, not integer codes

Stat values are `"HP" | "Power" | "Speed" | "Defense" | "Energy"`, not `0 | 1 | 2 | 3 | 4`. String enums are self-documenting in JSON files, readable in test output, and trivially serializable. Python `StrEnum` provides type safety without sacrificing readability.

### 5. Encounter type discrimination

Encounters use a `type` field discriminator: `"combat" | "hazard" | "event"`. All three share base fields (position in narrative arc, region reference) but have type-specific fields (combat has enemies + enemy cards; hazard has hazard modifiers + duration; event has choices). Pydantic discriminated unions handle this cleanly.

### 6. Upgrade tree as adjacency structure

Upgrade trees are represented as a flat dict keyed by tier+branch (`"1A"`, `"1B"`, `"2A_from_1A"`, etc.) rather than a nested tree. Each entry holds: the modifier(s) added at that tier, the prerequisite branch, and any exclusionary rules. Flat structure is easier to validate and traverse than deeply nested objects.

### 7. Stacking rules on modifiers

Each modifier carries an optional `stacking` field: `"stack" | "replace" | "max"`. Default is `"replace"` (re-applying refreshes duration but doesn't stack value). This prevents infinite Defense stacking (GDD Pitfall #4) at the schema level rather than relying on resolver logic.

## Risks / Trade-offs

**[Risk] Schema drift between JSON and Pydantic** → Mitigation: Tests load JSON files through Pydantic models. Any mismatch fails CI. No separate JSON Schema validation layer to maintain.

**[Risk] Initial card/world deck data is placeholder quality** → Mitigation: Mark data-authoring sub-tasks as HITL. Values come from GDD examples but will be tuned in M3. Schemas must be stable; data values will change.

**[Risk] Overconstrained schemas block M2 flexibility** → Mitigation: Use `Optional` fields and `extra = "forbid"` judiciously. Core fields are required; extension points (like future card keywords) use optional fields with defaults.

**[Risk] Character generation bounds too tight or too loose** → Mitigation: Bounds are initial estimates from GDD examples. M3 simulation will pressure-test them. Schema supports arbitrary bounds; values are tunable in JSON without code changes.
