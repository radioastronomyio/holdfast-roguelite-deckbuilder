import { execFileSync } from "node:child_process";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("derive-runic-card-icons", () => {
  it("derives from a temporary source fixture and rejects stale output", () => {
    const fixtureRoot = mkdtempSync(join(tmpdir(), "holdfast-runic-fixture-"));
    try {
      const sourceRoot = join(fixtureRoot, "source");
      const outputRoot = join(fixtureRoot, "output");
      const committed = JSON.parse(
        readFileSync(resolve(process.cwd(), "assets/card-icons/manifest.json"), "utf8"),
      ) as { assets: Array<{ id: string; mode: string; source: string }> };
      const assets = committed.assets.map(({ id, mode, source }) => ({
        id,
        mode,
        svgPath: source,
        ...(id === "fireball"
          ? { png: { "512": "assets/png/512/spells/fireball.png" } }
          : {}),
      }));
      for (const { id, svgPath } of assets) {
        const path = join(sourceRoot, svgPath);
        mkdirSync(resolve(path, ".."), { recursive: true });
        writeFileSync(
          path,
          `<svg xmlns="http://www.w3.org/2000/svg"><path id="${id}" fill="#fff1d0"/></svg>`,
        );
      }
      mkdirSync(outputRoot, { recursive: true });
      const pngSource = join(sourceRoot, "assets/png/512/spells/fireball.png");
      mkdirSync(resolve(pngSource, ".."), { recursive: true });
      writeFileSync(
        pngSource,
        Buffer.from(
          "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
          "base64",
        ),
      );
      writeFileSync(
        join(outputRoot, "immolate-fireball.png"),
        readFileSync(resolve(process.cwd(), "assets/card-icons/immolate-fireball.png")),
      );
      writeFileSync(join(sourceRoot, "manifest.json"), JSON.stringify({
        name: "Hermetic Runic fixture",
        version: "test",
        assets,
      }));

      execFileSync(
        process.execPath,
        [resolve(process.cwd(), "scripts/derive-runic-card-icons.mjs"), sourceRoot, outputRoot],
        { stdio: "pipe" },
      );
      expect(readFileSync(join(outputRoot, "arcane_burst.svg"), "utf8")).toContain("#f3e2b3");
      const manifest = JSON.parse(readFileSync(join(outputRoot, "manifest.json"), "utf8")) as {
        imageAssets: Array<{
          id: string;
          sourceId: string;
          source: string;
          file: string;
          transformation: string;
          sourceSha256: string;
          derivedSha256: string;
          licenseCoverage: string;
        }>;
      };
      expect(manifest.imageAssets).toEqual([
        expect.objectContaining({
          id: "immolate-fireball",
          sourceId: "fireball",
          source: "assets/png/512/spells/fireball.png",
          file: "immolate-fireball.png",
          transformation: expect.stringContaining("chroma-key"),
          sourceSha256: expect.stringMatching(/^[a-f0-9]{64}$/),
          derivedSha256: expect.stringMatching(/^[a-f0-9]{64}$/),
          licenseCoverage: expect.stringContaining("NOTICE"),
        }),
      ]);

      writeFileSync(join(outputRoot, "stale.svg"), "<svg/>");
      expect(() => execFileSync(
        process.execPath,
        [resolve(process.cwd(), "scripts/derive-runic-card-icons.mjs"), sourceRoot, outputRoot],
        { stdio: "pipe" },
      )).toThrow(/Unexpected files in Runic card icon output: stale\.svg/);
    } finally {
      rmSync(fixtureRoot, { recursive: true, force: true });
    }
  });
});
