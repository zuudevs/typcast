/**
 * Unit tests for the validation against the JSON Schema contract.
 *
 * The tests cover the validator of the TypeScript SDK: the keywords that the
 * schema contract uses, the diagnostics that the validator reports, and the
 * relation of the validator to the model of a document.
 */

import {
  CODE_SCHEMA_UNSUPPORTED_KEYWORD,
  CODE_SCHEMA_VIOLATION,
  Document,
  Length,
  Margin,
  Metadata,
  Page,
  Paragraph,
  Text,
  validateSchema,
} from "../lib/src/index.js";
import * as rootExports from "../lib/src/index.js";
import {
  ANNOTATION_KEYWORDS,
  ASSERTION_KEYWORDS,
  SCHEMAS,
  SCHEMA_ROOT,
  schemaKeywords,
} from "../lib/src/schema/index.js";
import type { Diagnostic } from "../lib/src/index.js";

const failures: string[] = [];

function check(condition: boolean, message: string): void {
  if (!condition) {
    failures.push(message);
  }
}

function checkEqual(actual: unknown, expected: unknown, message: string): void {
  if (actual !== expected) {
    failures.push(`${message}: expected ${String(expected)}, got ${String(actual)}`);
  }
}

function details(diagnostic: Diagnostic): Record<string, unknown> {
  return { ...diagnostic.details };
}

function document(): Document {
  const margin = new Margin(
    new Length(2, "cm"),
    new Length(2, "cm"),
    new Length(2, "cm"),
    new Length(2, "cm"),
  );
  return new Document(
    new Metadata("Title"),
    new Page("a4", "portrait", margin),
    [new Paragraph([new Text("Body")])],
  );
}

// ---------------------------------------------------------------------------
// The keywords of the schema contract
// ---------------------------------------------------------------------------

function keywordTests(): void {
  const keywords = schemaKeywords();
  check(keywords.length > 0, "the schema contract must use keywords");
  for (const keyword of keywords) {
    check(
      ANNOTATION_KEYWORDS.has(keyword) || ASSERTION_KEYWORDS.has(keyword),
      `the keyword '${keyword}' is not implemented by the validator`,
    );
  }
  check(
    Object.keys(SCHEMAS).includes(SCHEMA_ROOT),
    "the bundle must hold the schema of the document IR",
  );
  check(
    Object.keys(SCHEMAS).length === 6,
    "the bundle must hold the six files of the contract",
  );
}

// ---------------------------------------------------------------------------
// The diagnostics of the validator
// ---------------------------------------------------------------------------

function diagnosticTests(): void {
  const broken = {
    schemaVersion: "1.0.0",
    metadata: { title: "" },
    page: document().toJSON()["page"],
    contents: [{ type: "paragraph", content: [{ type: "text", value: "Body" }] }],
    modules: [],
  };
  const diagnostics = validateSchema(broken);
  checkEqual(diagnostics.length, 1, "an empty title must report one diagnostic");
  checkEqual(
    diagnostics[0]?.code,
    "TYPCAST-SCH-0001",
    "the code must be the code of the schema family",
  );
  checkEqual(
    diagnostics[0]?.path,
    "/metadata/title",
    "the path must name the title",
  );
  checkEqual(
    diagnostics[0]?.phase,
    "validation",
    "the phase must be the validation phase",
  );
  checkEqual(
    diagnostics[0]?.message,
    "'/metadata/title' must not be empty.",
    "the message must name the rule",
  );
  checkEqual(
    JSON.stringify(details(diagnostics[0] as Diagnostic)),
    JSON.stringify({ keyword: "minLength", minLength: 1 }),
    "the details must name the keyword of the rule",
  );

  const unknown = validateSchema({ ...document().toJSON(), theme: "dark" });
  checkEqual(unknown.length, 1, "an unknown field must report one diagnostic");
  checkEqual(
    unknown[0]?.path,
    "/theme",
    "the path must name the unknown field",
  );
  checkEqual(
    unknown[0]?.message,
    "'/theme' is not a known field.",
    "the message must name the rule",
  );
}

function catalogTests(): void {
  // The paper catalog holds more values than a message can list, so the
  // message names the number of the values and the details hold the list.
  const value = document().toJSON();
  const page = value["page"] as Record<string, unknown>;
  const diagnostics = validateSchema({ ...value, page: { ...page, paper: "letter" } });
  checkEqual(diagnostics.length, 1, "an unknown paper must report one diagnostic");
  checkEqual(
    diagnostics[0]?.message,
    "'/page/paper' must be one of the 107 allowed values, got 'letter'.",
    "the message must name the number of the values",
  );
  const allowed = details(diagnostics[0] as Diagnostic)["allowed"];
  check(
    Array.isArray(allowed) && allowed.length === 107,
    "the details must hold every allowed value",
  );
}

// ---------------------------------------------------------------------------
// The relation of the validator to the model of a document
// ---------------------------------------------------------------------------

function modelTests(): void {
  checkEqual(
    document().validateSchema().length,
    0,
    "a document that the model accepts must match the schema contract",
  );
  checkEqual(
    validateSchema(document().toJSON()).length,
    0,
    "the JSON value of a document must match the schema contract",
  );
  checkEqual(
    validateSchema("Title").length,
    1,
    "a value that is not an object must report one diagnostic",
  );
  checkEqual(
    validateSchema("Title")[0]?.path,
    null,
    "a value that is not an object has no path",
  );
}

// ---------------------------------------------------------------------------
// The public surface of the package root
// ---------------------------------------------------------------------------

function surfaceTests(): void {
  check(
    typeof validateSchema === "function",
    "the package root must export the schema validation",
  );
  checkEqual(
    CODE_SCHEMA_VIOLATION,
    "TYPCAST-SCH-0001",
    "the package root must export the code of a schema violation",
  );
  checkEqual(
    CODE_SCHEMA_UNSUPPORTED_KEYWORD,
    "TYPCAST-SCH-0002",
    "the package root must export the code of an unsupported keyword",
  );
  // The contract itself lives in the schema module, so that the root stays
  // small and the contract has one place.
  const root = rootExports as Record<string, unknown>;
  for (const name of [
    "SCHEMAS",
    "SCHEMA_ROOT",
    "schemaKeywords",
    "ANNOTATION_KEYWORDS",
    "ASSERTION_KEYWORDS",
  ]) {
    check(!(name in root), `the package root must not export '${name}'`);
  }
}

keywordTests();
diagnosticTests();
catalogTests();
modelTests();
surfaceTests();

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`ERROR ${failure}`);
  }
  console.error(`failures: ${failures.length}`);
  throw new Error(`${failures.length} unit test failures`);
}
console.log("failures: 0");
