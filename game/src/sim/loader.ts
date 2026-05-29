import { Operation, STAT_SCALE, type Card, type GameData, type Modifier, type RawGameData, type UpgradeEntry, type UpgradeTree } from "./types";

export function scaleModifier(modifier: Modifier): Modifier {
  if (modifier.operation === Operation.FLAT_ADD || modifier.operation === Operation.FLAT_SUB) {
    return { ...modifier, value: modifier.value * STAT_SCALE };
  }
  return { ...modifier };
}

function normalizeModifier(modifier: Modifier): Modifier {
  return {
    ...modifier,
    stacking: modifier.stacking,
    tags: modifier.tags ?? []
  };
}

function scaleUpgradeEntry(entry: UpgradeEntry): UpgradeEntry {
  return {
    ...entry,
    prerequisite: entry.prerequisite ?? null,
    exclusions: entry.exclusions ?? [],
    added_effects: (entry.added_effects ?? []).map((effect) => scaleModifier(normalizeModifier(effect)))
  };
}

function scaleCard(card: Card): Card {
  const upgradePaths: UpgradeTree = {};
  for (const [key, entry] of Object.entries(card.upgrade_paths ?? {})) {
    upgradePaths[key] = scaleUpgradeEntry(entry);
  }
  return {
    ...card,
    tags: card.tags ?? [],
    deck_copies: card.deck_copies ?? 1,
    upgrade_tier: card.upgrade_tier ?? 0,
    effects: (card.effects ?? []).map((effect) => scaleModifier(normalizeModifier(effect))),
    upgrade_paths: upgradePaths
  };
}

export function loadGameDataFromRaw(raw: RawGameData): GameData {
  const cardsById: Record<string, Card> = {};
  const upgradeTrees: Record<string, UpgradeTree> = {};

  for (const rawCard of [...raw.base_cards, ...raw.hazard_cards]) {
    const card = scaleCard(rawCard);
    cardsById[card.id] = card;
    if (Object.keys(card.upgrade_paths).length > 0) {
      upgradeTrees[card.id] = card.upgrade_paths;
    }
  }

  for (const [cardId, tree] of Object.entries(raw.upgrade_trees ?? {})) {
    const scaledTree: UpgradeTree = {};
    for (const [branch, entry] of Object.entries(tree)) {
      scaledTree[branch] = scaleUpgradeEntry(entry);
    }
    upgradeTrees[cardId] = scaledTree;
  }

  return {
    cards_by_id: cardsById,
    upgrade_trees: upgradeTrees,
    characters: raw.characters,
    enemies_by_id: Object.fromEntries(raw.enemies.map((enemy) => [enemy.id, enemy])),
    generation_bounds: raw.generation_bounds,
    regions: raw.regions,
    world_deck: raw.world_deck,
    outpost_upgrades: raw.outpost_upgrades,
    flavor: raw.flavor
  };
}
