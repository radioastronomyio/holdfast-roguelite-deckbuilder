import { readFile } from "node:fs/promises";
import path from "node:path";
import { loadGameDataFromRaw } from "./loader";
import type { RawGameData } from "./types";

async function readJson<T>(filePath: string): Promise<T> {
  return JSON.parse(await readFile(filePath, "utf8")) as T;
}

export async function loadGameDataFromPath(dataPath: string): Promise<ReturnType<typeof loadGameDataFromRaw>> {
  const root = path.resolve(dataPath);
  const repoRoot = path.resolve(root, "..");
  const flavorRoot = path.join(repoRoot, "mods", "default", "flavor");
  const raw: RawGameData = {
    base_cards: await readJson(path.join(root, "cards", "base-cards.json")),
    hazard_cards: await readJson(path.join(root, "cards", "hazard-cards.json")),
    upgrade_trees: await readJson(path.join(root, "cards", "upgrade-trees.json")),
    characters: await readJson(path.join(root, "entities", "example-characters.json")),
    enemies: await readJson(path.join(root, "entities", "example-enemies.json")),
    generation_bounds: await readJson(path.join(root, "entities", "generation-bounds.json")),
    regions: await readJson(path.join(root, "campaign", "example-regions.json")),
    world_deck: await readJson(path.join(root, "campaign", "world-deck.json")),
    outpost_upgrades: await readJson(path.join(root, "campaign", "outpost-upgrades.json")),
    flavor: {
      given_names: await readJson(path.join(flavorRoot, "given_names.json")),
      archetypes: await readJson(path.join(flavorRoot, "archetypes.json")),
      region_nouns: await readJson(path.join(flavorRoot, "region_nouns.json")),
      region_adjectives: await readJson(path.join(flavorRoot, "region_adjectives.json")),
      element_stat_map: await readJson(path.join(flavorRoot, "element-stat-map.json")),
      epithet_conditions: await readJson(path.join(flavorRoot, "epithet-conditions.json"))
    }
  };
  return loadGameDataFromRaw(raw);
}
