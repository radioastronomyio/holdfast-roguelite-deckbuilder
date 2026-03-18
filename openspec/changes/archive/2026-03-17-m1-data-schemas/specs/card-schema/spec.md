## ADDED Requirements

### Requirement: Card base schema
The system SHALL define a card with these required fields: `id` (unique string), `name` (string), `energy_cost` (integer >= 0), `effects` (list of Modifier tuples), `tags` (list of strings), `upgrade_tier` (integer 0-3), `upgrade_paths` (dict mapping branch keys to upgrade definitions, may be empty for tier 3 cards).

#### Scenario: Valid base card
- **WHEN** a card is created with id `"strike_01"`, name `"Strike"`, energy_cost `2`, one FLAT_SUB HP modifier in effects, tags `["attack", "physical"]`, upgrade_tier `0`, and upgrade_paths with tier 1 branches
- **THEN** the card passes validation

#### Scenario: Missing effects array rejected
- **WHEN** a card is created without an `effects` field
- **THEN** validation raises an error

#### Scenario: Negative energy cost rejected
- **WHEN** a card has `energy_cost: -1`
- **THEN** validation raises an error

#### Scenario: Zero energy cost accepted
- **WHEN** a card has `energy_cost: 0` (like Deep Focus)
- **THEN** the card passes validation

### Requirement: Card effects are modifier tuples
Every entry in a card's `effects` array SHALL be a valid Modifier tuple. Card effects inherit all modifier validation rules (stat enum, operation enum, target enum, duration semantics).

#### Scenario: Multi-effect card validates
- **WHEN** a card has effects `[{stat: HP, operation: FLAT_SUB, value: 8, duration: 0, target: ENEMY_SINGLE}, {stat: Speed, operation: PCT_SUB, value: 100, duration: 1, target: ENEMY_SINGLE}]` (Shield Bash pattern)
- **THEN** each effect validates individually and the card passes validation

### Requirement: Power interaction documented in schema
The card schema SHALL include a description field noting that a character's Power stat adds directly to damage effects at resolution time. A Power 8 character playing a FLAT_SUB HP card with value 12 deals 20 damage. This is resolver behavior (M2), not schema enforcement, but the schema MUST document it.

#### Scenario: Card schema includes power interaction note
- **WHEN** the card Pydantic model is inspected
- **THEN** the model or its effects field includes documentation about Power stat interaction

### Requirement: Upgrade tree structure
The system SHALL define upgrade trees as a dict keyed by branch identifiers (e.g., `"1A"`, `"1B"`, `"2A_from_1A"`). Each entry SHALL contain: `added_effects` (list of Modifier tuples appended to the card), `prerequisite` (branch key or null for tier 1), `tier` (integer 1-3), and `exclusions` (list of branch keys that become unavailable when this branch is chosen).

#### Scenario: Tier 1 branches have no prerequisite
- **WHEN** an upgrade entry has tier `1` and prerequisite `null`
- **THEN** the entry passes validation

#### Scenario: Tier 2 branch requires tier 1 prerequisite
- **WHEN** an upgrade entry has tier `2` and prerequisite `"1A"`
- **THEN** the entry passes validation only if `"1A"` exists in the same tree

#### Scenario: Tier 2 branch with missing prerequisite rejected
- **WHEN** an upgrade entry has tier `2` and prerequisite `"1C"` but `"1C"` does not exist in the tree
- **THEN** validation raises an error

#### Scenario: Exclusions reference valid branches
- **WHEN** an upgrade entry has exclusions `["1B"]`
- **THEN** `"1B"` MUST exist as a key in the same upgrade tree

### Requirement: Economy vs damage exclusionary rule
Upgrade branches at the same tier SHALL NOT pit economy manipulation (energy cost reduction, energy generation) against flat damage increases. If Branch A provides an economy benefit, Branch B MUST offer a mechanical subversion (AoE targeting, Defense bypass, debuff application, duration extension) rather than raw damage scaling.

#### Scenario: Valid branch pairing — shred vs economy
- **WHEN** tier 1 Branch A adds Defense PCT_SUB (shred) and Branch B reduces energy cost
- **THEN** this pairing is valid (mechanical subversion vs economy)

#### Scenario: Invalid branch pairing — damage vs economy
- **WHEN** tier 1 Branch A adds HP FLAT_SUB +10 (raw damage) and Branch B reduces energy cost to 0
- **THEN** this pairing violates the exclusionary rule

### Requirement: Initial card set from GDD
The system SHALL include 10-15 base cards with complete upgrade trees. The initial set MUST include at minimum these cards from the GDD: Arcane Strike (single target damage), Immolate (DoT), Shield Bash (damage + stun via Speed zeroing), Sweeping Blade (AoE), Phalanx (Defense buff), Adrenaline (Speed buff), Cleanse (heal + purge), Deep Focus (energy battery), Acid Flask (Defense shred). Hazard cards (Tripwire, Miasma) are region-played and stored separately from the player card pool.

#### Scenario: All GDD example cards present
- **WHEN** the base cards JSON is loaded
- **THEN** it contains at least 9 player cards matching the GDD examples, each with valid effects and upgrade trees

#### Scenario: Hazard cards stored separately
- **WHEN** hazard cards (Tripwire, Miasma) are defined
- **THEN** they are NOT in the player card pool file but in a separate hazard cards section or file

#### Scenario: Every base card has upgrade paths
- **WHEN** any base card (tier 0) is loaded
- **THEN** it has at least 2 tier-1 branches in its upgrade_paths
