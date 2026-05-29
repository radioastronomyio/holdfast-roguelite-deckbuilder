export const assetManifest = {
  font: {
    key: "fantasy",
    fnt: "assets/font/fantasypixelfont.fnt",
    image: "assets/font/fantasypixelfont.png"
  },
  cursor: { key: "cursor", path: "assets/cursors/cursor-1.png" },
  panels: {
    primary: { key: "panel-primary", path: "assets/panels/panel-a.png" },
    secondary: { key: "panel-secondary", path: "assets/panels/panel-b.png" },
    slot: { key: "panel-slot", path: "assets/panels/slot-a1.png" }
  },
  bars: {
    hp: { key: "bar-hp", path: "assets/bars/dynamic-bar-a1.png" },
    energy: { key: "bar-energy", path: "assets/bars/dynamic-bar-b1.png" }
  },
  buttons: {
    normal: { key: "button-normal", path: "assets/buttons/menu-button-a1.png" },
    hover: { key: "button-hover", path: "assets/buttons/menu-button-a2.png" }
  },
  cards: {
    face: { key: "card-face", path: "assets/cards/card-face-a.png" },
    back: { key: "card-back", path: "assets/cards/card-back-a.png" }
  },
  icons: {
    skill: { key: "icon-skill", path: "assets/icons/skill-01.png" },
    gem: { key: "gem", path: "assets/gems/gem-a1.png" },
    orb: { key: "orb", path: "assets/orbs/orb-a-base.png" }
  },
  banners: {
    blue: { key: "banner-blue", path: "assets/banners/blue-banner-a.png" }
  },
  victory: {
    star: { key: "victory-star", path: "assets/victory/victory-star-01.png" }
  }
} as const;

export const jsonManifest = {
  baseCards: { key: "data-base-cards", path: "data/cards/base-cards.json" },
  hazardCards: { key: "data-hazard-cards", path: "data/cards/hazard-cards.json" },
  upgradeTrees: { key: "data-upgrade-trees", path: "data/cards/upgrade-trees.json" },
  characters: { key: "data-characters", path: "data/entities/example-characters.json" },
  enemies: { key: "data-enemies", path: "data/entities/example-enemies.json" },
  generationBounds: { key: "data-generation-bounds", path: "data/entities/generation-bounds.json" },
  regions: { key: "data-regions", path: "data/campaign/example-regions.json" },
  worldDeck: { key: "data-world-deck", path: "data/campaign/world-deck.json" },
  outpostUpgrades: { key: "data-outpost-upgrades", path: "data/campaign/outpost-upgrades.json" },
  flavorGivenNames: { key: "flavor-given-names", path: "data/flavor/given_names.json" },
  flavorArchetypes: { key: "flavor-archetypes", path: "data/flavor/archetypes.json" },
  flavorRegionNouns: { key: "flavor-region-nouns", path: "data/flavor/region_nouns.json" },
  flavorRegionAdjectives: { key: "flavor-region-adjectives", path: "data/flavor/region_adjectives.json" },
  flavorElementStatMap: { key: "flavor-element-stat-map", path: "data/flavor/element-stat-map.json" },
  flavorEpithetConditions: { key: "flavor-epithet-conditions", path: "data/flavor/epithet-conditions.json" }
} as const;
