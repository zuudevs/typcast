/**
 * Cross-language contract checks for the validation engine.
 *
 * The shared fixtures under `tests/fixtures/validation/` are the single source
 * of truth of the contract. This runner reads the fixture manifest and checks
 * that the TypeScript SDK:
 *
 * - reports no diagnostic for every valid fixture,
 * - reports exactly the diagnostics the manifest names for every invalid
 *   fixture, in the order the manifest names them.
 *
 * The Python runner `tests/contract/test_validation.py` reads the same
 * manifest and the same fixtures, so a drift in either SDK fails one of the
 * two contract targets.
 */

import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  Document,
} from "../../packages/typescript/lib/src/index.js";
import type {
  Diagnostic,
  TypcastOptions,
} from "../../packages/typescript/lib/src/index.js";

const MANIFEST_NAME = "manifest.json";

interface ValidEntry {
  readonly file: string;
  readonly maxRawBytes?: number;
}

interface ExpectedDiagnostic {
  readonly code: string;
  readonly path: string | null;
  readonly message: string;
  readonly details: Readonly<Record<string, unknown>>;
}

interface InvalidEntry {
  readonly file: string;
  readonly maxRawBytes?: number;
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
    candidates.push(join(runfiles, workspace, "tests", "fixtures", "validation"));
    candidates.push(join(runfiles, "tests", "fixtures", "validation"));
  }
  let current = dirname(fileURLToPath(import.meta.url));
  for (;;) {
    candidates.push(join(current, "tests", "fixtures", "validation"));
    const parent = dirname(current);
    if (parent === current) {
      break;
    }
    current = parent;
  }
  candidates.push(join(process.cwd(), "tests", "fixtures", "validation"));
  for (const candidate of candidates) {
    if (hasManifest(candidate)) {
      return candidate;
    }
  }
  throw new Error("validation fixtures not found; run the target through Bazel");
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

/** Returns the options of a fixture, when the fixture names a limit. */
function optionsOf(entry: ValidEntry | InvalidEntry): TypcastOptions | undefined {
  if (entry.maxRawBytes === undefined) {
    return undefined;
  }
  return { maxRawBytes: entry.maxRawBytes };
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
    const source = readFileSync(join(root, entry.file), "utf-8");
    let document: Document;
    try {
      document = Document.fromJSONString(source);
    } catch (error) {
      failures.push(
        `${entry.file}: the fixture must be read, but it failed with ${String(error)}`,
      );
      continue;
    }
    const diagnostics = document.validate(optionsOf(entry));
    checkEqual(
      diagnostics.length,
      0,
      `${entry.file}: a valid fixture must report no diagnostic`,
    );
  }

  for (const entry of manifest.invalid) {
    const source = readFileSync(join(root, entry.file), "utf-8");
    let document: Document;
    try {
      document = Document.fromJSONString(source);
    } catch (error) {
      failures.push(
        `${entry.file}: the fixture must be read, but it failed with ${String(error)}`,
      );
      continue;
    }
    const diagnostics = document.validate(optionsOf(entry));
    checkEqual(
      diagnostics.map(describe),
      entry.diagnostics,
      `${entry.file}: the diagnostics must match the manifest`,
    );
  }

  const multiple = manifest.invalid.find(
    (entry) => entry.file === "invalid/multiple-problems.json",
  );
  if (multiple !== undefined) {
    const source = readFileSync(join(root, multiple.file), "utf-8");
    const document = Document.fromJSONString(source);
    const diagnostics = document.validate(optionsOf(multiple));
    checkEqual(
      diagnostics.map((diagnostic) => diagnostic.path),
      multiple.diagnostics.map((diagnostic) => diagnostic.path),
      `${multiple.file}: the diagnostics must come in the order of the document`,
    );
  }

  for (const entry of manifest.valid) {
    const source = readFileSync(join(root, entry.file), "utf-8");
    const document = Document.fromJSONString(source);
    for (const diagnostic of document.validate(optionsOf(entry))) {
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

  for (const entry of manifest.invalid) {
    const source = readFileSync(join(root, entry.file), "utf-8");
    const document = Document.fromJSONString(source);
    for (const diagnostic of document.validate(optionsOf(entry))) {
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
