import { applyCardUpgrade, characterToCombatEntity, createCampaignState, enemyDataToCombatEntity, partySize } from "./campaign";
import { generateCharacter, generateRegion } from "./generation";
import { SeededRng, type RngState } from "./rng";
import { CombatStepper, type CombatStepperState } from "./combatStepper";
import { AiHeuristic, Operation, type CampaignState, type Character, type CombatEntity, type Enemy, type GameData, type RegionState } from "./types";

export enum CampaignStepperPhase {
  REGION_SELECT = "REGION_SELECT",
  PARTY_SELECT = "PARTY_SELECT",
  ENCOUNTER_ACTIVE = "ENCOUNTER_ACTIVE",
  ENCOUNTER_TRANSITION = "ENCOUNTER_TRANSITION",
  POST_CONQUEST_UPGRADES = "POST_CONQUEST_UPGRADES",
  POST_CONQUEST_DRAFT = "POST_CONQUEST_DRAFT",
  WORLD_PHASE = "WORLD_PHASE",
  RESEARCH_PHASE = "RESEARCH_PHASE",
  VICTORY = "VICTORY",
  DEFEAT = "DEFEAT"
}

export interface EncounterCompletion {
  playerWon: boolean;
  survivors: string[];
}

export interface CampaignStepperState {
  seed: number;
  phase: CampaignStepperPhase;
  state: CampaignState;
  rng: RngState;
  selectedRegionIndex: number | null;
  selectedPartyIds: string[];
  encounterIndex: number;
  enemyRegistry: Enemy[];
  localCards: string[];
  combat: CombatStepperState | null;
  draftCandidates: Character[];
  worldCandidates: string[];
}

function cloneCampaignState(state: CampaignState): CampaignState {
  return JSON.parse(JSON.stringify(state)) as CampaignState;
}

function rngState(rng: SeededRng): RngState {
  const state = rng.getState();
  return { ...state, mt: state.mt.map((value) => value >>> 0) };
}

function fallbackEnemy(enemyId: string, cardIds: string[]): Enemy {
  return {
    id: enemyId,
    name: enemyId.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()),
    base_stats: { HP: 50_000, Power: 50_000, Speed: 50_000, Defense: 50_000, Energy: 50_000 },
    card_pool: cardIds.slice(0, 2),
    ai_heuristic_tag: AiHeuristic.balanced,
    is_elite: false
  };
}

export class CampaignStepper {
  readonly seed: number;
  readonly gameData: GameData;
  phase: CampaignStepperPhase;
  state: CampaignState;
  selectedRegionIndex: number | null;
  selectedPartyIds: string[];
  private readonly rng: SeededRng;
  private readonly enemyRegistry: Map<string, Enemy>;
  private localCards;
  private encounterIndex;
  private combat: CombatStepper | null;
  private draftCandidates: Character[];
  private worldCandidates: string[];

  constructor(seed: number, gameData: GameData) {
    this.seed = seed;
    this.gameData = gameData;
    this.phase = CampaignStepperPhase.REGION_SELECT;
    this.state = createCampaignState(seed);
    this.selectedRegionIndex = null;
    this.selectedPartyIds = [];
    this.rng = new SeededRng(seed);
    this.enemyRegistry = new Map<string, Enemy>();
    this.localCards = { ...gameData.cards_by_id };
    this.encounterIndex = 0;
    this.combat = null;
    this.draftCandidates = [];
    this.worldCandidates = [];
    this.initializeCampaign();
  }

  selectRegion(regionIndex: number): CampaignState {
    const region = this.state.region_states[regionIndex];
    if (!region || region.conquered) throw new Error(`Invalid region index ${regionIndex}`);
    this.selectedRegionIndex = regionIndex;
    this.encounterIndex = 0;
    this.phase = CampaignStepperPhase.PARTY_SELECT;
    this.state.campaign_log.push(`Assaulting ${region.region.name} (difficulty ${region.assigned_difficulty})`);
    return this.state;
  }

  selectParty(characterIds: string[]): void {
    if (this.selectedRegionIndex === null) throw new Error("Select a region before selecting a party.");
    const allowed = partySize(this.state);
    this.selectedPartyIds = characterIds.slice(0, allowed);
    if (this.selectedPartyIds.length === 0) throw new Error("Party must contain at least one character.");
    this.phase = CampaignStepperPhase.ENCOUNTER_ACTIVE;
    this.prepareEncounter();
  }

  getCombatStepper(): CombatStepper | null {
    return this.combat;
  }

