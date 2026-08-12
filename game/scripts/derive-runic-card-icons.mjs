import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptRoot = dirname(fileURLToPath(import.meta.url));
const gameRoot = resolve(scriptRoot, "..");
const sourceRoot = resolve(
  process.argv[2]
    ?? "/opt/agents/repos/html5-game-ui-framework/reference-files-ui/runic-relic-rpg-icons-144",
);
const outputRoot = join(gameRoot, "assets/card-icons");

const selectedIds = new Set([
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
]);

const palette = new Map([
  ["#fff1d0", "#f3e2b3"],
  ["#e45a68", "#9d3f4d"],
  ["#f0c65a", "#c49a43"],
  ["#5bc0eb", "#477a85"],
  ["#6fd08c", "#5f8d6d"],
  ["#9c75e8", "#795d9c"],
  ["#2b3540", "#34313a"],
  ["#1b242d", "#211e27"],
  ["#11161c", "#141118"],
  ["#080b0f", "#09070c"],
  ["#000000", "#050308"],
]);

const sourceManifest = JSON.parse(readFileSync(join(sourceRoot, "manifest.json"), "utf8"));
const selected = sourceManifest.assets
  .filter(({ id }) => selectedIds.has(id))
  .sort((left, right) => left.id.localeCompare(right.id));

if (selected.length !== selectedIds.size) {
  const found = new Set(selected.map(({ id }) => id));
  const missing = [...selectedIds].filter((id) => !found.has(id));
  throw new Error(`Runic Relic manifest is missing required icons: ${missing.join(", ")}`);
}

mkdirSync(outputRoot, { recursive: true });
for (const asset of selected) {
  const sourcePath = join(sourceRoot, asset.svgPath);
  let derived = readFileSync(sourcePath, "utf8");
  for (const [sourceColour, holdfastColour] of palette) {
    derived = derived.replaceAll(new RegExp(sourceColour, "gi"), holdfastColour);
  }
  derived = derived.replace(
    "<svg ",
    `<svg data-holdfast-derived-from="${asset.id}" `,
  );
  derived = derived.replace(
    /(<svg[^>]*>)/,
    `$1\n  <metadata>Holdfast recolour derived from Runic Relic RPG Icons 144 (${asset.id}, ${asset.mode} mode).</metadata>`,
  );
  writeFileSync(join(outputRoot, `${asset.id}.svg`), derived);
}

const derivedManifest = {
  name: "Holdfast Runic card icon vocabulary",
  sourcePack: sourceManifest.name,
  sourceVersion: sourceManifest.version,
  transformation: "Holdfast dark-fantasy palette recolour plus provenance metadata",
  assets: selected.map((asset) => ({
    id: asset.id,
    mode: asset.mode,
    source: asset.svgPath,
    file: `${asset.id}.svg`,
  })),
};
writeFileSync(
  join(outputRoot, "manifest.json"),
  `${JSON.stringify(derivedManifest, null, 2)}\n`,
);

console.log(`Derived ${selected.length} Runic Relic SVGs into ${outputRoot}.`);
