/**
 * Cross-language contract checks for the document IR.
 *
 * The shared fixtures under `tests/fixtures/documents/` are the single source
 * of truth of the contract. This runner reads the fixture manifest and checks
 * that the TypeScript SDK:
 *
 * - accepts every valid fixture and writes it back in the canonical form,
 * - rejects every invalid fixture with the diagnostic the manifest names,
 * - rejects every unserializable fixture when it writes it,
 * - rejects every invalid object fixture with the diagnostic the manifest
 *   names,
 * - reads every fixture that the manifest names.
 *
 * The Python runner `tests/contract/test_contract.py` reads the same manifest
 * and the same fixtures, so a drift in either SDK fails one of the two
 * contract targets. It also checks the set of the fixture files against the
 * source tree, because the sandbox of this runner copies the fixtures into the
 * output tree of the build.
 */

import { existsSync, readFileSync } from "node:fs";
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
  readonly path: string | null;
  readonly message: string;
  readonly details: Readonly<Record<string, unknown>>;
}

interface UnserializableEntry extends InvalidEntry {}

interface InvalidObjectEntry extends InvalidEntry {
  readonly case: string;
  readonly at: string;
}

interface Manifest {
  readonly valid: readonly ValidEntry[];
  readonly invalid: readonly InvalidEntry[];
  readonly unserializable: readonly UnserializableEntry[];
  readonly invalid_object: readonly InvalidObjectEntry[];
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
    unserializable: record["unserializable"] as readonly UnserializableEntry[],
    invalid_object: record["invalid_object"] as readonly InvalidObjectEntry[],
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

/**
 * Returns whether two JSON values are the same.
 *
 * The details of a diagnostic are JSON values, and the order of the keys of
 * an object belongs to no contract. A number is the same value when it is
 * the same number, and not when it is written in another form, so a value of
 * `1e-7` and a value of `0.0000001` are the same value.
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

/**
 * Returns the details of a diagnostic without the reason of the parser.
 *
 * The reason of the parser of the runtime belongs to no expectation of the
 * contract, because the two parsers word their reason differently.
 */
function comparableDetails(
  details: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  const copy: Record<string, unknown> = { ...details };
  delete copy["reason"];
  return copy;
}

/** Checks a diagnostic against the expectation of the manifest. */
function checkDiagnostic(
  error: TypcastError,
  entry: InvalidEntry,
  context: string,
): void {
  const diagnostics = error.diagnostics;
  check(
    diagnostics.length > 0,
    `${context}: the error must carry a diagnostic`,
  );
  const diagnostic = diagnostics[0];
  checkEqual(
    diagnostic?.code ?? "",
    entry.code,
    `${context}: the diagnostic code must match the manifest`,
  );
  checkEqual(
    diagnostic?.path ?? "",
    entry.path ?? "",
    `${context}: the diagnostic path must match the manifest`,
  );
  checkEqual(
    diagnostic?.message ?? "",
    entry.message,
    `${context}: the diagnostic message must match the manifest`,
  );
  check(
    deepEqual(comparableDetails(diagnostic?.details ?? {}), entry.details),
    `${context}: the diagnostic details must match the manifest`,
  );
}

/** Returns the value that a JSON Pointer names. */
function atPath(value: unknown, path: string): unknown {
  let current = value;
  for (const token of path.split("/")) {
    if (token === "") {
      continue;
    }
    const record = current as Record<string, unknown>;
    current = record[token];
  }
  return current;
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
  for (const entry of manifest.unserializable) {
    listed.add(entry.file);
  }
  for (const entry of manifest.invalid_object) {
    listed.add(entry.file);
  }
  // The sandbox copies the fixtures into the output tree of the build, and
  // the output tree can hold a file that the current commit no longer names.
  // The runner therefore checks that every file the manifest names exists.
  // The Python runner checks the set of the files against the source tree,
  // where no stale file can hide.
  for (const name of listed) {
    if (!existsSync(join(root, name))) {
      failures.push(`${name}: the manifest names a file that does not exist`);
    }
  }

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
    check(
      deepEqual(again.toJSON(), document.toJSON()),
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
    checkDiagnostic(error, entry, entry.file);
  }

  for (const entry of manifest.unserializable) {
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
    let error: unknown;
    try {
      document.toJSONString();
    } catch (caught) {
      error = caught;
    }
    if (error === undefined) {
      failures.push(`${entry.file}: the fixture must not be serializable`);
      continue;
    }
    if (!(error instanceof TypcastError)) {
      failures.push(
        `${entry.file}: the failure must be a TypcastError, got ${String(error)}`,
      );
      continue;
    }
    checkDiagnostic(error, entry, entry.file);
  }

  for (const entry of manifest.invalid_object) {
    const source = readFileSync(join(root, entry.file), "utf-8");
    const fixture = JSON.parse(source) as {
      readonly document: Record<string, unknown>;
    };
    const target = atPath(fixture.document, entry.at) as Record<string, unknown>;
    // The grammar of JSON holds no key that is not a string. A symbol key is
    // the only key of a JavaScript object that is not a string, and the
    // reader must reject it as it rejects another key in the Python SDK.
    Object.defineProperty(target, Symbol("key"), {
      value: target["title"],
      enumerable: true,
      configurable: true,
      writable: true,
    });
    let error: unknown;
    try {
      Document.fromJSON(fixture.document);
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
    checkDiagnostic(error, entry, entry.file);
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
    `valid fixtures: ${manifest.valid.length}, invalid fixtures: ${manifest.invalid.length}, ` +
      `unserializable fixtures: ${manifest.unserializable.length}, ` +
      `invalid object fixtures: ${manifest.invalid_object.length}`,
  );
  console.log("failures: 0");
}

main();
