import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { findStaleCardAssetReferences } from "./cardAssetHygiene";

describe("active card asset references", () => {
  it("contains no retired icon-pack source names or URLs", () => {
    expect(findStaleCardAssetReferences(resolve(process.cwd()))).toEqual([]);
  });

  it("flags a restored retired asset URL in tests/capture.py", () => {
    const gameRoot = mkdtempSync(join(tmpdir(), "holdfast-asset-hygiene-"));
    try {
      for (const directory of ["src", "scripts", "assets", "tests/baseline"]) {
        mkdirSync(join(gameRoot, directory), { recursive: true });
      }
      const stalePath = join(gameRoot, "tests/capture.py");
      writeFileSync(stalePath, `probe = "assets/${["card", "art", "icons"].join("-")}/old.svg"\n`);
      writeFileSync(join(gameRoot, "tests/baseline/ignored.sha1"), "binary baseline");

      expect(findStaleCardAssetReferences(gameRoot)).toEqual([stalePath]);
    } finally {
      rmSync(gameRoot, { recursive: true, force: true });
    }
  });
});
