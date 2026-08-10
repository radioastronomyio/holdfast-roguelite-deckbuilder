/** Behavior tests for the repository-scoped production publisher. */
import { execFileSync, spawnSync } from "node:child_process";
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

const SCRIPT = fileURLToPath(new URL("../../../publish.sh", import.meta.url));

let fixtureRoot: string;
let source: string;
let target: string;

function writeFixture(path: string, content: string): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, content);
}

function filesUnder(root: string): string[] {
  const entries = readdirSync(root, { recursive: true, withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile())
    .map((entry) => relative(root, resolve(entry.parentPath, entry.name)))
    .sort();
}

function runPublisher(targetPath = target) {
  return spawnSync(
    "bash",
    [SCRIPT, "--deploy-only", "--source", source, "--target", targetPath],
    {
      encoding: "utf8",
      env: {
        ...process.env,
        HOLDFAST_PUBLISH_TEST: "1",
        HOLDFAST_PUBLISH_TEST_ROOT: fixtureRoot,
      },
    },
  );
}

describe("publish.sh", () => {
  beforeEach(() => {
    fixtureRoot = mkdtempSync(join(tmpdir(), "holdfast-publish-"));
    source = join(fixtureRoot, "dist");
    target = join(fixtureRoot, "www", "holdfast");
    writeFixture(join(source, "index.html"), "<main>Holdfast</main>\n");
    writeFixture(join(source, "assets", "index-abc123.js"), "export const build = 'abc123';\n");
  });

  afterEach(() => {
    rmSync(fixtureRoot, { recursive: true, force: true });
  });

  it("mirrors the build exactly and removes only stale files inside the target", () => {
    writeFixture(join(target, "stale.txt"), "retired\n");

    const result = runPublisher();

    expect(result.status, result.stderr).toBe(0);
    expect(filesUnder(target)).toEqual(filesUnder(source));
    for (const path of filesUnder(source)) {
      expect(readFileSync(join(target, path))).toEqual(readFileSync(join(source, path)));
    }
  });

  it("is idempotent when source and target already match", () => {
    const first = runPublisher();
    expect(first.status, first.stderr).toBe(0);
    const deployed = join(target, "assets", "index-abc123.js");
    const firstMtime = statSync(deployed).mtimeMs;

    const second = runPublisher();

    expect(second.status, second.stderr).toBe(0);
    expect(statSync(deployed).mtimeMs).toBe(firstMtime);
    execFileSync("diff", ["-r", source, target]);
  });

  it("rejects a test target outside the explicitly bounded fixture root", () => {
    const outside = join(dirname(fixtureRoot), "not-the-holdfast-fixture");

    const result = runPublisher(outside);

    expect(result.status).not.toBe(0);
    expect(result.stderr).toContain("outside HOLDFAST_PUBLISH_TEST_ROOT");
  });
});
