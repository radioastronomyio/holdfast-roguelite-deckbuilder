import { existsSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;

// Representative members of each staged family. The prebuild check fails loudly
// and names whatever is missing if `prepare:public` has not staged the GameUI
// skin, the data, or the card icons. A missing entry means the published build
// would 404 that asset, so this guards the build before it ships.
const required = [
  // Vendored GameUI skin (one of each kind the dark-fantasy CSS references).
  "public/vendor/gameui/themes/dark-fantasy.css",
  "public/vendor/gameui/themes/fonts/Cinzel.ttf",
  "public/vendor/gameui/themes/dark-fantasy-assets/panel-bg.webp",
  "public/vendor/gameui/components/panels/panels.css",
  // Shared game data.
  "public/data/cards/base-cards.json",
  "public/data/flavor/given_names.json",
  // Legacy card-icon subset (retired after the SVG renderer is fully bound).
  "public/assets/icons/icon-attack.png",
  // Zero-raster card-art vocabulary and its attribution.
  "public/assets/card-art-icons/crossed-swords.svg",
  "public/assets/card-art-icons/NOTICE",
];

const missing = required.filter((file) => !existsSync(join(root, file)));

if (missing.length > 0) {
  console.error("Missing browser public assets/data. Run `npm run prepare:public` from game/.");
  for (const file of missing) console.error(`- ${file}`);
  process.exit(1);
}
