## ADDED Requirements

### Requirement: Character schema
The system SHALL define a character with these required fields: `id` (unique string), `name` (string), `base_stats` (dict mapping each Stat enum to an integer value — all 5 stats required), `innate_passive` (a single Modifier tuple representing the character's permanent passive ability), `name_parts` (dict with `first_name`, `title`, `origin` strings used for display as `"{first_name}, {title} from {origin}"`).

#### Scenario: Valid character with all fields
- **WHEN** a character is created with id, name, all 5 base stats, an innate passive modifier, and name parts
- **THEN** the character passes validation

#### Scenario: Missing stat in base_stats rejected
- **WHEN** a character's base_stats has only HP, Power, Speed, Defense (missing Energy)
- **THEN** validation raises an error

#### Scenario: Innate passive must be a valid modifier
- **WHEN** a character's innate_passive has `duration: -1` (permanent) and valid stat/operation/target
- **THEN** the passive passes validation

#### Scenario: Innate passive with non-permanent duration rejected
- **WHEN** a character's innate_passive has `duration: 3` (turn-based, not permanent)
- **THEN** validation raises an error — innate passives MUST be permanent (`duration: -1`)

### Requirement: Enemy schema
The system SHALL define an enemy with these required fields: `id` (unique string), `name` (string), `base_stats` (dict mapping each Stat enum to integer — all 5 stats required), `card_pool` (list of card IDs the enemy can play), `ai_heuristic_tag` (string enum: `aggressive`, `defensive`, `balanced`), `is_elite` (boolean, defaults false).

#### Scenario: Valid enemy with card pool
- **WHEN** an enemy is created with all required fields and a card_pool of `["strike_01", "phalanx_01"]`
- **THEN** the enemy passes validation

#### Scenario: Empty card pool rejected
- **WHEN** an enemy has `card_pool: []`
- **THEN** validation raises an error — enemies MUST have at least one card

#### Scenario: Valid AI heuristic tags
- **WHEN** an enemy's ai_heuristic_tag is `aggressive`, `defensive`, or `balanced`
- **THEN** the enemy passes validation

#### Scenario: Invalid AI heuristic tag rejected
- **WHEN** an enemy's ai_heuristic_tag is `passive` or any string not in the enum
- **THEN** validation raises an error

### Requirement: Character generation bounds
The system SHALL define generation bounds specifying the min and max values for each of the 5 base stats, plus a total stat budget constraint. Generated characters MUST have individual stats within their min/max range AND total stats within the budget range.

#### Scenario: Bounds define per-stat ranges
- **WHEN** generation bounds are loaded
- **THEN** each of the 5 stats has a `min` and `max` integer value, and `min <= max` for all stats

#### Scenario: Total stat budget constraint
- **WHEN** generation bounds are loaded
- **THEN** there is a `total_budget_min` and `total_budget_max` constraining the sum of all 5 base stats

#### Scenario: GDD example characters fall within bounds
- **WHEN** the Vanguard Sentinel (140/12/80/20/3), Ember Mage (65/28/115/5/4), and Field Tactician (85/15/105/12/5) are validated against bounds
- **THEN** all three fall within per-stat ranges and total budget range

### Requirement: Example entities from GDD
The system SHALL include at minimum 3 example characters matching the GDD: Vanguard Sentinel (HP 140, Power 12, Speed 80, Defense 20, Energy 3, passive: +15% Defense permanent), Ember Mage (HP 65, Power 28, Speed 115, Defense 5, Energy 4, passive: +20% Power vs enemies below 50% HP), Field Tactician (HP 85, Power 15, Speed 105, Defense 12, Energy 5, passive: +1 Energy permanent). At minimum 2 example enemies SHALL be included.

#### Scenario: GDD example characters present and valid
- **WHEN** the example characters JSON is loaded
- **THEN** it contains at least 3 characters matching the GDD stat distributions and passives

#### Scenario: Example enemies present and valid
- **WHEN** the example enemies JSON is loaded
- **THEN** it contains at least 2 enemies with valid stats, card pools, and AI heuristic tags
