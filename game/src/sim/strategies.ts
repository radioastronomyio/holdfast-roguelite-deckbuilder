import { getCurrentStat } from "./turnOrder";
import { AiHeuristic, Operation, STAT_SCALE, Stat, Target, type Card, type CampaignState, type Character, type CombatEntity, type EventChoice, type GameData, type Modifier, type RegionState, type UpgradeEntry, type WorldCard } from "./types";
import type { SeededRng } from "./rng";

export interface StrategyCampaignState extends CampaignState {
  rng: SeededRng;
}

export interface PlayerStrategy {
  selectRegion(state: StrategyCampaignState, gameData: GameData): RegionState;
  selectParty(state: StrategyCampaignState, gameData: GameData, region: RegionState): Character[];
  selectCard(caster: CombatEntity, availableCards: Card[], allies: CombatEntity[], enemies: CombatEntity[]): [Card, CombatEntity[]] | null;
  evaluateWorldCard(card: WorldCard, state: StrategyCampaignState, gameData: GameData): boolean;
  selectEventChoice(choices: EventChoice[], state: StrategyCampaignState): number;
  selectCardUpgrade(rosterCards: string[], upgradeTrees: Record<string, Record<string, UpgradeEntry>>, appliedUpgrades: Record<string, string[]>, state: StrategyCampaignState): [string, string] | null;
  selectResearch(state: StrategyCampaignState, gameData: GameData): RegionState | null;
  selectDraftedCharacter(candidates: Character[], state: StrategyCampaignState): Character;
}

export function damageScore(card: Card): number {
  return card.effects.filter((effect) => effect.stat === Stat.HP && effect.operation === Operation.FLAT_SUB).reduce((sum, effect) => sum + effect.value, 0);
}

function isHealingCard(card: Card): boolean {
  return card.effects.some((effect) => effect.stat === Stat.HP && effect.operation === Operation.FLAT_ADD);
}

function isAoe(card: Card): boolean {
  return card.effects.some((effect) => effect.target === Target.ENEMY_ALL);
}

function isBuff(card: Card): boolean {
  return card.effects.some((effect) => [Operation.FLAT_ADD, Operation.PCT_ADD].includes(effect.operation) && [Target.SELF, Target.ALLY_SINGLE, Target.ALLY_ALL].includes(effect.target));
}

function isDebuff(card: Card): boolean {
  return card.effects.some((effect) => [Operation.FLAT_SUB, Operation.PCT_SUB].includes(effect.operation) && [Target.ENEMY_SINGLE, Target.ENEMY_ALL].includes(effect.target) && effect.stat !== Stat.HP);
}

function netModifierImpact(mods: Modifier[]): number {
  return mods.reduce((total, mod) => {
    if (mod.operation === Operation.FLAT_ADD || mod.operation === Operation.PCT_ADD) return total + mod.value;
    if (mod.operation === Operation.FLAT_SUB || mod.operation === Operation.PCT_SUB) return total - mod.value;
    return total;
  }, 0);
}

function affordable(caster: CombatEntity, cards: Card[]): Card[] {
  return cards.filter((card) => card.energy_cost <= caster.current_energy);
}

function hpRatio(entity: CombatEntity): number {
  const currentHp = getCurrentStat(entity, Stat.HP);
  const maxHp = entity.base_stats[Stat.HP] ?? currentHp;
  return maxHp <= 0 ? 100 : Math.floor(currentHp * 100 / maxHp);
}

function targetForCard(card: Card, enemies: CombatEntity[]): CombatEntity[] {
  const living = enemies.filter((enemy) => enemy.is_alive);
  if (isAoe(card)) return living;
  return [living.reduce((low, current) => getCurrentStat(current, Stat.HP) < getCurrentStat(low, Stat.HP) ? current : low)];
}

function partySize(state: CampaignState): number {
  return Math.min(3 + (state.active_outpost_upgrades.some((upgrade) => upgrade.special_effect === "party_size+1") ? 1 : 0), state.roster.length);
}

export function pickGreedyUpgrade(
  rosterCards: string[],
  upgradeTrees: Record<string, Record<string, UpgradeEntry>>,
  appliedUpgrades: Record<string, string[]>,
  preferStat: Stat | null = null,
  rng?: Pick<SeededRng, "choice">
): [string, string] | null {
  const candidates: Array<[number, string, string]> = [];
  for (const cardId of rosterCards) {
    const already = appliedUpgrades[cardId] ?? [];
    for (const [branch, entry] of Object.entries(upgradeTrees[cardId] ?? {})) {
      if (already.includes(branch)) continue;
      if (entry.prerequisite && !already.includes(entry.prerequisite)) continue;
      if (entry.exclusions.some((exclusion) => already.includes(exclusion))) continue;
      const score = entry.tier + (preferStat && entry.added_effects.some((effect) => effect.stat === preferStat) ? 10 : 0);
      candidates.push([score, cardId, branch]);
    }
  }
  if (candidates.length === 0) return null;
  const maxScore = Math.max(...candidates.map(([score]) => score));
  const top = candidates.filter(([score]) => score === maxScore).map(([, cardId, branch]) => [cardId, branch] as [string, string]);
  return rng && top.length > 1 ? rng.choice(top) : top[0];
}

