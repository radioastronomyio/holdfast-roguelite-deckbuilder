## ADDED Requirements

### Requirement: Pydantic models for all data types
The system SHALL provide Pydantic v2 models in `simulation/models/` that validate every data type defined in the other specs: Modifier, Card, UpgradeTree, Character, Enemy, CharacterGenerationBounds, Region, CombatEncounter, HazardEncounter, EventEncounter, WorldCard, OutpostUpgrade.

#### Scenario: Every JSON data file validates through its Pydantic model
- **WHEN** each JSON file in `data/` is loaded and parsed through its corresponding Pydantic model
- **THEN** all files pass without validation errors

#### Scenario: Pydantic models use StrEnum for all enum fields
- **WHEN** enum fields (Stat, Operation, Target, etc.) are inspected
- **THEN** they are Python `StrEnum` types producing human-readable string values in JSON serialization

### Requirement: Discriminated union for encounter types
The system SHALL use Pydantic's discriminated union feature on the `type` field to route encounter validation to the correct sub-model (CombatEncounter, HazardEncounter, EventEncounter). A single `Encounter` type annotation handles all three variants.

#### Scenario: Combat encounter routes to CombatEncounter model
- **WHEN** a JSON object with `type: "combat"` is parsed as Encounter
- **THEN** it validates against CombatEncounter fields (enemies, enemy_cards required)

#### Scenario: Hazard encounter routes to HazardEncounter model
- **WHEN** a JSON object with `type: "hazard"` is parsed as Encounter
- **THEN** it validates against HazardEncounter fields (hazard_modifiers, hazard_duration required)

#### Scenario: Unknown encounter type rejected
- **WHEN** a JSON object with `type: "trap"` is parsed as Encounter
- **THEN** validation raises an error

### Requirement: Test fixtures for valid data
The system SHALL provide known-good test fixture files in `simulation/tests/fixtures/valid/` for every schema type. Each fixture file MUST contain at least 2 valid examples. Fixtures MUST be loadable as JSON and pass Pydantic validation.

#### Scenario: Valid modifier fixtures pass
- **WHEN** `fixtures/valid/modifiers.json` is loaded and each entry parsed as Modifier
- **THEN** all entries pass validation

#### Scenario: Valid card fixtures pass
- **WHEN** `fixtures/valid/cards.json` is loaded and each entry parsed as Card
- **THEN** all entries pass validation, including upgrade tree structure

#### Scenario: Valid fixtures exist for every schema type
- **WHEN** the fixtures/valid/ directory is listed
- **THEN** it contains fixture files for: modifiers, cards, characters, enemies, regions, world-cards, outpost-upgrades

### Requirement: Test fixtures for invalid data
The system SHALL provide intentionally invalid test fixture files in `simulation/tests/fixtures/invalid/` for every schema type. Each fixture file MUST contain examples that violate specific validation rules, annotated with comments describing the expected failure.

#### Scenario: Invalid modifier fixtures rejected
- **WHEN** `fixtures/invalid/modifiers.json` is loaded and each entry parsed as Modifier
- **THEN** every entry fails validation with a Pydantic ValidationError

#### Scenario: Invalid fixtures cover key failure modes
- **WHEN** the invalid modifier fixtures are inspected
- **THEN** they include at minimum: missing required field, invalid enum value, invalid duration (-2), and wrong type (string where int expected)

#### Scenario: Invalid fixtures exist for every schema type
- **WHEN** the fixtures/invalid/ directory is listed
- **THEN** it contains fixture files for: modifiers, cards, characters, enemies, regions, world-cards, outpost-upgrades

### Requirement: Pytest test suite
The system SHALL include a pytest test suite in `simulation/tests/` that: loads all valid fixtures and asserts they pass validation, loads all invalid fixtures and asserts they raise ValidationError, validates all JSON data files in `data/` against their Pydantic models, and tests cross-schema integrity (e.g., card IDs referenced in enemy card_pool exist in the card set).

#### Scenario: Test suite discovers and runs all fixture tests
- **WHEN** `pytest simulation/tests/` is executed
- **THEN** all tests pass and every fixture file is covered

#### Scenario: Cross-reference integrity test
- **WHEN** an enemy references card_pool `["strike_01"]`
- **THEN** `"strike_01"` MUST exist in the base cards data file

#### Scenario: Upgrade tree prerequisite integrity test
- **WHEN** an upgrade branch references prerequisite `"1A"`
- **THEN** `"1A"` MUST exist as a key in the same card's upgrade tree
