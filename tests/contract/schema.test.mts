/**
 * Cross-language contract checks for the validation against the JSON Schema
 * contract.
 *
 * The shared fixtures under `tests/fixtures/schema/` are the single source of
 * truth of the contract. This runner reads the fixture manifest and checks
 * that the TypeScript SDK:
 *
 * - reports no diagnostic for every valid fixture,
 * - reports exactly the diagnostics the manifest names for every invalid
 *   fixture, in the order the manifest names them.
 *
 * The Python runner `tests/contract/test_schema.py` reads the same manifest
 * and the same fixtures, so a drift in either SDK fails one of the two
 * contract targets.
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  validateSchema,
} from "../../packages/typescript/lib/src/index.js";
import type {
  Diagnostic,
} from "../../packages/typescript/lib/src/index.js";

const MANIFEST_NAME = "manifest.json";

interface ValidEntry {
  readonly file: string;
}

interface ExpectedDiagnostic {
  readonly code: string;
  readonly path: string | null;
  readonly message: string;
  readonly details: Readonly<Record<string, unknown>>;
}

interface InvalidEntry {
  readonly file: string;
  readonly diagnostics: readonly ExpectedDiagnostic[];
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
    candidates.push(join(runfiles, workspace, "tests", "fixtures", "schema"));
    candidates.push(join(runfiles, "tests", "fixtures", "schema"));
  }
  let current = dirname(fileURLToPath(import.meta.url));
  for (;;) {
    candidates.push(join(current, "tests", "fixtures", "schema"));
    const parent = dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }
  candidates.push(join(process.cwd(), "tests", "fixtures", "schema"));
  for (const candidate of candidates) {
    if (hasManifest(candidate)) {
      return candidate;
    }
  }
  throw new Error("schema fixtures not found; run the target through Bazel");
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

/**
 * Returns whether two JSON values are the same.
 *
 * The details of a diagnostic are JSON values, and the order of the keys of
 * an object belongs to no contract.
 */
function deepEqual(actual: unknown, expected: unknown): boolean {
  if (actual === expected) {
    return true;
  }
  if (typeof actual === "number" && typeof expected === "number") {
    return (
      actual === expected ||
      (Number.isNaN(actual) && Number.isNaN(expected))
    );
  }
  if (Array.isArray(actual) || Array.isArray(expected)) {
    if (!Array.isArray(actual) || !Array.isArray(expected)) {
      return false;
    }
    if (actual.length !== expected.length) {
      return false;
    }
    return actual.every((item, index) => deepEqual(item, expected[index]));
  }
  if (
    typeof actual === "object" &&
    typeof expected === "object" &&
    actual !== null &&
    expected !== null
  ) {
    const left = actual as Record<string, unknown>;
    const right = expected as Record<string, unknown>;
    const leftKeys = Object.keys(left).sort();
    const rightKeys = Object.keys(right).sort();
    if (leftKeys.length !== rightKeys.length) {
      return false;
    }
    if (!leftKeys.every((key, index) => key === rightKeys[index])) {
      return false;
    }
    return leftKeys.every((key) => deepEqual(left[key], right[key]));
  }
  return false;
}

/** Returns the comparable fields of a diagnostic. */
function describe(diagnostic: Diagnostic): Record<string, unknown> {
  return {
    code: diagnostic.code,
    path: diagnostic.path,
    message: diagnostic.message,
    details: diagnostic.details,
  };
}

const failures: string[] = [];

function check(condition: boolean, message: string): void {
  if (!condition) {
    failures.push(message);
  }
}

function checkEqual(actual: unknown, expected: unknown, message: string): void {
  if (!deepEqual(actual, expected)) {
    failures.push(
      `${message}\n--- actual ---\n${JSON.stringify(actual)}\n--- expected ---\n${JSON.stringify(expected)}`,
    );
  }
}

function readFixture(root: string, name: string): unknown {
  const text = readFileSync(join(root, name), "utf-8");
  return JSON.parse(text);
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
  for (const name of listed) {
    if (!existsSync(join(root, name))) {
      failures.push(`${name}: the manifest names a file that does not exist`);
    }
  }

  for (const entry of manifest.valid) {
    const diagnostics = validateSchema(readFixture(root, entry.file));
    checkEqual(
      diagnostics.length,
      0,
      `${entry.file}: a valid fixture must report no diagnostic`,
    );
  }

  for (const entry of manifest.invalid) {
    const diagnostics = validateSchema(readFixture(root, entry.file));
    checkEqual(
      diagnostics.map(describe),
      entry.diagnostics,
      `${entry.file}: the diagnostics must match the manifest`,
    );
  }

  for (const section of [manifest.valid, manifest.invalid]) {
    for (const entry of section) {
      for (const diagnostic of validateSchema(readFixture(root, entry.file))) {
        checkEqual(
          diagnostic.severity,
          "error",
          `${entry.file}: the severity of a diagnostic must be an error`,
        );
        checkEqual(
          diagnostic.phase,
          "validation",
          `${entry.file}: the phase of a diagnostic must be the validation phase`,
        );
      }
    }
  }

  const multiple = manifest.invalid.find(
    (entry) => entry.file === "invalid/multiple-problems.json",
  );
  if (multiple !== undefined) {
    const diagnostics = validateSchema(readFixture(root, multiple.file));
    checkEqual(
      diagnostics.map((diagnostic) => diagnostic.path),
      multiple.diagnostics.map((diagnostic) => diagnostic.path),
      `${multiple.file}: the diagnostics must come in the order of the document`,
    );
  }

  const notAnObject = validateSchema("Title");
  checkEqual(
    notAnObject.length,
    1,
    "a value that is not an object must report one diagnostic",
  );
  if (notAnObject.length === 1) {
    checkEqual(
      notAnObject[0]!.code,
      "TYPCAST-SCH-0001",
      "the code of the diagnostic must be the code of the schema family",
    );
    checkEqual(
      notAnObject[0]!.path,
      null,
      "the path of the diagnostic must be empty",
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
