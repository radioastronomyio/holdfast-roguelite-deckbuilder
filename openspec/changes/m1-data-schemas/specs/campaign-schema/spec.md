## ADDED Requirements

### Requirement: Region schema
The system SHALL define a region with these required fields: `id` (unique string), `name` (string), `region_type` (string — flavor category like "Ashen Wastes", "Whispering Thicket", etc.), `modifier_stack` (list of Modifier tuples active during all encounters in this region), `encounters` (list of exactly 3 Encounter objects in narrative order: Approach, Settlement, Stronghold), `meta_reward` (a Modifier tuple granted permanently to all participants on conquest), `research_layers` (list of 4 objects representing progressive intel reveals).

#### Scenario: Valid region with 3 encounters
- **WHEN** a region is created with all required fields and exactly 3 encounters
- **THEN** the region passes validation

#### Scenario: Region with wrong encounter count rejected
- **WHEN** a region has 2 or 4 encounters
- **THEN** validation raises an error

#### Scenario: Region modifier stack uses valid modifiers
- **WHEN** a region has modifier_stack `[{stat: HP, operation: FLAT_SUB, value: 2, duration: -1, target: ALLY_ALL}]` (toxic atmosphere)
- **THEN** the modifier stack passes validation

### Requirement: Research layers structure
Each region SHALL have exactly 4 research layers, each with a `level` (1-4), `reveal_type` (string describing what is revealed), and `cost` (integer resource cost). Layer contents: Level 1 = region type, Level 2 = primary modifier, Level 3 = encounter details, Level 4 = boss mechanics.

#### Scenario: Complete research layers
- **WHEN** a region has 4 research layers with levels 1-4
- **THEN** validation passes

#### Scenario: Incomplete research layers rejected
- **WHEN** a region has only 2 research layers
- **THEN** validation raises an error

### Requirement: Encounter schema with type discriminator
The system SHALL define encounters with a `type` discriminator field: `combat`, `hazard`, or `event`. All encounters share: `type`, `narrative_position` (enum: `approach`, `settlement`, `stronghold`), `name` (string), `description` (string). Type-specific fields: Combat adds `enemies` (list of Enemy references) and `enemy_cards` (list of card IDs). Hazard adds `hazard_modifiers` (list of Modifier tuples applied automatically) and `hazard_duration` (integer turns). Event adds `choices` (list of choice objects, each with `description`, `effects` as Modifier list, and `cost` as optional Modifier list).

#### Scenario: Valid combat encounter
- **WHEN** an encounter has type `combat`, narrative_position `stronghold`, and a non-empty enemies list
- **THEN** the encounter passes validation

#### Scenario: Valid hazard encounter
- **WHEN** an encounter has type `hazard`, narrative_position `approach`, hazard_modifiers, and hazard_duration
- **THEN** the encounter passes validation

#### Scenario: Valid event encounter
- **WHEN** an encounter has type `event`, narrative_position `settlement`, and at least 2 choices
- **THEN** the encounter passes validation

#### Scenario: Combat encounter without enemies rejected
- **WHEN** an encounter has type `combat` but empty enemies list
- **THEN** validation raises an error

#### Scenario: Event encounter with single choice rejected
- **WHEN** an encounter has type `event` with only 1 choice
- **THEN** validation raises an error — events MUST present a meaningful trade-off (minimum 2 choices)

### Requirement: Narrative position constraints
The encounter at position 0 (Approach) SHALL have narrative_position `approach`. Position 1 (Settlement) SHALL have narrative_position `settlement`. Position 2 (Stronghold) SHALL have narrative_position `stronghold`. The Stronghold encounter MUST be type `combat` (always a fight per GDD).

#### Scenario: Stronghold must be combat
- **WHEN** a region's third encounter has type `hazard` or `event`
- **THEN** validation raises an error

#### Scenario: Approach allows hazard or event
- **WHEN** a region's first encounter has type `hazard` or `event`
- **THEN** validation passes

### Requirement: World deck card schema
The system SHALL define a world card with: `id` (unique string), `name` (string), `upside` (list of Modifier tuples — the benefit), `downside` (list of Modifier tuples — the cost), `description` (string explaining the trade-off). Both `upside` and `downside` MUST be non-empty — every world card has both a benefit and a cost.

#### Scenario: Valid world card with upside and downside
- **WHEN** a world card has non-empty upside and non-empty downside modifier lists
- **THEN** the card passes validation

#### Scenario: World card with empty downside rejected
- **WHEN** a world card has upside modifiers but `downside: []`
- **THEN** validation raises an error — no free lunches

#### Scenario: World card with empty upside rejected
- **WHEN** a world card has downside modifiers but `upside: []`
- **THEN** validation raises an error — pure penalties are not valid world cards

### Requirement: Initial world deck from GDD
The system SHALL include 20 world deck cards matching the GDD examples. Cards MUST include at minimum: Forced March, Rations Cut, Reckless Assault, Heavy Armor, Blood Magic, Fog of War, Overclocked, Vampiric Contract, Scavenger's Greed, Hyper-Metabolism, Glass Cannon, Pacifism Protocol, Leyline Tap, Tunnel Vision, Unstable Mutagen, Barricaded, Cursed Relic, Martyrdom, Temporal Shift, Echo Chamber.

#### Scenario: All 20 GDD world cards present
- **WHEN** the world deck JSON is loaded
- **THEN** it contains exactly 20 cards with names matching the GDD list

#### Scenario: Each world card has mechanically valid modifiers
- **WHEN** each world card's upside and downside are validated
- **THEN** all modifier tuples pass the modifier-schema validation

### Requirement: Outpost upgrade schema
The system SHALL define an outpost upgrade with: `id` (unique string), `name` (string), `description` (string), `effects` (list of Modifier tuples — all MUST have `duration: -1` for permanent), `cost` (integer resource cost). Outpost upgrades apply to Base Stats (not current stats post-calculation) per GDD Pitfall #2.

#### Scenario: Valid outpost upgrade
- **WHEN** an upgrade has permanent modifiers (`duration: -1`) and a positive cost
- **THEN** the upgrade passes validation

#### Scenario: Non-permanent outpost modifier rejected
- **WHEN** an outpost upgrade has a modifier with `duration: 3`
- **THEN** validation raises an error — outpost upgrades MUST be permanent

#### Scenario: GDD example upgrades present
- **WHEN** the outpost upgrades JSON is loaded
- **THEN** it contains at minimum: Forge (+2 Power all), Watchtower (free research), Infirmary (+10% HP all), War Room (+1 party size), Library (-25% research cost)

### Requirement: Example regions from GDD
The system SHALL include at least 2 example regions matching the GDD: The Ashen Wastes (Ash Storm hazard approach, Scavenger Patrol combat settlement, Warlord Vanguard combat stronghold, meta-reward +Defense) and Whispering Thicket (Lost Caravan event approach, Toxic Spores hazard settlement, Fungal Behemoth combat stronghold, meta-reward research cost halved).

#### Scenario: GDD example regions present and valid
- **WHEN** the example regions JSON is loaded
- **THEN** it contains at least 2 regions with encounters matching the GDD narrative arc pattern
