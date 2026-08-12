import { execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("derive-runic-card-icons", () => {
  it("fails loudly when the output inventory contains an unexpected stale file", () => {
    const outputRoot = mkdtempSync(join(tmpdir(), "holdfast-runic-icons-"));
    writeFileSync(join(outputRoot, "stale.svg"), "<svg/>");

    expect(() => execFileSync(
      process.execPath,
      [
        resolve(process.cwd(), "scripts/derive-runic-card-icons.mjs"),
        "/opt/agents/repos/html5-game-ui-framework/reference-files-ui/runic-relic-rpg-icons-144",
        outputRoot,
      ],
      { stdio: "pipe" },
    )).toThrow(/Unexpected files in Runic card icon output: stale\.svg/);
  });
});
