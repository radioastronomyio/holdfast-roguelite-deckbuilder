<!--
---
title: "Holdfast — Game Design Document"
description: "Complete design specification for a browser-based roguelite deckbuilder with procedural campaign generation"
author: "CrainBramp + Claude"
date: "2026-03-02"
version: "1.0"
status: "Design Complete — Pre-Implementation"
tags:
  - type: game-design-document
  - domain: [game-dev, card-game, roguelite, incremental]
  - tech: [react, python, json]
related_documents:
  - "GDR Research Output (Gemini Deep Research, March 2026)"
  - "Orbweaver Simulation Brief (ml-orbweaver-roguelite)"
---
-->

# Holdfast — Game Design Document

**Domain:** Game Development — Browser-Based Roguelite Deckbuilder
**Status:** Design Complete — Pre-Implementation
**Date:** 2026-03-02
**Version:** 1.0

---

## Vision

Holdfast is a browser-based card game where every mechanic — combat, exploration, upgrades, strategy — runs on a single universal modifier engine. The player inherits an outpost on the edge of hostile territory and must conquer 6 procedurally generated regions to win. Every campaign is a unique strategic puzzle dealt by the procedural generator. Some seeds are brutal. Some are unwinnable. The game's identity lives in that variance — not guaranteed fairness, but interesting decisions under uncertainty.

> **Kernel concept:** A finite-campaign roguelite deckbuilder where everything is modifier arrays on a 5-stat model, every card has a trade-off, and the procedural generation can absolutely kill you.

---

## Reference Games and Design Lineage