export class AggressiveAI implements PlayerStrategy {
  selectRegion(state: StrategyCampaignState): RegionState {
    return state.region_states.filter((region) => !region.conquered).reduce((best, current) => current.assigned_difficulty < best.assigned_difficulty ? current : best);
  }

  selectParty(state: StrategyCampaignState, _gameData: GameData, _region: RegionState): Character[] {
    let party = [...state.roster].sort((a, b) => b.base_stats[Stat.Power] - a.base_stats[Stat.Power]).slice(0, partySize(state));
    if (state.roster.length > partySize(state)) {
      const allHp = state.roster.map((character) => character.base_stats[Stat.HP]).sort((a, b) => a - b);
      const medianHp = allHp[Math.floor(allHp.length / 2)];
      if (party.every((character) => character.base_stats[Stat.HP] < medianHp)) {
        const tankiest = state.roster.reduce((best, current) => current.base_stats[Stat.HP] > best.base_stats[Stat.HP] ? current : best);
        if (!party.includes(tankiest)) party = [...party.slice(0, -1), tankiest];
      }
    }
    return party;
  }

  selectCard(caster: CombatEntity, availableCards: Card[], _allies: CombatEntity[], enemies: CombatEntity[]): [Card, CombatEntity[]] | null {
    const livingEnemies = enemies.filter((enemy) => enemy.is_alive);
    const cards = affordable(caster, availableCards);
    if (!livingEnemies.length || !cards.length) return null;
    if (hpRatio(caster) < 25) {
      const heals = cards.filter(isHealingCard);
      if (heals.length) return [heals.reduce((best, current) => damageScore(current) > damageScore(best) ? current : best), [caster]];
    }
    const bestDamage = Math.max(...cards.map(damageScore), 0);
    const score = (card: Card): number => {
      let dmg = damageScore(card);
      if (isDebuff(card) && dmg === 0 && cards.some((other) => other !== card && damageScore(other) > 0)) {
        const shred = card.effects.filter((effect) => effect.stat === Stat.Defense && [Operation.PCT_SUB, Operation.FLAT_SUB].includes(effect.operation)).reduce((sum, effect) => sum + effect.value, 0);
        if (shred > 0) return bestDamage + shred;
      }
      if (isAoe(card) && livingEnemies.length > 1) dmg *= livingEnemies.length;
      if (dmg === 0 && isBuff(card)) return Math.max(Math.floor(bestDamage * 40 / 100), 1);
      if (dmg === 0 && isHealingCard(card)) return 1;
      return dmg;
    };
    const best = cards.reduce((a, b) => score(b) > score(a) ? b : a);
    if (damageScore(best) > 0 && !isAoe(best)) {
      const sorted = [...livingEnemies].sort((a, b) => getCurrentStat(a, Stat.HP) - getCurrentStat(b, Stat.HP));
      const lowHp = Math.floor(getCurrentStat(sorted[0], Stat.HP) / STAT_SCALE);
      const cardDmg = Math.floor(damageScore(best) / STAT_SCALE);
      if (lowHp > 0 && cardDmg >= lowHp * 3 && sorted.length > 1) return [best, [sorted[1]]];
      return [best, [sorted[0]]];
    }
    return [best, targetForCard(best, enemies)];
  }

  evaluateWorldCard(card: WorldCard): boolean {
    const allyTargets = [Target.SELF, Target.ALLY_SINGLE, Target.ALLY_ALL];
    if (card.downside.some((mod) => mod.stat === Stat.HP && mod.operation === Operation.FLAT_SUB && mod.value >= 30 * STAT_SCALE && allyTargets.includes(mod.target))) return false;
    const upside = card.upside.filter((mod) => [Operation.FLAT_ADD, Operation.PCT_ADD].includes(mod.operation)).reduce((sum, mod) => sum + mod.value, 0);
    const downside = card.downside.filter((mod) => [Operation.FLAT_SUB, Operation.PCT_SUB].includes(mod.operation)).reduce((sum, mod) => sum + mod.value, 0);
    return upside >= downside;
  }

