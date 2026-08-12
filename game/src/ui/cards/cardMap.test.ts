import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, expectTypeOf, it } from "vitest";
import baseCardsJson from "../../../../data/cards/base-cards.json";
import hazardCardsJson from "../../../../data/cards/hazard-cards.json";
import upgradeTreesJson from "../../../../data/cards/upgrade-trees.json";
import type { Card, Modifier, UpgradeTree } from "../../sim/types";
import type { HoldfastCardOptions } from "./contract";
import {
  CARD_VISUAL_IDS,
  CARD_ART_SYMBOLS,
  RUNIC_ICON_MODES,
  cardIconUrl,
  resolveCardVisual,
  resolveEffectSymbol,
} from "./cardMap";

const cards = [
  ...(baseCardsJson as unknown as Card[]),
  ...(hazardCardsJson as unknown as Card[]),
];
const upgradeTrees = upgradeTreesJson as unknown as Record<string, UpgradeTree>;
const upgradeEffects = Object.entries(upgradeTrees).flatMap(([cardId, tree]) => (
  Object.entries(tree).flatMap(([branchId, branch]) => (
    branch.added_effects.map((effect) => ({ cardId, branchId, effect }))
  ))
));

const expectedMotifs: Readonly<Record<string, string>> = {
  arcane_strike_01: "arcane_burst",
  immolate_01: "fireball",
  shield_bash_01: "tower_shield",
  sweeping_blade_01: "crescent_blade",
  phalanx_01: "barrier_spell",
  adrenaline_01: "swift_boots",
  cleanse_01: "holy_ray",
  deep_focus_01: "mana_orb",
  acid_flask_01: "black_bomb",
  frost_bolt_01: "frostbite",
  power_surge_01: "rage_surge",
  stone_wall_01: "stone_spike",
  lightning_chain_01: "thunder_arc",
  heal_potion_01: "health_potion",
  drain_life_01: "life_drain",
  tripwire_hazard_01: "root_snare",
  miasma_hazard_01: "tidal_surge",
  toxic_fumes_hazard_01: "poison_cloud",
  freezing_wind_hazard_01: "wind_cut",
  crushing_weight_hazard_01: "rune_hammer",
  blinding_light_hazard_01: "warning",
};

const expectedRunicIcons = [
  "arcane_burst",
  "barrier_spell",
  "black_bomb",
  "crescent_blade",
  "fireball",
  "frostbite",
  "healing_light",
  "health_potion",
  "holy_ray",
  "life_drain",
  "mana_orb",
  "poison_cloud",
  "rage_surge",
  "root_snare",
  "rune_hammer",
  "stone_spike",
  "swift_boots",
  "thunder_arc",
  "tidal_surge",
  "tower_shield",
  "warning",
  "wind_cut",
] as const;

const expectedRunicModes = {
  arcane_burst: "rune",
  barrier_spell: "barrier",
  black_bomb: "bomb",
  crescent_blade: "sword",
  fireball: "flame",
  frostbite: "frost",
  healing_light: "heart",
  health_potion: "potion",
  holy_ray: "sun",
  life_drain: "skull",
  mana_orb: "gem",
  poison_cloud: "poison",
  rage_surge: "claw",
  root_snare: "root",
  rune_hammer: "hammer",
  stone_spike: "earth",
  swift_boots: "boots",
  thunder_arc: "bolt",
  tidal_surge: "wave",
  tower_shield: "shield",
  warning: "warning",
  wind_cut: "wind",
} as const;

const expectedTagModes: Readonly<Record<string, string>> = {
  aoe: "wave",
  attack: "sword",
  bleed: "claw",
  blind: "sun",
  buff: "rune",
  control: "root",
  dark: "skull",
  debuff: "warning",
  defense: "barrier",
  dot: "flame",
  energy: "gem",
  fire: "flame",
  hazard: "warning",
  heal: "heart",
  ice: "frost",
  lifesteal: "skull",
  lightning: "bolt",
  magic: "rune",
  party: "barrier",
  physical: "sword",
  poison: "poison",
  power: "claw",
  pressure: "hammer",
  regen: "heart",
  shred: "poison",
  slow: "boots",
  speed: "boots",
  stun: "root",
  trap: "root",
  utility: "gem",
  weaken: "warning",
};

const expectedStatModes: Readonly<Record<string, string>> = {
  HP: "heart",
  Power: "claw",
  Speed: "boots",
  Defense: "barrier",
  Energy: "gem",
};

