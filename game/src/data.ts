/**
 * Browser data loader — fetches the shared JSON definitions served under
 * `public/data/` and builds a `GameData` via the frozen sim loader.
 *
 * @module data
 */

import { loadGameDataFromRaw } from "./sim/loader";
import type { GameData, RawGameData } from "./sim/types";

const BASE = import.meta.env.BASE_URL;

async function fetchJson<T>(relativePath: string): Promise<T> {
  const response = await fetch(`${BASE}${relativePath}`);
  if (!response.ok) throw new Error(`Failed to load ${relativePath}: ${response.status}`);
  return (await response.json()) as T;
}

export async function loadGameData(): Promise<GameData> {
  const raw: RawGameData = {
    base_cards: await fetchJson("data/cards/base-cards.json"),
    hazard_cards: await fetchJson("data/cards/hazard-cards.json"),
    upgrade_trees: await fetchJson("data/cards/upgrade-trees.json"),
    characters: await fetchJson("data/entities/example-characters.json"),
    enemies: await fetchJson("data/entities/example-enemies.json"),
    generation_bounds: await fetchJson("data/entities/generation-bounds.json"),
    regions: await fetchJson("data/campaign/example-regions.json"),
    world_deck: await fetchJson("data/campaign/world-deck.json"),
    outpost_upgrades: await fetchJson("data/campaign/outpost-upgrades.json"),
    flavor: {
      given_names: await fetchJson("data/flavor/given_names.json"),
      archetypes: await fetchJson("data/flavor/archetypes.json"),
      region_nouns: await fetchJson("data/flavor/region_nouns.json"),
      region_adjectives: await fetchJson("data/flavor/region_adjectives.json"),
      element_stat_map: await fetchJson("data/flavor/element-stat-map.json"),
      epithet_conditions: await fetchJson("data/flavor/epithet-conditions.json"),
    },
  };
  return loadGameDataFromRaw(raw);
}
