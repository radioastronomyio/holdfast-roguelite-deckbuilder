import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

function filesBelow(root: string): string[] {
  return readdirSync(root).flatMap((entry) => {
    const path = join(root, entry);
    return statSync(path).isDirectory() ? filesBelow(path) : [path];
  });
}

describe("active card asset references", () => {
  it("contains no retired icon-pack source names or URLs", () => {
    const gameRoot = resolve(process.cwd());
    const activeFiles = ["src", "scripts", "assets"].flatMap((directory) => (
      filesBelow(join(gameRoot, directory))
    ));
    const retiredPath = ["card", "art", "icons"].join("-");
    const retiredPack = /game[- ]icons/i;
    const stale = activeFiles.filter((path) => {
      const source = readFileSync(path, "utf8");
      return source.includes(retiredPath) || retiredPack.test(source);
    });

    expect(stale).toEqual([]);
  });
});
