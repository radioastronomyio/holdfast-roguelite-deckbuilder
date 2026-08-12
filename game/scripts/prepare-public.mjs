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

// --- Zero-raster card art (in-repo source) ---
rmSync(join(publicRoot, "assets"), { recursive: true, force: true });
stageCardIcons();

console.log("Prepared browser data, GameUI vendor skin, and card SVG assets in game/public/.");

/** Stage the licensed Runic Relic-derived SVG vocabulary used by card art. */
function stageCardIcons() {
  copyDir(
    join(gameRoot, "assets/card-icons"),
    join(publicRoot, "assets/card-icons"),
  );
}
