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

console.log("Prepared browser data and Pixel Quest assets in game/public/.");
