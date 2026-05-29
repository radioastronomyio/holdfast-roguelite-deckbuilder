import { resolveCombat, resolveEvent, resolveHazard, type CombatResult, type EventResult, type HazardResult } from "./encounters";
import { generateCharacter, generateRegion } from "./generation";
import { SeededRng } from "./rng";
import { createStrategy, type PlayerStrategy, type StrategyCampaignState } from "./strategies";
import { createCombatEntity } from "./turnOrder";
import { AiHeuristic, Operation, STAT_SCALE, type CampaignState, type Card, type Character, type CombatEntity, type Enemy, type GameData, type Modifier, type RegionState, type UpgradeEntry } from "./types";

export interface CampaignResult {
  seed: number;
  victory: boolean;
  regions_cleared: number;
  total_turns: number;
  final_roster: Character[];
  world_cards_drawn: number;
  world_cards_skipped: number;
  resources_spent_on_research: number;
  campaign_log: string[];
  encounter_results: Array<CombatResult | HazardResult | EventResult>;
  world_cards_accepted_ids: string[];
  world_cards_skipped_ids: string[];
  upgrade_branches_chosen: Record<string, string>;
  region_order: string[];
  region_difficulties: Record<string, number>;
  starting_roster_ids: string[];
  drafted_character_ids: string[];
  card_pool_ids: string[];
}

export function createCampaignState(seed: number): CampaignState {
  return {
    seed,
    turn_number: 0,
    resources: 0,
    roster: [],
    region_states: [],
    skip_tokens: 0,
    active_world_modifiers: [],
    active_outpost_upgrades: [],
    card_upgrades_applied: {},
    drafted_characters: [],
    game_over: false,
    victory: false,
    campaign_log: []
  };
}

function createStrategyState(seed: number, rng: SeededRng): StrategyCampaignState {
  return { ...createCampaignState(seed), rng };
}

export function partySize(state: CampaignState): number {
  const bonus = state.active_outpost_upgrades.some((upgrade) => upgrade.special_effect === "party_size+1") ? 1 : 0;
  return Math.min(3 + bonus, state.roster.length);
}

export function conqueredCount(state: CampaignState): number {
  return state.region_states.filter((region) => region.conquered).length;
}

export function unconqueredRegions(state: CampaignState): RegionState[] {
  return state.region_states.filter((region) => !region.conquered);
}

export function characterToCombatEntity(character: Character, activeWorldMods: Modifier[], activeOutpostMods: Modifier[]): CombatEntity {
  return createCombatEntity({
    id: character.id,
    name: character.name,
    base_stats: { ...character.base_stats },
    active_modifiers: [character.innate_passive, ...activeWorldMods, ...activeOutpostMods],
    is_player: true,
    card_pool: []
  });
}

export function enemyDataToCombatEntity(enemy: Enemy): CombatEntity {
  return createCombatEntity({
    id: enemy.id,
    name: enemy.name,
    base_stats: { ...enemy.base_stats },
    is_player: false,
    card_pool: [...enemy.card_pool],
    ai_heuristic: enemy.ai_heuristic_tag
  });
}

export function applyCardUpgrade(card: Card, branchKey: string, upgradeTrees: Record<string, Record<string, UpgradeEntry>>): Card {
  const entry = upgradeTrees[card.id]?.[branchKey];
  if (!entry) return card;
  return {
    ...card,
    effects: [...card.effects, ...entry.added_effects],
    upgrade_tier: card.upgrade_tier + 1
  };
}

function fallbackEnemy(enemyId: string, cardIds: string[]): Enemy {
  return {
    id: enemyId,
    name: enemyId.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()),
    base_stats: { HP: 50 * STAT_SCALE, Power: 50 * STAT_SCALE, Speed: 50 * STAT_SCALE, Defense: 50 * STAT_SCALE, Energy: 50 * STAT_SCALE },
    card_pool: cardIds.slice(0, 2),
    ai_heuristic_tag: AiHeuristic.balanced,
    is_elite: false
  };
}

