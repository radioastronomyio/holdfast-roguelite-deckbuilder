import { cpSync, existsSync, mkdirSync, readdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";

const gameRoot = new URL("..", import.meta.url).pathname;
const repoRoot = join(gameRoot, "..");
const publicRoot = join(gameRoot, "public");

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

// --- Shared game data (source of truth under repo data/ + mods/) ---
copyDir(join(repoRoot, "data/cards"), join(publicRoot, "data/cards"));
copyDir(join(repoRoot, "data/campaign"), join(publicRoot, "data/campaign"));
copyDir(join(repoRoot, "data/entities"), join(publicRoot, "data/entities"));
copyFile(join(repoRoot, "data/enums.json"), join(publicRoot, "data/enums.json"));

rmSync(join(publicRoot, "data/flavor"), { recursive: true, force: true });
mkdirSync(join(publicRoot, "data/flavor"), { recursive: true });
for (const file of readdirSync(join(repoRoot, "mods/default/flavor"))) {
  if (file.endsWith(".json")) copyFile(join(repoRoot, "mods/default/flavor", file), join(publicRoot, "data/flavor", file));
}

// --- Vendored GameUI framework (the dark-fantasy skin) ---
// index.html links the framework stylesheets by absolute /vendor/gameui/...
// paths. The dev server resolves those from the project root (game/vendor/),
// but `vite build` only emits the publicDir tree into dist/, so the vendored
// framework must be staged under public/ to be copied into dist/ and resolve
// under the production preview. The source of truth stays pinned at
// game/vendor/gameui/; this is a generated, gitignored copy.
copyDir(join(gameRoot, "vendor/gameui"), join(publicRoot, "vendor/gameui"));

// --- Card icons (in-repo source) ---
rmSync(join(publicRoot, "assets"), { recursive: true, force: true });
stageCardIcons();

console.log("Prepared browser data, GameUI vendor skin, and card icons in game/public/.");

/**
 * Stage the curated RPG icon subset used by the Holdfast card renderer into
 * `public/assets/icons/` from the in-repo source at `game/assets/card-icons/`.
 *
 * The neor-rpg-icon-pack subset is vendored in-repo under normalized clean
 * kebab names, so staging is a straight file copy and the build is hermetic on
 * any host — no out-of-repo absolute paths are read. The list below is the
 * single source of truth for which icons the renderer depends on: adding a tag
 * to iconMap.ts means adding its filename here.
 */
function stageCardIcons() {
  const iconSrcRoot = join(gameRoot, "assets/card-icons");
  const destRoot = join(publicRoot, "assets/icons");
  if (!existsSync(iconSrcRoot)) throw new Error(`Missing in-repo icon source directory: ${iconSrcRoot}`);
  mkdirSync(destRoot, { recursive: true });

  // Filenames iconMap.ts resolves: tag icons, stat-fallback icons, and default.
  const icons = [
    "icon-attack.png", "icon-magic.png", "icon-fire.png", "icon-dot.png",
    "icon-physical.png", "icon-shred.png", "icon-control.png", "icon-snowflake.png",
    "icon-aoe.png", "icon-defense.png", "icon-buff.png", "icon-speed.png",
    "icon-heal.png", "icon-utility.png", "icon-energy.png", "icon-lightning.png",
    "icon-dark.png", "icon-poison.png", "icon-bleed.png", "icon-weaken.png",
    "icon-stun.png", "icon-party.png", "icon-hazard.png", "icon-blind.png",
    "icon-unknown.png",
  ];

  for (const name of icons) {
    const source = join(iconSrcRoot, name);
    if (!existsSync(source)) throw new Error(`Missing in-repo icon source: ${source}`);
    cpSync(source, join(destRoot, name));
  }
}
