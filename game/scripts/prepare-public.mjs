import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";

const gameRoot = new URL("..", import.meta.url).pathname;
const repoRoot = join(gameRoot, "..");
const publicRoot = join(gameRoot, "public");
const assetRoot = join(repoRoot, "assets/2d-pixel-quest-vol3-the-ui-gui");

function copyFile(source, destination) {
  if (!existsSync(source)) throw new Error(`Missing required source asset: ${source}`);
  mkdirSync(dirname(destination), { recursive: true });
  cpSync(source, destination);
}

function copyDir(source, destination) {
  if (!existsSync(source)) throw new Error(`Missing required source directory: ${source}`);
  rmSync(destination, { recursive: true, force: true });
  mkdirSync(dirname(destination), { recursive: true });
  cpSync(source, destination, { recursive: true });
}

copyDir(join(repoRoot, "data/cards"), join(publicRoot, "data/cards"));
copyDir(join(repoRoot, "data/campaign"), join(publicRoot, "data/campaign"));
copyDir(join(repoRoot, "data/entities"), join(publicRoot, "data/entities"));
copyFile(join(repoRoot, "data/enums.json"), join(publicRoot, "data/enums.json"));

rmSync(join(publicRoot, "data/flavor"), { recursive: true, force: true });
mkdirSync(join(publicRoot, "data/flavor"), { recursive: true });
for (const file of readdirSync(join(repoRoot, "mods/default/flavor"))) {
  if (file.endsWith(".json")) copyFile(join(repoRoot, "mods/default/flavor", file), join(publicRoot, "data/flavor", file));
}

rmSync(join(publicRoot, "assets"), { recursive: true, force: true });
const assets = [
  ["Font/FantasypixelFont.fnt", "font/fantasypixelfont.fnt"],
  ["Font/FantasypixelFont.png", "font/fantasypixelfont.png"],
  ["Cursors/F_UI_Cursor1.png", "cursors/cursor-1.png"],
  ["Panels/Panels/F_UI_Panel_A.png", "panels/panel-a.png"],
  ["Panels/Panels/F_UI_Panel_B.png", "panels/panel-b.png"],
  ["Panels/Slots/F_U_SlotA1.png", "panels/slot-a1.png"],
  ["Dynamic Bars/F_UI_DynamicBar_A1.png", "bars/dynamic-bar-a1.png"],
  ["Dynamic Bars/F_UI_DynamicBar_B1.png", "bars/dynamic-bar-b1.png"],
  ["Menu Buttons And Switch/Menu Buttons/F_UI_MenuButton_A1.png", "buttons/menu-button-a1.png"],
  ["Menu Buttons And Switch/Menu Buttons/F_UI_MenuButton_A2.png", "buttons/menu-button-a2.png"],
  ["Skill Cards- Flip Animations/Skills face flip/F_U_Card_Ability01_Flip04.png", "cards/card-face-a.png"],
  ["Skill Cards- Flip Animations/Back Face Flip/Back Face Flip A/F_U_CardA_Back_Flip04.png", "cards/card-back-a.png"],
  ["Skill Icons/Gold Icons/F_UI_Skill01.png", "icons/skill-01.png"],
  ["Gems/F_UI_Gem_A1.png", "gems/gem-a1.png"],
  ["Resources Orbs/Type A/ResOrbA_Base.png", "orbs/orb-a-base.png"],
  ["Banners/F_UI_BlueBannerA.png", "banners/blue-banner-a.png"],
  ["Victory Star/F_UI_VictoryStarAnimation_1.png", "victory/victory-star-01.png"]
];

for (const [source, destination] of assets) {
  copyFile(join(assetRoot, source), join(publicRoot, "assets", destination));
}

stageCardIcons();

console.log("Prepared browser data and Pixel Quest assets in game/public/.");

/**
 * Stage the curated RPG icon subset used by the Holdfast card renderer into
 * `public/assets/icons/`, normalizing the source pack's filename quirks so
 * lookups from iconMap.ts are deterministic.
 *
 * The neor-rpg-icon-pack ships a handful of files with a doubled `.png.png`
 * extension and one typo (`ui-watrer-drop.png`). `copyIcon` resolves those by
 * falling back through candidate source spellings, then writes a clean
 * kebab-case destination name. The mapping is the single source of truth for
 * which icons the renderer depends on; adding a tag to iconMap.ts means adding
 * its row here.
 */
function stageCardIcons() {
  const iconPackRoot = "/opt/agents/repos/retro-gaming-html5/asset-game/ui-shared/neor-rpg-icon-pack";
  const destRoot = join(publicRoot, "assets/icons");
  mkdirSync(destRoot, { recursive: true });

  // [pack-relative source path, clean destination name]
  const icons = [
    ["magics/items-magic-sword-empowered-01.png.png", "icon-attack.png"],
    ["magics/items-magic-pentagram-01.png", "icon-magic.png"],
    ["spells/items-spells-fire-01.png", "icon-fire.png"],
    ["spells/items-spells-spiral-01.png", "icon-dot.png"],
    ["items/items-sickle-01.png", "icon-physical.png"],
    ["items/items-sickle-01.png", "icon-shred.png"],
    ["spells/items-spells-tornado-01.png", "icon-control.png"],
    ["magics/items-magic-snowflake-01.png", "icon-snowflake.png"],
    ["spells/items-spells-burst-01.png", "icon-aoe.png"],
    ["armors/armor-shield-01.png", "icon-defense.png"],
    ["magics/items-magic-crystal-ball-01.png", "icon-buff.png"],
    ["spells/items-spells-wind-01.png", "icon-speed.png"],
    ["ui/ui-heart.png", "icon-heal.png"],
    ["items/items-scroll-text-01.png", "icon-utility.png"],
    ["items/items-crystals-01.png", "icon-energy.png"],
    ["spells/items-spells-lightning-01.png", "icon-lightning.png"],
    ["magics/items-magic-pentagram-02.png", "icon-dark.png"],
    ["magics/items-magic-potion-liquid-01.png", "icon-poison.png"],
    ["ui/ui-watrer-drop.png", "icon-bleed.png"],
    ["spells/items-spells-eye-01.png", "icon-weaken.png"],
    ["magics/items-magic-cloud-with-lightning-bolt-01.png", "icon-stun.png"],
    ["ui/ui-star-four-pointed.png", "icon-party.png"],
    ["ui/ui-caution-triangle.png", "icon-hazard.png"],
    ["ui/ui-eye.png", "icon-blind.png"],
    ["ui/ui-question-mark.png", "icon-unknown.png"],
  ];

  for (const [sourceRel, destName] of icons) {
    copyIcon(iconPackRoot, sourceRel, destName, destRoot);
  }
}

/**
 * Copy one icon, normalizing the source filename. Candidates tried in order:
 * the path as written, the path with underscores swapped for hyphens, and the
 * path with a collapsed doubled extension (`.png.png` → `.png`). The first
 * candidate that exists wins; if none exist the source is missing and the
 * build fails loudly.
 */
function copyIcon(packRoot, sourceRel, destName, destRoot) {
  const candidates = [sourceRel];
  if (sourceRel.includes("_")) candidates.push(sourceRel.replaceAll("_", "-"));
  if (sourceRel.endsWith(".png.png")) candidates.push(sourceRel.slice(0, -4));

  const source = candidates
    .map((rel) => join(packRoot, rel))
    .find((path) => existsSync(path));
  if (!source) throw new Error(`Missing icon source: ${sourceRel} (in ${packRoot})`);
  cpSync(source, join(destRoot, destName));
}