  completeEncounter(result: EncounterCompletion): CampaignStepperPhase {
    if (!result.playerWon) {
      this.state.game_over = true;
      this.phase = CampaignStepperPhase.DEFEAT;
      this.state.campaign_log.push("Campaign lost.");
      return this.phase;
    }
    this.combat = null;
    this.encounterIndex += 1;
    const region = this.selectedRegion();
    if (this.encounterIndex < region.region.encounters.length) {
      this.phase = CampaignStepperPhase.ENCOUNTER_TRANSITION;
      this.prepareEncounter();
      return this.phase;
    }
    this.finishRegion(region);
    return this.phase;
  }

  selectUpgrade(cardId: string, branchKey: string): void {
    const card = this.localCards[cardId];
    if (!card) throw new Error(`Unknown card ${cardId}`);
    this.state.card_upgrades_applied[cardId] = [...(this.state.card_upgrades_applied[cardId] ?? []), branchKey];
    this.localCards[cardId] = applyCardUpgrade(card, branchKey, this.gameData.upgrade_trees);
    this.state.campaign_log.push(`Applied upgrade ${branchKey} to ${cardId}`);
    this.phase = CampaignStepperPhase.POST_CONQUEST_DRAFT;
  }

  selectDraftCharacter(characterIndex: number): void {
    const drafted = this.draftCandidates[characterIndex];
    if (drafted) {
      this.state.roster.push(drafted);
      this.state.drafted_characters.push(drafted.id);
      this.state.campaign_log.push(`Drafted: ${drafted.name}`);
    }
    this.phase = CampaignStepperPhase.WORLD_PHASE;
    this.worldCandidates = this.rng.sample(this.gameData.world_deck, Math.min(3, this.gameData.world_deck.length)).map((card) => card.id);
  }

  evaluateWorldCard(accept: boolean): void {
    const cardId = this.worldCandidates.shift();
    const card = this.gameData.world_deck.find((item) => item.id === cardId);
    if (!card) {
      this.phase = CampaignStepperPhase.REGION_SELECT;
      return;
    }
    if (accept || this.state.skip_tokens <= 0) {
      this.state.active_world_modifiers.push(...card.upside, ...card.downside);
      this.state.campaign_log.push(`Accepted world card: ${card.name}`);
    } else {
      this.state.skip_tokens -= 1;
      this.state.campaign_log.push(`Skipped world card: ${card.name}`);
    }
    if (this.worldCandidates.length === 0) this.phase = CampaignStepperPhase.REGION_SELECT;
  }

  selectResearch(regionIndex: number): void {
    const region = this.state.region_states[regionIndex];
    if (!region || region.research_level >= region.region.research_layers.length) return;
    const layer = region.region.research_layers[region.research_level];
    if (this.state.resources < layer.cost) return;
    this.state.resources -= layer.cost;
    region.research_level += 1;
    this.state.campaign_log.push(`Researched ${region.region.name} to level ${region.research_level}`);
  }

  endResearch(): void {
    this.phase = CampaignStepperPhase.REGION_SELECT;
  }

  toJSON(): CampaignStepperState {
    return {
      seed: this.seed,
      phase: this.phase,
      state: cloneCampaignState(this.state),
      rng: rngState(this.rng),
      selectedRegionIndex: this.selectedRegionIndex,
      selectedPartyIds: [...this.selectedPartyIds],
      encounterIndex: this.encounterIndex,
      enemyRegistry: [...this.enemyRegistry.values()],
      localCards: Object.keys(this.localCards),
      combat: this.combat?.toJSON() ?? null,
      draftCandidates: JSON.parse(JSON.stringify(this.draftCandidates)) as Character[],
      worldCandidates: [...this.worldCandidates]
    };
  }

  static fromJSON(serialized: CampaignStepperState, gameData: GameData): CampaignStepper {
    const stepper = new CampaignStepper(serialized.seed, gameData);
    stepper.phase = serialized.phase;
    stepper.state = cloneCampaignState(serialized.state);
    stepper.rng.setState(serialized.rng);
    stepper.selectedRegionIndex = serialized.selectedRegionIndex;
    stepper.selectedPartyIds = [...serialized.selectedPartyIds];
    stepper.encounterIndex = serialized.encounterIndex;
    stepper.enemyRegistry.clear();
    for (const enemy of serialized.enemyRegistry) stepper.enemyRegistry.set(enemy.id, enemy);
    stepper.localCards = { ...gameData.cards_by_id };
    stepper.combat = serialized.combat ? CombatStepper.fromJSON(serialized.combat, stepper.localCards) : null;
    stepper.draftCandidates = JSON.parse(JSON.stringify(serialized.draftCandidates)) as Character[];
    stepper.worldCandidates = [...serialized.worldCandidates];
    return stepper;
  }