export function runCampaign(seed: number, gameData: GameData, strategyInput: AiHeuristic | "aggressive" | "defensive" | "balanced" | PlayerStrategy = AiHeuristic.aggressive): CampaignResult {
  const rng = new SeededRng(seed);
  const state = createStrategyState(seed, rng);
  const strategy = typeof strategyInput === "string" ? createStrategy(strategyInput as AiHeuristic) : strategyInput;
  const encounterResults: Array<CombatResult | HazardResult | EventResult> = [];
  const localCards = { ...gameData.cards_by_id };
  const allCardIds = Object.entries(localCards).filter(([, card]) => !card.tags.includes("hazard")).map(([id]) => id);
  const enemyRegistry = new Map<string, Enemy>();
  const regionDifficulties: Record<string, number> = {};
  const regionOrder: string[] = [];
  const upgradeBranchesChosen: Record<string, string> = {};
  const worldCardsAcceptedIds: string[] = [];
  const worldCardsSkippedIds: string[] = [];
  const draftedCharacterIds: string[] = [];
  let totalTurns = 0;
  let worldCardsDrawn = 0;
  let worldCardsSkipped = 0;
  let resourcesSpent = 0;

  for (let difficulty = 1; difficulty <= 6; difficulty += 1) {
    const region = generateRegion(rng, difficulty, allCardIds, gameData.flavor, { regionAdjectives: gameData.flavor.region_adjectives, enemyRegistry, cardsById: localCards });
    state.region_states.push({ region, conquered: false, research_level: 0, assigned_difficulty: difficulty });
    regionDifficulties[region.id] = difficulty;
  }

  const candidates = Array.from({ length: 5 }, () => generateCharacter(rng, gameData.generation_bounds, gameData.flavor))
    .sort((a, b) => Object.values(b.base_stats).reduce((sum, value) => sum + value, 0) - Object.values(a.base_stats).reduce((sum, value) => sum + value, 0));
  for (const starter of candidates.slice(0, 2)) {
    state.roster.push(starter);
    state.campaign_log.push(`Starting character: ${starter.name}`);
  }
  const startingRosterIds = state.roster.map((character) => character.id);

  const unrevealed = state.region_states.filter((region) => region.research_level === 0);
  if (unrevealed.length > 0) {
    const reveal = rng.choice(unrevealed);
    reveal.research_level = 1;
    state.campaign_log.push(`Free intel: ${reveal.region.name} revealed to level 1`);
  }

  const remainingWorldDeck = [...gameData.world_deck];
  while (!state.game_over && !state.victory) {
    while (true) {
      const researchTarget = strategy.selectResearch(state, gameData);
      if (!researchTarget || researchTarget.research_level >= 4) break;
      const layer = researchTarget.region.research_layers[researchTarget.research_level];
      if (state.resources < layer.cost) break;
      state.resources -= layer.cost;
      resourcesSpent += layer.cost;
      researchTarget.research_level += 1;
      state.campaign_log.push(`Researched ${researchTarget.region.name} to level ${researchTarget.research_level} (cost ${layer.cost})`);
    }

    if (unconqueredRegions(state).length === 0) {
      state.victory = true;
      state.campaign_log.push("Victory! All 6 regions conquered.");
      break;
    }
    const target = strategy.selectRegion(state, gameData);
    state.campaign_log.push(`Assaulting ${target.region.name} (difficulty ${target.assigned_difficulty})`);
    regionOrder.push(target.region.id);

    const partyChars = strategy.selectParty(state, gameData, target);
    let party = partyChars.map((character) => characterToCombatEntity(character, state.active_world_modifiers, state.active_outpost_upgrades.flatMap((upgrade) => upgrade.effects)));
    for (const entity of party) entity.card_pool = allCardIds;
    let wiped = false;

    for (const encounter of target.region.encounters) {
      if (encounter.type === "combat") {
        const enemies = encounter.enemies.map((enemyId) => enemyDataToCombatEntity(enemyRegistry.get(enemyId) ?? gameData.enemies_by_id[enemyId] ?? fallbackEnemy(enemyId, encounter.enemy_cards)));
        const result = resolveCombat(party, enemies, localCards, { region_modifiers: target.region.modifier_stack, player_strategy: strategy, strategy_state: state, rng });
        encounterResults.push(result);
        totalTurns += result.turns_taken;
        if (!result.player_won) {
          state.game_over = true;
          wiped = true;
          state.campaign_log.push(`Party wiped in combat at ${encounter.name}!`);
          break;
        }
        party = result.final_state.filter((entity) => entity.is_player && entity.is_alive);
        if (party.length === 0) {
          state.game_over = true;
          wiped = true;
        }
      } else if (encounter.type === "hazard") {
        const result = resolveHazard(party, encounter.hazard_modifiers, encounter.hazard_duration, target.region.modifier_stack);
        encounterResults.push(result);
        if (!result.survived) {
          state.game_over = true;
          wiped = true;
          state.campaign_log.push(`Party wiped in hazard at ${encounter.name}!`);
          break;
        }
        party = result.final_state.filter((entity) => entity.is_alive);
        if (party.length === 0) {
          state.game_over = true;
          wiped = true;
        }
      } else {
        const result = resolveEvent(party, encounter.choices, strategy.selectEventChoice(encounter.choices, state));
        encounterResults.push(result);
        party = result.final_state.filter((entity) => entity.is_alive);
        if (party.length === 0) {
          state.game_over = true;
          wiped = true;
        }
      }
    }

    if (wiped) {
      state.campaign_log.push("Campaign lost.");
      break;
    }
    target.conquered = true;
    state.turn_number += 1;
    state.campaign_log.push(`Conquered ${target.region.name}!`);
    state.resources += 50;
    state.skip_tokens += 1;

    for (const character of partyChars) {
      const meta = target.region.meta_reward;
      if (meta.operation === Operation.FLAT_ADD) character.base_stats[meta.stat] += meta.value;
      else if (meta.operation === Operation.FLAT_SUB) character.base_stats[meta.stat] = Math.max(0, character.base_stats[meta.stat] - meta.value);
      else if (meta.operation === Operation.PCT_ADD) character.base_stats[meta.stat] = Math.floor(character.base_stats[meta.stat] * (100 + meta.value) / 100);
      else if (meta.operation === Operation.PCT_SUB) character.base_stats[meta.stat] = Math.floor(character.base_stats[meta.stat] * Math.max(0, 100 - meta.value) / 100);
    }

    for (let i = 0; i < partySize(state); i += 1) {
      const upgrade = strategy.selectCardUpgrade(allCardIds, gameData.upgrade_trees, state.card_upgrades_applied, state);
      if (!upgrade) continue;
      const [cardId, branch] = upgrade;
      state.card_upgrades_applied[cardId] = [...(state.card_upgrades_applied[cardId] ?? []), branch];
      localCards[cardId] = applyCardUpgrade(localCards[cardId], branch, gameData.upgrade_trees);
      state.campaign_log.push(`Applied upgrade ${branch} to ${cardId}`);
      upgradeBranchesChosen[cardId] = branch;
    }

    const draftCandidates = Array.from({ length: 3 }, () => generateCharacter(rng, gameData.generation_bounds, gameData.flavor));
    const drafted = strategy.selectDraftedCharacter(draftCandidates, state);
    state.roster.push(drafted);
    state.drafted_characters.push(drafted.id);
    state.campaign_log.push(`Drafted: ${drafted.name}`);
    draftedCharacterIds.push(drafted.id);

    rng.shuffle(remainingWorldDeck);
    const drawn = remainingWorldDeck.splice(0, Math.min(3, remainingWorldDeck.length));
    for (const card of drawn) {
      worldCardsDrawn += 1;
      const accept = strategy.evaluateWorldCard(card, state, gameData);
      if (accept) {
        state.active_world_modifiers.push(...card.upside, ...card.downside);
        state.campaign_log.push(`Accepted world card: ${card.name}`);
        worldCardsAcceptedIds.push(card.id);
      } else {
        if (state.skip_tokens > 0) {
          state.skip_tokens -= 1;
          worldCardsSkipped += 1;
          state.campaign_log.push(`Skipped world card: ${card.name}`);
          worldCardsSkippedIds.push(card.id);
        } else {
          state.active_world_modifiers.push(...card.upside, ...card.downside);
          state.campaign_log.push(`Forced to accept world card: ${card.name}`);
          worldCardsAcceptedIds.push(card.id);
        }
      }
    }
  }

  return {
    seed,
    victory: state.victory,
    regions_cleared: conqueredCount(state),
    total_turns: totalTurns,
    final_roster: state.roster,
    world_cards_drawn: worldCardsDrawn,
    world_cards_skipped: worldCardsSkipped,
    resources_spent_on_research: resourcesSpent,
    campaign_log: state.campaign_log,
    encounter_results: encounterResults,
    world_cards_accepted_ids: worldCardsAcceptedIds,
    world_cards_skipped_ids: worldCardsSkippedIds,
    upgrade_branches_chosen: upgradeBranchesChosen,
    region_order: regionOrder,
    region_difficulties: regionDifficulties,
    starting_roster_ids: startingRosterIds,
    drafted_character_ids: draftedCharacterIds,
    card_pool_ids: allCardIds
  };
}
