## ADDED Requirements

### Requirement: Stat enum defines exactly 5 values
The system SHALL define a `Stat` enum with exactly these values: `HP`, `Power`, `Speed`, `Defense`, `Energy`. No other stat values are valid.

#### Scenario: Valid stat values accepted
- **WHEN** a modifier is created with stat set to any of `HP`, `Power`, `Speed`, `Defense`, `Energy`
- **THEN** the modifier passes validation

#### Scenario: Invalid stat values rejected
- **WHEN** a modifier is created with stat set to `Mana`, `Luck`, or any string not in the enum
- **THEN** validation raises an error

### Requirement: Operation enum defines exactly 5 values
The system SHALL define an `Operation` enum with values: `FLAT_ADD`, `FLAT_SUB`, `PCT_ADD`, `PCT_SUB`, `MULTIPLY`. These correspond to the resolution order phases: flat modification, percentage modification, multiplicative scaling.

#### Scenario: Valid operation values accepted
- **WHEN** a modifier uses any of the 5 defined operation values
- **THEN** the modifier passes validation

#### Scenario: Invalid operation values rejected
- **WHEN** a modifier uses operation `DIVIDE`, `SET`, or any string not in the enum
- **THEN** validation raises an error

### Requirement: Target enum defines exactly 6 values
The system SHALL define a `Target` enum with values: `SELF`, `ALLY_SINGLE`, `ALLY_ALL`, `ENEMY_SINGLE`, `ENEMY_ALL`, `GLOBAL`.

#### Scenario: All target values accepted
- **WHEN** a modifier uses any of the 6 defined target values
- **THEN** the modifier passes validation

### Requirement: Modifier tuple structure
The system SHALL define a modifier tuple with these required fields: `stat` (Stat enum), `operation` (Operation enum), `value` (numeric, integer or float), `duration` (integer), `target` (Target enum).

#### Scenario: Complete modifier tuple validates
- **WHEN** a modifier is created with all 5 fields populated with valid enum/type values
- **THEN** the modifier passes validation

#### Scenario: Missing required field rejected
- **WHEN** a modifier is missing any of the 5 required fields (e.g., no `duration`)
- **THEN** validation raises an error

### Requirement: Duration semantics
The `duration` field SHALL use these conventions: `0` means instant (apply and discard), `-1` means permanent (persists until explicitly removed), any positive integer means turn-based (decremented each turn, purged at 0).

#### Scenario: Instant modifier (duration 0)
- **WHEN** a modifier has `duration: 0`
- **THEN** the modifier is valid and semantically represents a one-time application

#### Scenario: Permanent modifier (duration -1)
- **WHEN** a modifier has `duration: -1`
- **THEN** the modifier is valid and semantically represents a persistent effect

#### Scenario: Turn-based modifier (duration > 0)
- **WHEN** a modifier has `duration: 3`
- **THEN** the modifier is valid and semantically represents a 3-turn effect

#### Scenario: Invalid duration rejected
- **WHEN** a modifier has `duration: -2` or any negative value other than -1
- **THEN** validation raises an error

### Requirement: Stacking rule field
Each modifier SHALL have an optional `stacking` field with values: `stack`, `replace`, `max`. Default is `replace`. When `replace`, re-applying the same modifier refreshes duration without stacking value. When `stack`, values accumulate. When `max`, only the highest value is kept.

#### Scenario: Default stacking is replace
- **WHEN** a modifier is created without a `stacking` field
- **THEN** the modifier defaults to `replace` stacking behavior

#### Scenario: Explicit stacking values accepted
- **WHEN** a modifier specifies `stacking` as `stack`, `replace`, or `max`
- **THEN** the modifier passes validation

### Requirement: Resolution order specification
The system SHALL document that modifiers resolve in this strict order: (1) collect all FLAT_ADD and FLAT_SUB, sum them, apply to base value; (2) collect all PCT_ADD and PCT_SUB, sum percentages, apply to post-flat value; (3) apply MULTIPLY operations sequentially. Formula: `result = (base + flat_sum) * (100 + pct_sum) / 100`, then sequential multiplicative application.

#### Scenario: Flat then percentage resolution
- **WHEN** base HP is 100, with modifiers FLAT_ADD 20 and PCT_ADD 50
- **THEN** result is `(100 + 20) * (100 + 50) / 100 = 180`

#### Scenario: Multiple flat modifiers sum
- **WHEN** base Power is 10, with modifiers FLAT_ADD 5 and FLAT_SUB 3
- **THEN** flat sum is +2, result is `(10 + 2) = 12` (before any percentage)

#### Scenario: Percentage on zero base
- **WHEN** base Defense is 0, with modifier PCT_ADD 50
- **THEN** result is `(0 + 0) * (100 + 50) / 100 = 0` (percentage cannot create value from nothing)

#### Scenario: Multiplicative applies sequentially after percentage
- **WHEN** base Speed is 100, with FLAT_ADD 10, PCT_ADD 20, and MULTIPLY 1.5
- **THEN** post-flat is 110, post-pct is `110 * 120/100 = 132`, final is `132 * 1.5 = 198`

#### Scenario: Multiple multiplicative modifiers chain
- **WHEN** a stat has MULTIPLY 2.0 and MULTIPLY 0.5 applied
- **THEN** they apply sequentially: `value * 2.0 * 0.5` (order matters)