  private initializeCampaign(): void {
    const allCardIds = this.cardPoolIds();
    for (let difficulty = 1; difficulty <= 6; difficulty += 1) {
      const region = generateRegion(this.rng, difficulty, allCardIds, this.gameData.flavor, {
        regionAdjectives: this.gameData.flavor.region_adjectives,
        enemyRegistry: this.enemyRegistry,
        cardsById: this.localCards
      });
      this.state.region_states.push({ region, conquered: false, research_level: 0, assigned_difficulty: difficulty });
    }

    const candidates = Array.from({ length: 5 }, () => generateCharacter(this.rng, this.gameData.generation_bounds, this.gameData.flavor))
      .sort((a, b) => Object.values(b.base_stats).reduce((sum, value) => sum + value, 0) - Object.values(a.base_stats).reduce((sum, value) => sum + value, 0));
    this.state.roster.push(...candidates.slice(0, 2));
    const unrevealed = this.state.region_states.filter((region) => region.research_level === 0);
    if (unrevealed.length > 0) this.rng.choice(unrevealed).research_level = 1;
  }

  private selectedRegion(): RegionState {
    if (this.selectedRegionIndex === null) throw new Error("No selected region.");
    const region = this.state.region_states[this.selectedRegionIndex];
    if (!region) throw new Error("Selected region no longer exists.");
    return region;
  }

  private selectedParty(): CombatEntity[] {
    const ids = new Set(this.selectedPartyIds);
    const party = this.state.roster
      .filter((character) => ids.has(character.id))
      .map((character) => characterToCombatEntity(character, this.state.active_world_modifiers, this.state.active_outpost_upgrades.flatMap((upgrade) => upgrade.effects)));
    for (const entity of party) entity.card_pool = this.cardPoolIds();
    return party;
  }

  private prepareEncounter(): void {
    const region = this.selectedRegion();
    const encounter = region.region.encounters[this.encounterIndex];
    if (!encounter) {
      this.finishRegion(region);
      return;
    }
    if (encounter.type !== "combat") {
      this.phase = CampaignStepperPhase.ENCOUNTER_ACTIVE;
      return;
    }
    const enemies = encounter.enemies.map((enemyId) => enemyDataToCombatEntity(this.enemyRegistry.get(enemyId) ?? this.gameData.enemies_by_id[enemyId] ?? fallbackEnemy(enemyId, encounter.enemy_cards)));
    this.combat = new CombatStepper(this.selectedParty(), enemies, this.localCards, { seed: this.seed + this.encounterIndex, region_modifiers: region.region.modifier_stack });
    this.phase = CampaignStepperPhase.ENCOUNTER_ACTIVE;
  }

  private finishRegion(region: RegionState): void {
    region.conquered = true;
    this.state.turn_number += 1;
    this.state.resources += 50;
    this.state.skip_tokens += 1;
    this.state.campaign_log.push(`Conquered ${region.region.name}!`);
    this.applyMetaReward(region);
    if (this.state.region_states.every((item) => item.conquered)) {
      this.state.victory = true;
      this.phase = CampaignStepperPhase.VICTORY;
      return;
    }
    this.draftCandidates = Array.from({ length: 3 }, () => generateCharacter(this.rng, this.gameData.generation_bounds, this.gameData.flavor));
    this.phase = CampaignStepperPhase.POST_CONQUEST_UPGRADES;
  }

  private applyMetaReward(region: RegionState): void {
    const selected = new Set(this.selectedPartyIds);
    for (const character of this.state.roster.filter((item) => selected.has(item.id))) {
      const meta = region.region.meta_reward;
      if (meta.operation === Operation.FLAT_ADD) character.base_stats[meta.stat] += meta.value;
      else if (meta.operation === Operation.FLAT_SUB) character.base_stats[meta.stat] = Math.max(0, character.base_stats[meta.stat] - meta.value);
      else if (meta.operation === Operation.PCT_ADD) character.base_stats[meta.stat] = Math.floor(character.base_stats[meta.stat] * (100 + meta.value) / 100);
      else if (meta.operation === Operation.PCT_SUB) character.base_stats[meta.stat] = Math.floor(character.base_stats[meta.stat] * Math.max(0, 100 - meta.value) / 100);
    }
  }

  private cardPoolIds(): string[] {
    return Object.entries(this.localCards).filter(([, card]) => !card.tags.includes("hazard")).map(([id]) => id);
  }
}