describe("card visual mappings", () => {
  it("maps every base and hazard card to a curated motif, palette, and tag-derived ground", () => {
    expect(cards).toHaveLength(21);
    for (const card of cards) {
      const visual = resolveCardVisual(card);
      expect(CARD_ART_SYMBOLS, card.id).toContain(visual.motif);
      expect(visual.palette, card.id).toMatch(/^(primary|success|warning|danger|info|magic|pink)$/);
      expect(visual.ground, card.id).toMatch(/^(arcane|ash|ice|marsh|ruin|stone|thicket)$/);
    }
  });

  it("locks the visual rows to exactly the current JSON card IDs", () => {
    expect([...CARD_VISUAL_IDS].sort()).toEqual(cards.map((card) => card.id).sort());
  });

  it("maps every card identity to its literal Runic Relic-derived motif", () => {
    for (const card of cards) {
      const visual = resolveCardVisual(card);
      expect(visual.motif, card.id).toBe(expectedMotifs[card.id]);
      expect(RUNIC_ICON_MODES[visual.motif], card.id).toBe(
        expectedRunicModes[visual.motif],
      );
    }
  });

  it("keeps art-source selection in presentation, with SVG as the default and Immolate as the PNG exemplar", () => {
    const byId = Object.fromEntries(cards.map((card) => [card.id, card]));

    expect(resolveCardVisual(byId.arcane_strike_01!).artSource).toBe("svg");
    expect(resolveCardVisual(byId.immolate_01!).artSource).toBe("image");
  });

  it("does not expose the presentation art source through card JSON or the frozen factory options", () => {
    expect(cards.every((card) => !Object.hasOwn(card, "artSource"))).toBe(true);
    expectTypeOf<"artSource" extends keyof HoldfastCardOptions ? true : false>()
      .toEqualTypeOf<false>();
  });

  it("backs every semantic tag and tagless stat fallback with its expected Runic mode", () => {
    for (const [tag, expectedMode] of Object.entries(expectedTagModes)) {
      const modifier = { tags: [tag], stat: "HP" } as unknown as Modifier;
      const symbol = resolveEffectSymbol(modifier);
      expect(RUNIC_ICON_MODES[symbol], tag).toBe(expectedMode);
    }
    for (const [stat, expectedMode] of Object.entries(expectedStatModes)) {
      const modifier = { tags: [], stat } as unknown as Modifier;
      const symbol = resolveEffectSymbol(modifier);
      expect(RUNIC_ICON_MODES[symbol], stat).toBe(expectedMode);
    }
  });

  it("fails loudly when a card ID has no explicit visual row", () => {
    expect(() => resolveCardVisual({ id: "unknown_card_01", tags: ["attack"] } as Card)).toThrow(
      /Unmapped card visual: id=unknown_card_01/,
    );
  });

  it("gives Arcane Strike, Immolate, and Shield Bash distinct scene axes", () => {
    const byId = Object.fromEntries(cards.map((card) => [card.id, card]));
    const arcaneStrike = resolveCardVisual(byId.arcane_strike_01!);
    const immolate = resolveCardVisual(byId.immolate_01!);
    const shieldBash = resolveCardVisual(byId.shield_bash_01!);

    expect(new Set([arcaneStrike.palette, immolate.palette, shieldBash.palette]).size).toBe(3);
    expect(new Set([arcaneStrike.ground, immolate.ground, shieldBash.ground]).size).toBe(3);
    expect(new Set([arcaneStrike.motif, immolate.motif, shieldBash.motif]).size).toBe(3);
  });

  it("maps every real modifier to a curated effect symbol", () => {
    for (const card of cards) {
      for (const effect of card.effects) {
        expect(CARD_ART_SYMBOLS, `${card.id}: ${effect.stat}`).toContain(
          resolveEffectSymbol(effect),
        );
      }
    }
    expect(upgradeEffects).toHaveLength(90);
    for (const { cardId, branchId, effect } of upgradeEffects) {
      expect(CARD_ART_SYMBOLS, `${cardId}/${branchId}: ${effect.stat}`).toContain(
        resolveEffectSymbol(effect),
      );
    }
  });

  it("fails loudly when neither effect tags nor stat have a symbol mapping", () => {
    const unmapped = {
      stat: "Fortune",
      operation: "FLAT_ADD",
      value: 1,
      duration: 0,
      target: "SELF",
      stacking: "stack",
      tags: ["unmapped"],
    } as unknown as Modifier;

    expect(() => resolveEffectSymbol(unmapped)).toThrow(/Unmapped card effect/);
  });

  it("rejects unknown non-empty effect tags even when the stat is known", () => {
    const unknownTaggedHp = {
      stat: "HP",
      operation: "FLAT_ADD",
      value: 1,
      duration: 0,
      target: "SELF",
      stacking: "stack",
      tags: ["unmapped"],
    } as unknown as Modifier;

    expect(() => resolveEffectSymbol(unknownTaggedHp)).toThrow(
      /Unmapped card effect: stat=HP tags=unmapped/,
    );
  });

  it("uses a stat fallback only for a tagless effect", () => {
    const taglessHp = {
      stat: "HP",
      operation: "FLAT_ADD",
      value: 1,
      duration: 0,
      target: "SELF",
      stacking: "stack",
      tags: [],
    } as unknown as Modifier;

    expect(resolveEffectSymbol(taglessHp)).toBe("healing_light");
  });

  it("builds stable SVG and future PNG URLs under the Runic card-icon path", () => {
    expect(cardIconUrl("arcane_burst", "svg")).toBe(
      "/assets/card-icons/arcane_burst.svg",
    );
    expect(cardIconUrl("arcane_burst", "png")).toBe(
      "/assets/card-icons/arcane_burst.png",
    );
  });

  it("ships the exact derived Runic vocabulary with provenance and license facts", () => {
    const assetRoot = resolve(process.cwd(), "assets/card-icons");
    expect([...CARD_ART_SYMBOLS].sort()).toEqual([...expectedRunicIcons].sort());
    for (const icon of expectedRunicIcons) {
      expect(existsSync(resolve(assetRoot, `${icon}.svg`)), icon).toBe(true);
    }

    const manifest = JSON.parse(readFileSync(resolve(assetRoot, "manifest.json"), "utf8")) as {
      licenseNotice: string;
      assets: Array<{
        id: string;
        mode: string;
        source: string;
        file: string;
        sourceSha256: string;
        derivedSha256: string;
      }>;
      imageAssets: Array<{
        id: string;
        sourceId: string;
        mode: string;
        source: string;
        file: string;
        transformation: string;
        sourceSha256: string;
        derivedSha256: string;
        licenseCoverage: string;
      }>;
    };
    expect(manifest.assets.map(({ id }) => id).sort()).toEqual([...expectedRunicIcons].sort());
    expect(Object.fromEntries(manifest.assets.map(({ id, mode }) => [id, mode]))).toEqual(
      expectedRunicModes,
    );
    expect(RUNIC_ICON_MODES).toEqual(expectedRunicModes);
    expect(manifest.assets.every(({ source, file }) => (
      source.startsWith("assets/svg/") && file.endsWith(".svg")
    ))).toBe(true);
    expect(manifest.assets.every(({ sourceSha256, derivedSha256 }) => (
      /^[a-f0-9]{64}$/.test(sourceSha256) && /^[a-f0-9]{64}$/.test(derivedSha256)
    ))).toBe(true);
    expect(manifest.licenseNotice).toBe("NOTICE");
    expect(manifest.imageAssets).toEqual([
      expect.objectContaining({
        id: "immolate-fireball",
        sourceId: "fireball",
        mode: "flame",
        source: "assets/png/512/spells/fireball.png",
        file: "immolate-fireball.png",
        transformation: expect.stringContaining("chroma-key"),
        sourceSha256: "3660f30fed01ac9181e72f8379e34d7db6b59947038c32f76bcc5b624a1005d2",
        derivedSha256: "d281d861c645d6020de98db02d8b661341aa69482099b05cf1975f97983a837c",
        licenseCoverage: expect.stringContaining("NOTICE"),
      }),
    ]);

    const notice = readFileSync(resolve(assetRoot, "NOTICE"), "utf8");
    expect(notice).toContain("Template Foundry");
    expect(notice).toContain("Runic Relic RPG Icons 144");
    expect(notice).toContain("Royalty-free asset license for the purchaser");
  });

  it("uses the card identity as a variety axis within one tag family", () => {
    expect(resolveCardVisual({ id: "sweeping_blade_01", tags: ["attack", "physical"] } as Card)).not.toEqual(
      resolveCardVisual({ id: "shield_bash_01", tags: ["attack", "physical", "control"] } as Card),
    );
  });
});
