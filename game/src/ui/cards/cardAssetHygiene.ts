import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { basename, extname, join } from "node:path";

const ACTIVE_SOURCE_ROOTS = ["src", "scripts", "assets", "tests"] as const;
const IGNORED_DIRECTORIES = new Set(["baseline", "__pycache__"]);
const TEXT_EXTENSIONS = new Set([
  ".css",
  ".html",
  ".js",
  ".json",
  ".md",
  ".mjs",
  ".py",
  ".svg",
  ".ts",
  ".tsx",
  ".txt",
]);
const TEXT_BASENAMES = new Set(["LICENSE", "NOTICE"]);

function activeTextFilesBelow(root: string): string[] {
  if (!existsSync(root)) return [];
  return readdirSync(root).flatMap((entry) => {
    const path = join(root, entry);
    if (statSync(path).isDirectory()) {
      return IGNORED_DIRECTORIES.has(entry) ? [] : activeTextFilesBelow(path);
    }
    return TEXT_EXTENSIONS.has(extname(entry)) || TEXT_BASENAMES.has(basename(entry))
      ? [path]
      : [];
  });
}

/** Return active game files that still name the retired card-icon source/URL. */
export function findStaleCardAssetReferences(gameRoot: string): string[] {
  const retiredPath = ["card", "art", "icons"].join("-");
  const retiredPack = /game[- ]icons/i;
  return ACTIVE_SOURCE_ROOTS
    .flatMap((directory) => activeTextFilesBelow(join(gameRoot, directory)))
    .filter((path) => {
      const source = readFileSync(path, "utf8");
      return source.includes(retiredPath) || retiredPack.test(source);
    })
    .sort();
}