  selectEventChoice(choices: EventChoice[]): number {
    let bestIdx = 0;
    let bestScore = -999999;
    choices.forEach((choice, i) => {
      const score = choice.effects.filter((effect) => effect.stat === Stat.HP && effect.operation === Operation.FLAT_SUB).reduce((sum, effect) => sum + effect.value, 0)
        + choice.effects.filter((effect) => effect.stat === Stat.Power && [Operation.PCT_ADD, Operation.FLAT_ADD].includes(effect.operation)).reduce((sum, effect) => sum + effect.value, 0);
      if (score > bestScore) { bestScore = score; bestIdx = i; }
    });
    return bestIdx;
  }

  selectCardUpgrade(cards: string[], trees: Record<string, Record<string, UpgradeEntry>>, applied: Record<string, string[]>, state: StrategyCampaignState): [string, string] | null {
    return pickGreedyUpgrade(cards, trees, applied, Stat.Power, state.rng);
  }

  selectResearch(_state: StrategyCampaignState, _gameData: GameData): RegionState | null { return null; }
  selectDraftedCharacter(candidates: Character[], _state: StrategyCampaignState): Character { return candidates.reduce((best, current) => current.base_stats[Stat.Power] > best.base_stats[Stat.Power] ? current : best); }
}

export class DefensiveAI extends AggressiveAI {
  override selectRegion(state: StrategyCampaignState): RegionState {
    return state.region_states.filter((region) => !region.conquered).reduce((best, current) => {
      const b = [best.assigned_difficulty, -best.research_level];
      const c = [current.assigned_difficulty, -current.research_level];
      return c[0] < b[0] || (c[0] === b[0] && c[1] < b[1]) ? current : best;
    });
  }

  override selectParty(state: StrategyCampaignState): Character[] {
    return [...state.roster].sort((a, b) => (b.base_stats[Stat.HP] + b.base_stats[Stat.Defense] * 5) - (a.base_stats[Stat.HP] + a.base_stats[Stat.Defense] * 5)).slice(0, partySize(state));
  }

  override selectCard(caster: CombatEntity, availableCards: Card[], allies: CombatEntity[], enemies: CombatEntity[]): [Card, CombatEntity[]] | null {
    const livingEnemies = enemies.filter((enemy) => enemy.is_alive);
    const livingAllies = allies.filter((ally) => ally.is_alive);
    const cards = affordable(caster, availableCards);
    if (!livingEnemies.length || !cards.length) return null;
    if (hpRatio(caster) < 30) {
      const heals = cards.filter(isHealingCard);
      if (heals.length) return [heals.reduce((best, current) => damageScore(current) > damageScore(best) ? current : best), [livingAllies.reduce((a, b) => getCurrentStat(b, Stat.HP) < getCurrentStat(a, Stat.HP) ? b : a)]];
    }
    const damageCards = cards.filter((card) => damageScore(card) > 0);
    if (damageCards.length) {
      const best = damageCards.reduce((a, b) => damageScore(b) > damageScore(a) ? b : a);
      if (isAoe(best)) return [best, livingEnemies];
      return [best, [livingEnemies.reduce((a, b) => b.base_stats[Stat.Power] > a.base_stats[Stat.Power] ? b : a)]];
    }
    return [cards[0], [caster]];
  }

  override evaluateWorldCard(card: WorldCard): boolean {
    const allyTargets = [Target.SELF, Target.ALLY_SINGLE, Target.ALLY_ALL];
    if ([...card.upside, ...card.downside].some((mod) => mod.operation === Operation.FLAT_SUB && mod.value >= 50 * STAT_SCALE && allyTargets.includes(mod.target))) return false;
    return [...card.upside, ...card.downside].some((mod) => [Stat.HP, Stat.Defense].includes(mod.stat) && [Operation.FLAT_ADD, Operation.PCT_ADD].includes(mod.operation) && allyTargets.includes(mod.target));
  }

  override selectEventChoice(choices: EventChoice[]): number {
    let bestIdx = 0;
    let bestCost = 999999;
    choices.forEach((choice, i) => {
      const cost = choice.cost.reduce((sum, mod) => sum + Math.abs(mod.value), 0);
      if (cost < bestCost) { bestCost = cost; bestIdx = i; }
    });
    return bestIdx;
  }

  override selectCardUpgrade(cards: string[], trees: Record<string, Record<string, UpgradeEntry>>, applied: Record<string, string[]>, state: StrategyCampaignState): [string, string] | null {
    return pickGreedyUpgrade(cards, trees, applied, Stat.Defense, state.rng);
  }

  override selectResearch(state: StrategyCampaignState, _gameData: GameData): RegionState | null {
    return state.region_states.filter((region) => !region.conquered && region.research_level < 4 && state.resources >= region.region.research_layers[region.research_level].cost)
      .sort((a, b) => a.region.research_layers[a.research_level].cost - b.region.research_layers[b.research_level].cost)[0] ?? null;
  }

