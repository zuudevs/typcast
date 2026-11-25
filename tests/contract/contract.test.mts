/**
 * Cross-language contract checks for the document IR.
 *
 * The shared fixtures under `tests/fixtures/documents/` are the single source
 * of truth of the contract. This runner reads the fixture manifest and checks
 * that the TypeScript SDK:
 *
 * - accepts every valid fixture and writes it back in the canonical form,
 * - rejects every invalid fixture with the diagnostic code the manifest names,
 * - keeps the fixture set and the manifest in agreement.
 *
 * The Python runner `tests/contract/test_contract.py` reads the same manifest
 * and the same fixtures, so a drift in either SDK fails one of the two
 * contract targets.
 */

import { readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  Document,
  SCHEMA_VERSION,
  TypcastError,
} from "../../packages/typescript/lib/src/index.js";

const MANIFEST_NAME = "manifest.json";

interface ValidEntry {
  readonly file: string;
}

interface InvalidEntry {
  readonly file: string;
  readonly code: string;
}

interface Manifest {
  readonly valid: readonly ValidEntry[];
  readonly invalid: readonly InvalidEntry[];
}

function hasManifest(directory: string): boolean {
  try {
    readFileSync(join(directory, MANIFEST_NAME), "utf-8");
    return true;
  } catch {
    return false;
  }
}

function findFixtureRoot(): string {
  const candidates: string[] = [];
  const runfiles = process.env["RUNFILES_DIR"];
  const workspace = process.env["TEST_WORKSPACE"] ?? "_main";
  if (runfiles !== undefined) {
    candidates.push(join(runfiles, workspace, "tests", "fixtures", "documents"));
    candidates.push(join(runfiles, "tests", "fixtures", "documents"));
  }
  let current = dirname(fileURLToPath(import.meta.url));
  for (;;) {
    candidates.push(join(current, "tests", "fixtures", "documents"));
    const parent = dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }
  candidates.push(join(process.cwd(), "tests", "fixtures", "documents"));
  for (const candidate of candidates) {
    if (hasManifest(candidate)) {
      return candidate;
    }
  }
  throw new Error("document fixtures not found; run the target through Bazel");
}

function loadManifest(root: string): Manifest {
  const text = readFileSync(join(root, MANIFEST_NAME), "utf-8");
  const value: unknown = JSON.parse(text);
  if (typeof value !== "object" || value === null) {
    throw new Error("the fixture manifest must be a JSON object");
  }
  const record = value as Record<string, unknown>;
  return {
    valid: record["valid"] as readonly ValidEntry[],
    invalid: record["invalid"] as readonly InvalidEntry[],
  };
}

const failures: string[] = [];

function check(condition: boolean, message: string): void {
  if (!condition) {
    failures.push(message);
  }
}

function checkEqual(actual: string, expected: string, message: string): void {
  if (actual !== expected) {
    failures.push(`${message}\n--- actual ---\n${actual}\n--- expected ---\n${expected}`);
  }
}

function main(): void {
  const root = findFixtureRoot();
  const manifest = loadManifest(root);

  const listed = new Set<string>();
  for (const entry of manifest.valid) {
    listed.add(entry.file);
  }
  for (const entry of manifest.invalid) {
    listed.add(entry.file);
  }
  const present = new Set<string>(
    readdirSync(root).filter((name) => name !== MANIFEST_NAME),
  );
  check(
    listed.size === present.size &&
      [...listed].every((name) => present.has(name)),
    "the manifest and the fixture directory must list the same files",
  );

  const contract = SCHEMA_VERSION.split(".").slice(0, 2).join(".");
  for (const entry of manifest.valid) {
    const source = readFileSync(join(root, entry.file), "utf-8");
    const value = JSON.parse(source) as { readonly schemaVersion: string };
    checkEqual(
      value.schemaVersion.split(".").slice(0, 2).join("."),
      contract,
      `${entry.file}: the fixture and the SDK must use the same contract version`,
    );
    let document: Document;
    try {
      document = Document.fromJSONString(source);
    } catch (error) {
      failures.push(
        `${entry.file}: the fixture must be accepted, but it failed with ${String(error)}`,
      );
      continue;
    }
    checkEqual(
      document.toJSONString(),
      source,
      `${entry.file}: the canonical form must reproduce the fixture byte for byte`,
    );
    const again = Document.fromJSONString(document.toJSONString());
    checkEqual(
      JSON.stringify(again.toJSON()),
      JSON.stringify(document.toJSON()),
      `${entry.file}: the round trip must preserve the document`,
    );
  }

  for (const entry of manifest.invalid) {
    const source = readFileSync(join(root, entry.file), "utf-8");
    let error: unknown;
    try {
      Document.fromJSONString(source);
    } catch (caught) {
      error = caught;
    }
    if (error === undefined) {
      failures.push(`${entry.file}: the fixture must be rejected`);
      continue;
    }
    if (!(error instanceof TypcastError)) {
      failures.push(
        `${entry.file}: the failure must be a TypcastError, got ${String(error)}`,
      );
      continue;
    }
    const diagnostics = error.diagnostics;
    check(
      diagnostics.length > 0,
      `${entry.file}: the error must carry a diagnostic`,
    );
    const code = diagnostics[0]?.code;
    checkEqual(
      code ?? "",
      entry.code,
      `${entry.file}: the diagnostic code must match the manifest`,
    );
  }

  if (failures.length > 0) {
    for (const failure of failures) {
      console.error(`ERROR ${failure}`);
    }
    console.error(`failures: ${failures.length}`);
    process.exit(1);
    return;
  }
  console.log(
    `valid fixtures: ${manifest.valid.length}, invalid fixtures: ${manifest.invalid.length}`,
  );
  console.log("failures: 0");
}

main();
