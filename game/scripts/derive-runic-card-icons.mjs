import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptRoot = dirname(fileURLToPath(import.meta.url));
const gameRoot = resolve(scriptRoot, "..");
const sourceRoot = resolve(
  process.argv[2]
    ?? "/opt/agents/repos/html5-game-ui-framework/reference-files-ui/runic-relic-rpg-icons-144",
);
const outputRoot = resolve(process.argv[3] ?? join(gameRoot, "assets/card-icons"));
const imageDerivative = Object.freeze({
  id: "immolate-fireball",
  sourceId: "fireball",
  file: "immolate-fireball.png",
  transformation:
    "AI-assisted dark-fantasy restyle, flat-key background replacement, chroma-key transparency removal, and 512px normalization",
  licenseCoverage: "Covered by the Runic Relic royalty-free source license documented in NOTICE",
});

function sha256(path) {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

function assertPng(path, label) {
  const bytes = readFileSync(path);
  const signature = bytes.subarray(0, 8).toString("hex");
  const firstChunk = bytes.subarray(12, 16).toString("ascii");
  if (bytes.length < 24 || signature !== "89504e470d0a1a0a" || firstChunk !== "IHDR") {
    throw new Error(`${label} is not a valid PNG: ${path}`);
  }
}

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

const imageSourceAsset = selected.find(({ id }) => id === imageDerivative.sourceId);
const imageSourceRelative = imageSourceAsset?.png?.["512"];
if (!imageSourceRelative) {
  throw new Error(
    `Runic Relic manifest is missing the 512px PNG for ${imageDerivative.sourceId}`,
  );
}
const imageSourcePath = join(sourceRoot, imageSourceRelative);
const imageDerivedPath = join(outputRoot, imageDerivative.file);

const expectedOutputFiles = new Set([
  ...selected.map(({ id }) => `${id}.svg`),
  "README.md",
  "NOTICE",
  "manifest.json",
  imageDerivative.file,
]);
if (existsSync(outputRoot)) {
  const unexpected = readdirSync(outputRoot)
    .filter((file) => !expectedOutputFiles.has(file))
    .sort();
  if (unexpected.length > 0) {
    throw new Error(`Unexpected files in Runic card icon output: ${unexpected.join(", ")}`);
  }
}

mkdirSync(outputRoot, { recursive: true });
if (!existsSync(imageDerivedPath)) {
  throw new Error(
    `Required edited PNG derivative is missing (the derivation command preserves it): ${imageDerivedPath}`,
  );
}
assertPng(imageSourcePath, "Runic Relic source");
assertPng(imageDerivedPath, "Holdfast image derivative");
if (sha256(imageSourcePath) === sha256(imageDerivedPath)) {
  throw new Error("Holdfast image derivative must not be a byte-identical raw pack export");
}

const derivedAssets = [];
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
  const derivedPath = join(outputRoot, `${asset.id}.svg`);
  writeFileSync(derivedPath, derived);
  derivedAssets.push({
    id: asset.id,
    mode: asset.mode,
    source: asset.svgPath,
    file: `${asset.id}.svg`,
    sourceSha256: sha256(sourcePath),
    derivedSha256: sha256(derivedPath),
  });
}

const derivedManifest = {
  name: "Holdfast Runic card icon vocabulary",
  sourcePack: sourceManifest.name,
  sourceVersion: sourceManifest.version,
  transformation: "Holdfast dark-fantasy palette recolour plus provenance metadata",
  licenseNotice: "NOTICE",
  assets: derivedAssets,
  imageAssets: [{
    ...imageDerivative,
    mode: imageSourceAsset.mode,
    source: imageSourceRelative,
    sourceSha256: sha256(imageSourcePath),
    derivedSha256: sha256(imageDerivedPath),
  }],
};
writeFileSync(
  join(outputRoot, "manifest.json"),
  `${JSON.stringify(derivedManifest, null, 2)}\n`,
);

console.log(
  `Derived ${selected.length} Runic Relic SVGs and verified ${imageDerivative.file} in ${outputRoot}.`,
);
