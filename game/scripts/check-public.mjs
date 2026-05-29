import { existsSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;
const required = [
  "public/assets/font/fantasypixelfont.fnt",
  "public/assets/font/fantasypixelfont.png",
  "public/assets/panels/panel-a.png",
  "public/assets/bars/dynamic-bar-a1.png",
  "public/data/cards/base-cards.json",
  "public/data/flavor/given_names.json"
];

const missing = required.filter((file) => !existsSync(join(root, file)));

if (missing.length > 0) {
  console.error("Missing browser public assets/data. Run `npm run prepare:public` from game/.");
  for (const file of missing) console.error(`- ${file}`);
  process.exit(1);
}
