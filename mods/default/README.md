# Default Mod

This is the default content mod for Holdfast. All game content is loaded from this directory.

## Structure

```
flavor/
├── given_names.json          # First names for character generation
├── archetypes.json           # Character archetype/class labels
├── action_verbs.json         # Attack card name second words
├── region_adjectives.json    # Region name first words
├── region_nouns.json         # Region name second words
├── element-stat-map.json     # Maps stats to element pools
└── epithet-conditions.json   # Condition-based epithet assignment
```

## Pool Minimum Requirements

All pools must meet minimum counts:
- `given_names.json`: >= 60 entries
- `archetypes.json`: >= 20 entries
- `action_verbs.json`: >= 30 entries
- `region_adjectives.json`: >= 30 entries
- `region_nouns.json`: >= 30 entries
- `epithet-conditions.json`: >= 20 entries

## Epithet Conditions

Epithets are assigned based on character stat distributions. Two condition types:

**Type 1**: Single stat threshold
```json
{
  "epithet": "the Strong",
  "conditions": [{"type": 1, "stat": "power", "op": ">=", "value": 70}],
  "pool": "default"
}
```

**Type 2**: Two-stat condition with logic
```json
{
  "epithet": "the Volatile",
  "conditions": [{
    "type": 2,
    "stat_a": "power", "op_a": ">=", "value_a": 75,
    "logic": "XOR",
    "stat_b": "defense", "op_b": "<=", "value_b": 25
  }],
  "pool": "rare"
}
```

Operators: `>=`, `<=`, `>`, `<`, `=`, `<>` (not equal)
Pool tiers: `default` (standard), `rare` (reduced weight for memorable outliers)

## Element-Stat Mapping

Maps each of the 5 Stats to default and rare element pools. Used for attack card names and resistance flavor text.

See `element-stat-map.json` for the mapping.
