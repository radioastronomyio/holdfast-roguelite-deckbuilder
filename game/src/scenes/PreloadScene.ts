import * as Phaser from "phaser";
import { assetManifest, jsonManifest } from "../assets/manifest";
import { loadGameDataFromRaw } from "../sim/loader";
import type { RawGameData } from "../sim/types";
import { label, panel } from "../ui/theme";

type JsonManifestEntry = { key: string; path: string };

export class PreloadScene extends Phaser.Scene {
  constructor() {
    super("PreloadScene");
  }

  preload(): void {
    panel(this, 390, 312, 500, 96);
    const progress = this.add.image(420, 364, assetManifest.bars.hp.key).setOrigin(0, 0).setDisplaySize(1, 22);
    label(this, 420, 328, "Loading", 24);
    this.load.on(Phaser.Loader.Events.PROGRESS, (value: number) => {
      progress.setDisplaySize(Math.floor(440 * value), 22);
    });

    this.loadRemainingAssets();
    for (const entry of Object.values(jsonManifest) as JsonManifestEntry[]) this.load.json(entry.key, entry.path);
  }

  create(): void {
    const raw: RawGameData = {
      base_cards: this.cache.json.get(jsonManifest.baseCards.key),
      hazard_cards: this.cache.json.get(jsonManifest.hazardCards.key),
      upgrade_trees: this.cache.json.get(jsonManifest.upgradeTrees.key),
      characters: this.cache.json.get(jsonManifest.characters.key),
      enemies: this.cache.json.get(jsonManifest.enemies.key),
      generation_bounds: this.cache.json.get(jsonManifest.generationBounds.key),
      regions: this.cache.json.get(jsonManifest.regions.key),
      world_deck: this.cache.json.get(jsonManifest.worldDeck.key),
      outpost_upgrades: this.cache.json.get(jsonManifest.outpostUpgrades.key),
      flavor: {
        given_names: this.cache.json.get(jsonManifest.flavorGivenNames.key),
        archetypes: this.cache.json.get(jsonManifest.flavorArchetypes.key),
        region_nouns: this.cache.json.get(jsonManifest.flavorRegionNouns.key),
        region_adjectives: this.cache.json.get(jsonManifest.flavorRegionAdjectives.key),
        element_stat_map: this.cache.json.get(jsonManifest.flavorElementStatMap.key),
        epithet_conditions: this.cache.json.get(jsonManifest.flavorEpithetConditions.key)
      }
    };
    this.registry.set("gameData", loadGameDataFromRaw(raw));
    this.scene.start("MainMenuScene");
  }

  private loadRemainingAssets(): void {
    const imageEntries = [
      assetManifest.panels.secondary,
      assetManifest.panels.slot,
      assetManifest.bars.energy,
      assetManifest.buttons.normal,
      assetManifest.buttons.hover,
      assetManifest.cards.face,
      assetManifest.cards.back,
      assetManifest.icons.skill,
      assetManifest.icons.gem,
      assetManifest.icons.orb,
      assetManifest.banners.blue,
      assetManifest.victory.star
    ];
    for (const entry of imageEntries) this.load.image(entry.key, entry.path);
  }
}