  override selectDraftedCharacter(candidates: Character[], _state: StrategyCampaignState): Character { return candidates.reduce((best, current) => current.base_stats[Stat.HP] > best.base_stats[Stat.HP] ? current : best); }
}

export class BalancedAI extends AggressiveAI {
  override selectRegion(state: StrategyCampaignState): RegionState {
    const unconquered = state.region_states.filter((region) => !region.conquered);
    const researched = unconquered.filter((region) => region.research_level >= 2);
    return (researched.length ? researched : unconquered).reduce((best, current) => current.assigned_difficulty < best.assigned_difficulty ? current : best);
  }

  override selectParty(state: StrategyCampaignState, _gameData: GameData, region: RegionState): Character[] {
    const score = (character: Character) => {
      let total = Object.values(character.base_stats).reduce((sum, value) => sum + value, 0);
      for (const mod of region.region.modifier_stack) if ([Operation.FLAT_SUB, Operation.PCT_SUB].includes(mod.operation)) total += character.base_stats[Stat.Defense];
      return total;
    };
    return [...state.roster].sort((a, b) => score(b) - score(a)).slice(0, partySize(state));
  }

  override selectCard(caster: CombatEntity, availableCards: Card[], allies: CombatEntity[], enemies: CombatEntity[]): [Card, CombatEntity[]] | null {
    const livingEnemies = enemies.filter((enemy) => enemy.is_alive);
    const livingAllies = allies.filter((ally) => ally.is_alive);
    const cards = affordable(caster, availableCards);
    if (!livingEnemies.length || !cards.length) return null;
    const score = (card: Card) => {
      const dmg = damageScore(card);
      const dpe = dmg > 0 ? Math.floor(dmg / Math.max(1, card.energy_cost)) : 0;
      if (livingAllies.some((ally) => hpRatio(ally) < 40) && isHealingCard(card)) return 999999;
      if (livingEnemies.length > 2 && isAoe(card)) return dmg * 2 + dpe;
      if (livingEnemies.length === 1 && !isAoe(card)) return dmg * 2 + dpe;
      return dmg + dpe;
    };
    const best = cards.reduce((a, b) => score(b) > score(a) ? b : a);
    if (isHealingCard(best)) return [best, [livingAllies.reduce((a, b) => getCurrentStat(b, Stat.HP) < getCurrentStat(a, Stat.HP) ? b : a)]];
    return [best, targetForCard(best, enemies)];
  }

  override evaluateWorldCard(card: WorldCard): boolean {
    const upside = netModifierImpact(card.upside);
    const net = upside + netModifierImpact(card.downside);
    return net > (upside > 0 ? Math.floor(Math.abs(upside) * 20 / 100) : 0);
  }

  override selectEventChoice(choices: EventChoice[]): number {
    let bestIdx = 0;
    let bestScore = -999999;
    choices.forEach((choice, i) => {
      const score = netModifierImpact(choice.effects) + netModifierImpact(choice.cost);
      if (score > bestScore) { bestScore = score; bestIdx = i; }
    });
    return bestIdx;
  }

  override selectCardUpgrade(cards: string[], trees: Record<string, Record<string, UpgradeEntry>>, applied: Record<string, string[]>, state: StrategyCampaignState): [string, string] | null {
    return pickGreedyUpgrade(cards, trees, applied, state.turn_number % 2 === 0 ? Stat.Power : Stat.Defense, state.rng);
  }

  override selectResearch(state: StrategyCampaignState, _gameData: GameData): RegionState | null {
    return state.region_states.filter((region) => !region.conquered && region.research_level < 2 && state.resources >= region.region.research_layers[region.research_level].cost)
      .sort((a, b) => a.region.research_layers[a.research_level].cost - b.region.research_layers[b.research_level].cost)[0] ?? null;
  }

  override selectDraftedCharacter(candidates: Character[], state: StrategyCampaignState): Character {
    const totals = Object.fromEntries(Object.values(Stat).map((stat) => [stat, state.roster.reduce((sum, character) => sum + character.base_stats[stat], 0)])) as Record<Stat, number>;
    const weakest = Object.values(Stat).reduce((a, b) => totals[b] < totals[a] ? b : a);
    return candidates.reduce((best, current) => current.base_stats[weakest] > best.base_stats[weakest] ? current : best);
  }
}

export function createStrategy(heuristic: AiHeuristic): PlayerStrategy {
  if (heuristic === AiHeuristic.defensive) return new DefensiveAI();
  if (heuristic === AiHeuristic.balanced) return new BalancedAI();
  return new AggressiveAI();
}