| Game | What We Take | What We Leave |
|------|-------------|---------------|
| Soda Dungeon | Idle dungeon loop, party stable, incremental progression | Infinite prestige loops, cheesy tone |
| Darkest Dungeon | Attrition pressure, environmental hazards as modifiers, tone | Stress as separate system, positional lane combat |
| Across the Obelisk | Card upgrade paths (add effects, not just scale numbers), cooperative card combat | Multiplayer focus, fixed characters |
| Legend of Keepers | Traps and hazards as pure modifier encounters, reverse-dungeon structure | Defending (we're attacking), corporate comedy |
| Risk | Strategic map control, incomplete information, territory-based power growth | Dice combat, multiplayer |
| FTL | Procedural map with branching paths, resource scarcity, sector-based difficulty | Real-time pause combat, ship management |

**Lineage:** This design evolved through multiple conversations exploring dungeon crawlers, DD-clones, Dungeons of Daggorath remakes, and Orbweaver's Monte Carlo simulation approach. The card game format was chosen because it is the most agent-friendly implementation path — pure state machines and data, no physics, no real-time input, no animation dependencies. Validated via Gemini Deep Research (NSB-bounded, March 2026).

---

## Core Design Principle: Everything Is Modifiers

The entire game runs on one data structure. A card, a hazard, a character passive, an outpost upgrade, a region effect, a world deck trade-off — all are arrays of modifiers applied to the same 5-stat model. The engine has one resolver. Flavor text is cosmetic. The math is the game.

### The 5-Stat Model

| Stat | Role | Design Notes |
|------|------|-------------|
| **HP** | Survival metric. Zero = dead. | Absolute resource — cannot be regenerated above max without explicit modifier |
| **Power** | Base scalar for offensive output. Adds into card damage/effectiveness. | A Power 5 character playing a 3-damage card deals 8. Power amplifies all offensive cards. |
| **Speed** | Determines turn frequency via Charge Time system | Most volatile stat. Percentage buffs to Speed are exponentially powerful — must be capped or taxed (see Pitfalls) |
| **Defense** | Subtractive buffer against incoming flat HP damage | Operates before HP reduction is finalized. Does not mitigate percentage-based HP loss. |
| **Energy** | Per-turn action budget. Refreshes fully each turn. | The sole economic bottleneck. Full hand visible every turn — Energy is the only constraint on what you play. |

### The Modifier Tuple

Every effect in the game is expressed as:

```json
{
  "stat": "HP | Power | Speed | Defense | Energy",
  "operation": "FLAT_ADD | FLAT_SUB | PCT_ADD | PCT_SUB | MULTIPLY",
  "value": 15,
  "duration": 0,
  "target": "SELF | ALLY_SINGLE | ALLY_ALL | ENEMY_SINGLE | ENEMY_ALL | GLOBAL"
}
```

- `duration: 0` = instant (apply and discard)
- `duration: -1` = permanent (persists until explicitly removed)
- `duration: >0` = turns (decremented each turn, purged at 0)

### Resolution Order

All modifiers resolve in strict priority: **Base Value → Flat Modification → Percentage Modification → Multiplicative Scaling**

This prevents percentage buffs from yielding zero impact on base-zero stats and ensures mathematical stability. Identical to Orbweaver's `calculate_stat()` pattern: `(base + flat_sum) * (100 + add_pct_sum) // 100`, then sequential multiplicative application.

---

## Campaign Structure

### The Macro Loop

1. **Start:** Player has an outpost, one character, and a fog-covered map of 6 regions. One random region is revealed at Research Level 1 (initial intelligence — a crapshoot).
2. **Research:** Spend resources/time to reveal region details in layers (type → modifiers → encounter details → boss mechanics).
3. **Assault:** Select a region. Choose a party (max 3-4 characters from roster). Progress through 3 narrative encounters.
4. **Conquer:** Clear the region. All participating characters receive a meta-upgrade + N card upgrades (N = participant count). Draft 1 of 3 procedurally generated new characters.
5. **World Phase:** 3 rounds of world deck cards (all trade-offs). Earned skips from conquered regions let you dodge bad draws.
6. **Repeat** until all 6 regions cleared or campaign fails.
7. **Win Condition:** Clear all 6 regions. Performance metric: total time/turns.
8. **Prestige (optional/future):** Carry character roster into a new procedurally generated campaign with harder parameters.

### Non-Linear Conquest

The player chooses which region to assault next. This is the primary strategic decision space. Region order matters because:

- Conquered regions grant meta-modifiers that affect all future battles
- Research lets you see what's coming (if you invest in it)
- Some regions are easy picks that grant powerful bonuses; others are brutal but offer game-changing rewards
- Low-hanging fruit in a bad-modifier region might still be high-level
- You can rush blind or research everything — both are valid strategies with trade-offs

### The Unwinnable Seed Philosophy

The procedural generator does not guarantee solvable campaigns. Some seeds produce modifier stacks that are extremely difficult or mathematically impossible to overcome. This is intentional and is the game's identity. The simulation targets a 40-70% win rate distribution across seeds — not 100% solvability.

---

## Region Design

### Narrative Arc (3 Encounters per Region)

Each region follows a fixed narrative template with procedurally generated content:

| Section | Name | Role | Encounter Pool |
|---------|------|------|----------------|
| 1 | **The Approach** | Traveling to the region. Environmental storytelling. | Hazard (60%), Event (40%). Rarely combat. |
| 2 | **The Settlement** | Arriving at the population center. Preparation phase. | Combat (70%), Event (30%). Merchants, negotiations, ambushes. |
| 3 | **The Stronghold** | The region's core challenge. Always a fight. | Elite Combat (100%). Boss encounter scaled to region difficulty. |

### Encounter Types

**Combat:** Enemies with stats play cards against you. Standard card-vs-card resolution. The full combat loop.

**Hazard:** The environment "attacks" with modifier arrays. One-sided — you play mitigation cards or eat the damage. A toxic swamp applying -2 HP/turn to all characters is mechanically identical to a poison enemy, but there's no enemy HP to deplete. You survive and move on, carrying damage into the next encounter.

**Event:** A trade-off choice presented mid-region. "You find a wounded deserter — spend 3 HP from one character to recruit a temporary ally for the boss fight, or ignore them." "A merchant offers to swap one of your cards for a random card from their stock." Same modifier math, different framing.

### Region Properties

Each procedurally generated region has:

- **Type:** Determines narrative flavor and encounter pool weights (Ashen Wastes, Whispering Thicket, Iron Citadel, Frozen Depths, etc.)
- **Modifier Stack:** Persistent modifiers active during all encounters in this region (e.g., "all enemies +15% Defense", "healing reduced 50%", "-2 HP/turn to all from toxic atmosphere")
- **3 Encounters:** Generated from weighted pools per the narrative arc
- **Meta-Reward:** A permanent campaign-wide modifier granted to all characters who participated in clearing the region
- **Character Draft Pool:** 3 procedurally generated characters to choose from upon conquest
- **Research Layers:** Information revealed incrementally (Level 1: region type, Level 2: primary modifier, Level 3: encounter details, Level 4: boss mechanics)

### Example Regions (from GDR)

| Region | Encounter 1 (Approach) | Encounter 2 (Settlement) | Encounter 3 (Stronghold) | Meta-Reward |
|--------|----------------------|------------------------|------------------------|-|
| The Ashen Wastes | Hazard: Ash Storm (-15% Speed all) | Combat: Scavenger Patrol | Combat: Warlord Vanguard | +Defense to all roster |
| Whispering Thicket | Event: Lost Caravan (Trade HP for Power) | Hazard: Toxic Spores (-HP over time) | Combat: Fungal Behemoth | Research cost halved |

### Region Meta-Reward Archetypes

| Type | Example | Strategic Impact |
|------|---------|-----------------|
| Combat bonus | Conquered fortress grants +1 Defense to all characters | Makes subsequent hard regions survivable |
| Economic bonus | Conquered trading post reduces outpost upgrade costs | Accelerates campaign-wide power curve |
| Intelligence bonus | Conquered mage tower grants free Level 1 research on all unscouted regions | Opens strategic planning dramatically |
| Draft bonus | Conquered barracks shows 4 character draft options instead of 3 | Improves roster quality |

---

## Character System

### Procedural Generation

Characters are not fixed classes. Every character is procedurally generated with:

- **Name:** Generated from word banks — `[First Name] + [Title/Archetype] + [Origin]`. Example: "Alvino, Ice Mage from the Mountains of Kud"
- **Base Stats:** Randomized within bounds across the 5-stat model. Stat arrays create natural archetypes without explicit class labels. High HP/Defense/low Speed = tank. High Power/Speed/low HP = glass cannon.
- **Innate Passive:** One permanent modifier injected into the combat resolver at encounter start. The "Ice Mage" part means cold-typed hazards deal reduced damage. This is what makes party composition matter — your roster's passives determine which regions are easy and which are deadly.

### Example Characters (from GDR)

| Name | Base Stats (HP/Pwr/Spd/Def/Ene) | Innate Passive |
|------|----------------------------------|----------------|
| Vanguard Sentinel | 140 / 12 / 80 / 20 / 3 | +15% Defense permanent (tanky, slow, energy-starved) |
| Ember Mage | 65 / 28 / 115 / 5 / 4 | +20% Power vs enemies below 50% HP (finisher, fragile) |
| Field Tactician | 85 / 15 / 105 / 12 / 5 | +1 Energy permanent (flexibility, jack-of-all-trades) |

### Character Progression

Characters are **not locked** when a region is conquered. The full roster remains active and continues developing.

- **Meta-upgrades:** All characters who participated in a region clear receive a powerful permanent modifier (the region's meta-reward).
- **Card upgrades:** N card upgrades are granted per region clear, where N = number of participants. These follow the AtO model — add effects to existing cards, not just scale numbers.
- **Party selection pressure:** Max 3-4 characters per battle. By Region 4+, you have more characters than battle slots. Only participants get upgrades. Do you stack your best team (rich-get-richer) or spread upgrades across the roster (balanced investment)?

---

## Card System

### Card Structure

Every card is a modifier array with metadata:

```json
{
  "id": "strike_01",
  "name": "Strike",
  "energy_cost": 2,
  "effects": [
    { "stat": "HP", "operation": "FLAT_SUB", "value": 12, "duration": 0, "target": "ENEMY_SINGLE" }
  ],
  "tags": ["attack", "physical"],
  "upgrade_tier": 0,
  "upgrade_paths": { "1A": "...", "1B": "..." }
}
```

Power interaction: A character's Power stat adds directly to damage effects. A Power 8 character playing a card with `FLAT_SUB HP value: 12` deals `12 + 8 = 20` damage (before Defense mitigation).

### Shared Card Pool

All characters draw from a shared generic card pool. There are no class-specific cards in v1. Card effectiveness varies by character stats — a high-Power character makes attack cards devastating, a high-Energy character can play more cards per turn, a high-Speed character acts more frequently.

### Example Cards (from GDR, 10 cards)

| Card | Energy | Target | Effect | Notes |
|------|--------|--------|--------|-------|
| Arcane Strike | 2 | ENEMY_SINGLE | HP FLAT_SUB 15, instant | Clean single-target damage |
| Immolate | 1 | ENEMY_SINGLE | HP FLAT_SUB 4, 3 turns | Damage over time. Low upfront, high total. |
| Shield Bash | 2 | ENEMY_SINGLE | HP FLAT_SUB 8 + Speed PCT_SUB 100% for 1 turn | Damage + stun (removes next turn via Speed zeroing) |
| Sweeping Blade | 3 | ENEMY_ALL | HP FLAT_SUB 12, instant | AoE. Expensive but clears swarms. |
| Phalanx | 2 | ALLY_SINGLE | Defense FLAT_ADD 15, 2 turns | Heavy mitigation. Timing matters. |
| Adrenaline | 1 | ALLY_SINGLE | Speed PCT_ADD 30%, 3 turns | Pushes character up turn order. Volatile. |
| Cleanse | 1 | ALLY_SINGLE | HP FLAT_ADD 10, instant + purge negatives | Heal + removes active debuffs |
| Deep Focus | 0 | SELF | Energy FLAT_ADD 3, instant | Economic battery. Play more cards this turn. |
| Acid Flask | 1 | ENEMY_ALL | Defense PCT_SUB 25%, 2 turns | Shred. Amplifies all subsequent flat attacks. |
| Tripwire (Hazard) | 0 | ALLY_SINGLE | Power PCT_SUB 50%, 2 turns | Hazard card played by region. No player choice. |
| Miasma (Hazard) | 0 | ALLY_ALL | HP FLAT_SUB 2, permanent | Permanent environmental attrition. Must end encounter fast. |

### Card Upgrade System (AtO Model)

Upgrades **add effects** to existing cards rather than replacing or scaling base values. This prevents early cards from becoming obsolete while avoiding exponential power creep.

Cards have a 3-tier upgrade tree with branching choices at each tier. Each upgrade appends a secondary modifier to the card's effect array. Branches are designed to be contextually dependent — the "correct" choice depends on the procedural seed, not a solved meta.

**Exclusionary rule:** If Branch A provides economic manipulation (Energy cost reduction), Branch B must offer a comparable mechanical subversion (AoE targeting, Defense bypass, debuff application). Economy manipulation must never be directly pitted against flat damage increases — economy always wins in card games (see Pitfalls).

### Example Upgrade Tree: Strike

| Tier | Branch A | Branch B |
|------|----------|----------|
| Base | HP FLAT_SUB 12, ENEMY_SINGLE, Cost 2 | — |
| 1 | Add Defense PCT_SUB 15%, 2 turns (shred) | Reduce Energy Cost to 0 |
| 2 (from 1A) | Increase shred duration to 4 turns | Add HP FLAT_SUB 5 DoT, 2 turns |
| 3 (Capstone) | Target becomes ENEMY_ALL (AoE) | Base damage increased to 25 |

At Tier 3, Branch 3A turns Strike into an AoE shred tool (crowd control). Branch 3B turns it into a single-target nuke (boss killer). Neither is universally better — it depends on whether the next region features swarms or elites.

---

## Combat System

### Turn Order: Charge Time (CT)

Rather than static round-robin, each entity has a continuous CT variable. Each tick, the entity's current Speed is added to their CT. When CT ≥ 100, the entity takes a turn. After acting, CT is decremented by 100.

**Effect:** A Speed 150 character takes 3 turns for every 1 turn a Speed 50 character takes. Speed becomes the most powerful and volatile stat in the game.

**Tie-breaking:** If multiple entities cross 100 CT simultaneously, highest CT overflow goes first.

### Combat Flow (Per Turn)

1. **Process over-time effects:** Tick down durations. Apply DoT/HoT. Purge expired modifiers. Recalculate stats.
2. **Check death from DoT:** If entity died from over-time effects, skip their action.
3. **Refresh Energy:** Reset to base Energy + permanent modifiers. No carry-over between turns.
4. **Action phase:** Player selects cards to play (via hotkeys 1-N or click). Each card costs Energy. Modifiers resolve immediately through the universal engine.
5. **Consume CT:** Deduct 100 from entity's CT.
6. **Repeat** until one side is eliminated.

### The Hand

- Full hand is always visible. No draw RNG in combat — all randomness lives in the campaign layer.
- Cards are laid out horizontally. Hotkeys 1-6 (or controller buttons) select cards. Played cards flip face-down but stay in position.
- At end of round (all entities have acted), cards redeal — flip animation signifies new hand.
- Energy is the only constraint on what you play per turn.

### Encounter Resolution (Unified)

The same ResolverEngine handles all three encounter types:

- **Combat:** Enemy entities have CT, stats, and cards. They act on their turns using AI heuristics (pick valid action, score with simple heuristic, pick max). Full back-and-forth.
- **Hazard:** Region "plays" modifier cards against the party automatically. No enemy HP. Player plays mitigation cards or absorbs damage. Encounter ends after hazard duration expires.
- **Event:** Present trade-off choices. Player selects. Modifiers applied. Move on.

---

## World Phase (Between Regions)

### The World Deck

Between region assaults, the player gets 3 rounds of world deck cards. The world deck uses the **same card UI and hotkey interface** as combat — everything is cards.

**Critical rule: Every world card has both an upside and a downside.** There are no free lunches. Every benefit comes with a cost. The strategic depth comes from evaluating which costs are tolerable in the context of your current roster, upcoming region, and campaign state.

### Skip Mechanic

Each conquered region earns 1 skip token. Skips allow the player to dodge a bad world card hand. Early game (0 conquered regions) = 0 skips, you eat whatever the world deck deals. By Region 5, you've stockpiled up to 4 skips and can be highly selective. This is the only way to avoid bad world draws — a natural power curve that rewards progress without stat inflation.

### Example World Cards (20 cards, from GDR)

| Card | Upside | Downside | Strategic Context |
|------|--------|----------|-------------------|
| Forced March | +30% Speed (All) | -20% HP (All) | Strong for alpha-strike builds. Fatal against attrition encounters. |
| Rations Cut | +2 Energy base max | -25% Power (All) | Ideal for utility/defense rosters that play many cheap cards. |
| Reckless Assault | +40% Power (All) | -40% Defense (All) | Glass cannon play. Needs Speed advantage to kill before taking hits. |
| Heavy Armor | +30 Defense (All) | -30% Speed (All) | Trivializes swarms. Devastating against fast enemies. |
| Blood Magic | Card costs -1 Energy | -8 HP per card played | Extremely dangerous in long fights. Degenerates with heal-on-cast upgrades. |
| Fog of War | Enemies start -50% Power | Roster starts Blind (no targeting Turn 1) | Reduces burst threat but prevents precise combos round 1. |
| Overclocked | +60% Speed (All) | Energy does not refresh Turn 2 | All-in Turn 1 dependency. If enemies survive, you skip round 2. |
| Vampiric Contract | +15 HP heal on kill | Base max HP -30% | Excellent for multi-enemy nodes. Mathematically poor vs single bosses. |
| Scavenger's Greed | Reward output +50% | Stronghold Elite +50% Power | Standard greed pick. Obvious if snowballing, run-ending if struggling. |
| Hyper-Metabolism | +50% HP (All) | Status effect duration ×2 | Massive survivability but DoT hazards become fatal. |
| Glass Cannon | +100% Power (All) | HP permanently set to 1 | Ultimate risk. Needs extreme Speed + Defense spam. Instant loss to pre-emptive hazards. |
| Pacifism Protocol | +50 Defense (All) | Cannot play Attack cards Turn 1 | Excellent for buff setup. Useless for aggro builds. |
| Leyline Tap | Energy refreshes to Max+5 | Lose 10% current HP per turn | High-octane attrition. Forces 3-turn kills or self-inflicted death. |
| Tunnel Vision | +50% Power vs Elites | -50% Power vs Minions | Highly specific. Boss-focused or swarm-focused region determines value. |
| Unstable Mutagen | Random stat +50% | Random stat -50% | True RNG. Often skipped. Trap card for desperate runs. |
| Barricaded | Start with +100 Defense | Lose 20 Defense per turn | Incredible for surviving ambushes. Falls apart in prolonged battles. |
| Cursed Relic | +1 character drafted early | All enemies +15% stats | Accelerates roster growth at severe immediate difficulty cost. |
| Martyrdom | Lowest HP ally +200% Defense | Highest HP ally -50% HP | Requires precise roster management to manipulate who gets buff vs penalty. |
| Temporal Shift | +100% Speed Turn 1 | -50% Speed Turns 2-4 | First-strike guaranteed. Enemy takes multiple consecutive turns after. |
| Echo Chamber | Played cards trigger twice | Card Energy costs ×2 | Shifts paradigm from many cheap cards to one expensive mega-card per turn. |

---

## Outpost System

The outpost is the player's persistent base. Upgrades come through world deck cards and region meta-rewards. All outpost upgrades are campaign-scoped (reset between campaigns; prestige is future scope).

Outpost upgrades are expressed as — yes — permanent modifiers applied to the roster's base stats or to campaign-level parameters:

- **Forge:** +2 Power to all characters (FLAT_ADD, permanent)
- **Watchtower:** Free Level 1 research on one random unscouted region
- **Infirmary:** +10% HP to all characters (PCT_ADD, permanent)
- **War Room:** Party size +1 for battles
- **Library:** Research costs reduced by 25%

**Pitfall warning (from GDR):** Outpost upgrades must apply to Base Stats, while world card and region modifiers apply to Current Stats post-calculation. If outpost upgrades inflate base HP by +500, then a world card costing "-20% HP" becomes meaningless. Percentage-based downsides must remain threatening throughout the campaign.

---

## UI and Input Design

### Universal Card Interface

All game phases use the same interaction model: a horizontal hand of cards, hotkeys 1-N to select, effects resolve. The player learns one UI pattern and it works everywhere — combat, world phase, outpost, events.

### Input Model

- **Keyboard:** 1-6 for card selection. Additional hotkeys for targeting (if required by card). Z for undo.
- **Controller:** Face buttons map to card slots. Bumpers for page/targeting.
- **Mouse/Touch:** Click cards directly.
- **Targeting:** "Press card, then press 1-N to pick target." Auto-target for single-viable-target effects.

### Card Animation

Cards are positionally static. When played, a card flips face-down but stays in its slot. At end-of-round, a brief flip animation on all cards signifies the redeal. No drag-and-drop, no card movement, no hand reshuffling. Muscle memory builds fast.

### Phase Screens

| Phase | Display |
|-------|---------|
| World Map | Procedural map with fog, region icons, research status indicators. Click region to assault or research. |
| Encounter (Combat) | Enemy entities top, party entities bottom, card hand horizontal center-bottom. Combat log sidebar. |
| Encounter (Hazard) | Hazard effect display top, party entities bottom, mitigation cards in hand. |
| Encounter (Event) | Trade-off card choices displayed as selectable cards. |
| World Deck | 3 rounds of world cards dealt as a hand. Select or skip. |
| Outpost | Roster management, upgrade altar for card upgrades, research console. |

---

## Technical Architecture

### Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React (browser) | Playable game. Single-file components, Tailwind CSS, hotkey input. |
| Simulation | Python | Monte Carlo balance testing. Card math validation. Degenerate combo detection. |
| Data | Shared JSON | Card definitions, character pools, region templates, encounter pools. Consumed by both frontend and sim. |
| State | Redux-style reducer | Deterministic, serializable game state. Phase-based finite state machine. |

### Why React, Not a Game Engine

A card game is fundamentally state management and click targets. No physics, no collision, no sprite animation, no real-time game loop. React was built for exactly this. Agents generate React extremely well. Browser deployment means instant sharing. The pixel art UI pack (2D Pixel Quest) provides assets as sprite sheets that render identically in CSS/Canvas as in any game engine.

### State Machine Phases

```
WORLD_MAP ↔ ENCOUNTER_ACTIVE ↔ OUTPOST_UPGRADE
```

The entire game state is a serializable JSON blob. At any point, `JSON.stringify(gameState)` produces a complete save. `JSON.parse(savedState)` restores it perfectly. No desynchronization possible.

### State Shape (TypeScript)

```typescript
interface GameState {
  run_seed: string;
  current_phase: 'WORLD_MAP' | 'COMBAT' | 'HAZARD' | 'EVENT' | 'WORLD_DECK' | 'OUTPOST';
  campaign_map: Region[];
  active_roster: Character[];
  party_selection: string[];  // character IDs for current region assault
  inventory_deck: Card[];
  world_modifiers: Modifier[];
  outpost_upgrades: Modifier[];
  skips_available: number;
  regions_cleared: number;
  encounter_state: {
    turn_queue: string[];
    enemies: Entity[];
    combat_log: ActionTuple[];
    active_entity_id: string | null;
    hazard_modifiers: Modifier[];
  };
  state_history: GameState[];  // for undo via Memento pattern
}
```

### Component Architecture (from GDR)

```jsx
<App>
  <KeyboardController hotkeys={{ '1-6': playCardIndex, 'Z': undoLastAction }}>
    <StateRouter phase={current_phase}>
      <Phase_WorldMap>
        <CampaignGraph nodes={campaign_map} />
        <ResearchPanel />
      </Phase_WorldMap>
      <Phase_WorldDeck>
        <WorldDeckSelector cards={drawn_world_cards} skips={skips_available} />
      </Phase_WorldDeck>
      <Phase_Encounter>
        <CombatArena>
          <EntityRenderer type="ENEMY" data={enemies} />
          <EntityRenderer type="PARTY" data={party} />
        </CombatArena>
        <HandController>
          {hand.map((card, i) => (
            <CardComponent key={card.id} data={card} hotkey={i + 1} />
          ))}
        </HandController>
      </Phase_Encounter>
      <Phase_Outpost>
        <RosterManagement characters={active_roster} />
        <UpgradeAltar deck={inventory_deck} />
        <ResearchConsole regions={campaign_map} />
      </Phase_Outpost>
    </StateRouter>
  </KeyboardController>
</App>
```

### Engine Separation

**Critical:** The ResolverEngine operates entirely independently of React. It calculates the full turn synchronously and outputs an array of ActionTuples. React acts as a "dumb renderer" consuming tuples sequentially with CSS transitions/timeouts. This prevents UI state desynchronization — the engine is always ahead, the UI is always catching up visually.

---

## Balance Simulation (Python)

### Goals

The simulation validates **card math and decision quality**, not seed solvability.

| Metric | Healthy Range | Degenerate Signal |
|--------|--------------|-------------------|
| Win rate across 10K seeds | 40-70% | <30% (too hard) or >80% (too easy) |
| Upgrade path pick rate | No branch >70% in winning runs | Any branch >85% = false choice |
| World card skip rate | Varies by context | Any card skipped >90% = too punishing. Any card always picked = too cheap. |
| Speed stat ceiling | Characters act ≤3× per enemy cycle | Any character acting 5×+ = Speed collapse |
| Card combo win rate | No 2-card combo >90% win rate | Degenerate combo detected |

### Simulation Framework

Three AI heuristics play thousands of campaigns:

- **Aggressive:** Always picks highest-damage cards. Rushes regions. Minimal research.
- **Defensive:** Prioritizes mitigation and healing. Full research before assault.
- **Balanced:** Scores cards by context. Moderate research. Adapts party composition.

If all three heuristics converge on the same strategy, the game lacks meaningful choice. If one heuristic dominates (>80% win rate vs others <40%), the balance is off.

### Simulation Pipeline

```
Generate seed → Build campaign map → For each region:
  → Select party (heuristic-dependent)
  → Resolve 3 encounters via ResolverEngine
  → Apply meta-rewards + card upgrades
  → Resolve 3 world deck rounds
→ Record outcome + all intermediate state
→ Aggregate across 10K runs
→ Output: win rate distribution, upgrade dominance, combo detection, world card analysis
```

---

## Known Pitfalls and Mitigations (from GDR)

| # | Pitfall | Why It Happens | Mitigation |
|---|---------|---------------|------------|
| 1 | **Speed collapse** | PCT_ADD to Speed scales exponentially with CT system. +100% Speed = 2× turns = permanent stun + 2× damage. | Cap Speed percentage modifiers. Or: introduce Fatigue (flat Energy cost increase when taking multiple turns per enemy CT cycle). |
| 2 | **Trade-off nullification** | Outpost upgrades inflate base stats so much that percentage-based world card downsides become irrelevant. | Outpost upgrades apply to Base Stats. World/region modifiers apply to Current Stats post-calculation. Enforce numerical ceilings on incremental progression. |
| 3 | **Economy manipulation dominance** | "Energy Cost -1" or "Draw +1 card" upgrades always beat flat damage increases in card games. | Never pit economy manipulation against raw damage in the same upgrade branch. Economy vs. mechanical subversion (AoE, Defense bypass, debuff). |
| 4 | **Infinite Defense stacking** | If a Defense buff lasts 3 turns but can be re-cast every 2 turns, Defense stacks infinitely → invulnerability. | Enforce stacking rules in JSON: modifiers either REPLACE identical active modifiers (refreshing duration) or are tagged STACKABLE. Restrict stackability on defensive parameters. |
| 5 | **UI desync** | React async state updates inside combat loops → UI renders frame X+2 while engine calculates frame X. | Engine operates independently. Outputs ActionTuple array. React consumes sequentially with forced delays. Strict separation: math state vs visual rendering. |

---

## Implementation Phases

### Phase 1: Simulation (Python)

Card definitions in JSON. Combat resolver as pure functions. Generate campaigns. Run 10K simulations. Output CSVs with balance metrics. Validate card math, detect degenerate combos, tune modifier values. **No UI.** This is the Orbweaver pattern.

**Agent-implementable:** Yes. Spec-driven. KiloCode + GLM territory.

### Phase 2: Minimal Playable (React)

Cards as rectangles with text. Map as clickable nodes. Combat log showing resolution. Enough to feel whether decisions are engaging when a human chooses instead of a random agent. Ugly but functional.

**Agent-implementable:** Yes. Standard React state management. Card components + hotkey handlers.

### Phase 3: Visual Polish

Pixel art UI pack integration (2D Pixel Quest). Card art, region visuals, animations, sound. The game looks and feels like a game.

**Agent-implementable:** Partially. Asset integration and CSS work is agent-friendly. Art direction requires human judgment.

---

## Scope Boundaries

### In Scope (v1)

- 6-region campaign with procedural generation
- 10-15 base cards with 3-tier upgrade trees
- Procedural character generation with innate passives
- 3 encounter types (combat, hazard, event) on unified resolver
- World deck with 20 trade-off cards
- Research system with layered reveals
- Skip mechanic from conquered regions
- Outpost upgrades (campaign-scoped)
- Party selection (3-4 characters per battle)
- Monte Carlo balance simulation
- React browser frontend with hotkey input
- Seed-based deterministic generation (shareable seeds)

### Out of Scope (v1)

- Prestige system / cross-campaign progression
- Multiplayer or PvP
- Difficulty settings (difficulty comes from seed variance)
- Story, lore, narrative writing
- Audio
- Mobile-specific UI
- Cloud saves / accounts
- Achievements / unlockables

### Future Considerations

- Prestige loop: carry character roster into harder generated campaigns (more regions, nastier modifiers)
- Seed leaderboards: compete on fastest clear of specific seeds
- Additional card pools and upgrade paths
- Physical card game prototype for playtesting
- Controller-first couch mode

---

## Asset Reference

- **UI/Card Art:** [2D Pixel Quest - UI/GUI](https://barely-games.itch.io/2d-pixel-quest-the-uigui) (purchased, includes card templates)
- **Tileset (if needed for map):** [0x72 Dungeon Tileset](https://0x72.itch.io/dungeontileset-ii) (free, community packs)

---

## Document Info

| | |
|---|---|
| Author | CrainBramp + Claude (orchestrator) |
| Created | 2026-03-02 |
| Version | 1.0 |
| Status | Design Complete — Pre-Implementation |

## Sources

- Gemini Deep Research output (NSB-bounded, March 2026) — universal modifier model, card examples, upgrade trees, world deck cards, React architecture, pitfall analysis
- Claude conversation history (Dec 2025 – Mar 2026) — design evolution from DD-clone → incremental → card game, campaign structure, character draft mechanic, region narrative arc, world deck trade-off philosophy
- Orbweaver simulation brief (ml-orbweaver-roguelite) — `calculate_stat()` modifier resolution pattern, Monte Carlo methodology
- Reference games: Soda Dungeon, Darkest Dungeon, Across the Obelisk, Legend of Keepers, FTL, Risk
