export const STAT_SCALE = 1000;
export const CT_THRESHOLD = 100 * STAT_SCALE;
export const HAND_SIZE = 5;
export const COMBAT_TURN_CAP = 200;
export const SPEED_PCT_CAP = 75;
export const SPEED_MIN_FLOOR = 10;

export enum Stat {
  HP = "HP",
  Power = "Power",
  Speed = "Speed",
  Defense = "Defense",
  Energy = "Energy"
}

export enum Operation {
  FLAT_ADD = "FLAT_ADD",
  FLAT_SUB = "FLAT_SUB",
  PCT_ADD = "PCT_ADD",
  PCT_SUB = "PCT_SUB",
  MULTIPLY = "MULTIPLY"
}

export enum Target {
  SELF = "SELF",
  ALLY_SINGLE = "ALLY_SINGLE",
  ALLY_ALL = "ALLY_ALL",
  ENEMY_SINGLE = "ENEMY_SINGLE",
  ENEMY_ALL = "ENEMY_ALL",
  GLOBAL = "GLOBAL"
}

export enum Stacking {
  stack = "stack",
  replace = "replace",
  max = "max"
}

export enum AiHeuristic {
  aggressive = "aggressive",
  defensive = "defensive",
  balanced = "balanced"
}

export enum NarrativePosition {
  approach = "approach",
  settlement = "settlement",
  stronghold = "stronghold"
}

export enum EncounterType {
  combat = "combat",
  hazard = "hazard",
  event = "event"
}

export interface Modifier {
  stat: Stat;
  operation: Operation;
  value: number;
  duration: number;
  target: Target;
  stacking: Stacking;
  tags: string[];
}

export interface UpgradeEntry {
  added_effects: Modifier[];
  prerequisite: string | null;
  tier: number;
  exclusions: string[];
}

export type UpgradeTree = Record<string, UpgradeEntry>;

export interface Card {
  id: string;
  name: string;
  energy_cost: number;
  effects: Modifier[];
  tags: string[];
  deck_copies: number;
  upgrade_tier: number;
  upgrade_paths: UpgradeTree;
}

export interface Character {
  id: string;
  name: string;
  base_stats: Record<Stat, number>;
  innate_passive: Modifier;
  name_parts: Record<string, string>;
}

export interface Enemy {
  id: string;
  name: string;
  base_stats: Record<Stat, number>;
  card_pool: string[];
  ai_heuristic_tag: AiHeuristic;
  is_elite: boolean;
}

export interface CombatEntity {
  id: string;
  name: string;
  base_stats: Record<Stat, number>;
  active_modifiers: Modifier[];
  ct: number;
  is_player: boolean;
  card_pool: string[];
  ai_heuristic?: AiHeuristic | null;
  is_alive: boolean;
  current_energy: number;
  draw_pile: string[];
  hand: string[];
  discard_pile: string[];
}

export interface ResearchLayer {
  level: number;
  reveal_type: string;
  cost: number;
}

export interface CombatEncounter {
  type: "combat";
  narrative_position: NarrativePosition;
  name: string;
  description: string;
  enemies: string[];
  enemy_cards: string[];
}

export interface HazardEncounter {
  type: "hazard";
  narrative_position: NarrativePosition;
  name: string;
  description: string;
  hazard_modifiers: Modifier[];
  hazard_duration: number;
}

export interface EventChoice {
  description: string;
  effects: Modifier[];
  cost: Modifier[];
}

export interface EventEncounter {
  type: "event";
  narrative_position: NarrativePosition;
  name: string;
  description: string;
  choices: EventChoice[];
}

export type Encounter = CombatEncounter | HazardEncounter | EventEncounter;

export interface Region {
  id: string;
  name: string;
  region_type: string;
  modifier_stack: Modifier[];
  encounters: Encounter[];
  meta_reward: Modifier;
  research_layers: ResearchLayer[];
}

export interface WorldCard {
  id: string;
  name: string;
  upside: Modifier[];
  downside: Modifier[];
  description: string;
}

export interface OutpostUpgrade {
  id: string;
  name: string;
  description: string;
  effects: Modifier[];
  cost: number;
  special_effect: string;
}

export interface CharacterGenerationBounds {
  per_stat_min: Record<Stat, number>;
  per_stat_max: Record<Stat, number>;
  total_budget_min: number;
  total_budget_max: number;
}

export interface FlavorData {
  given_names: string[];
  archetypes: string[];
  region_nouns: string[];
  region_adjectives: string[];
  element_stat_map: Record<string, { default: string[]; rare: string[] }>;
  epithet_conditions: Array<Record<string, unknown>>;
}

export interface RawGameData {
  base_cards: Card[];
  hazard_cards: Card[];
  upgrade_trees: Record<string, UpgradeTree>;
  characters: Character[];
  enemies: Enemy[];
  generation_bounds: CharacterGenerationBounds;
  regions: Region[];
  world_deck: WorldCard[];
  outpost_upgrades: OutpostUpgrade[];
  flavor: FlavorData;
}

export interface GameData {
  cards_by_id: Record<string, Card>;
  upgrade_trees: Record<string, UpgradeTree>;
  characters: Character[];
  enemies_by_id: Record<string, Enemy>;
  generation_bounds: CharacterGenerationBounds;
  regions: Region[];
  world_deck: WorldCard[];
  outpost_upgrades: OutpostUpgrade[];
  flavor: FlavorData;
}

export interface RegionState {
  region: Region;
  conquered: boolean;
  research_level: number;
  assigned_difficulty: number;
}

export interface CampaignState {
  seed: number;
  turn_number: number;
  resources: number;
  roster: Character[];
  region_states: RegionState[];
  skip_tokens: number;
  active_world_modifiers: Modifier[];
  active_outpost_upgrades: OutpostUpgrade[];
  card_upgrades_applied: Record<string, string[]>;
  drafted_characters: string[];
  game_over: boolean;
  victory: boolean;
  campaign_log: string[];
}
