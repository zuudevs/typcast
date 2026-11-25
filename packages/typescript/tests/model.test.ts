/**
 * Unit tests for the immutable document model of the TypeScript SDK.
 *
 * The tests cover the model-level invariants of `docs/specifications/document-ir.md`:
 * the immutability of the model, the checks of the constructors, the canonical
 * JSON form, and the behavior of the reader.
 */

import {
  Bold,
  Document,
  Heading,
  Image,
  Italic,
  Length,
  LineBreak,
  Link,
  ListBlock,
  Margin,
  Metadata,
  Module,
  Monospace,
  Page,
  PageBreak,
  Paragraph,
  RawBlock,
  RawSpan,
  Table,
  TableColumn,
  Text,
  TypcastError,
  ValidationError,
} from "../lib/src/index.js";
import type { Block } from "../lib/src/index.js";

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

function margin(value = 2, unit = "cm"): Margin {
  return new Margin(
    new Length(value, unit as "cm"),
    new Length(value, unit as "cm"),
    new Length(value, unit as "cm"),
    new Length(value, unit as "cm"),
  );
}

function buildDocument(
  metadata: Metadata = new Metadata("Title"),
  page: Page = new Page("a4", "portrait", margin()),
  contents: readonly Block[] = [new Paragraph([new Text("Body")])],
  modules: readonly Module[] = [],
): Document {
  return new Document(metadata, page, contents, modules);
}

function expectCode(code: string, factory: () => unknown, message: string): void {
  try {
    factory();
  } catch (error) {
    if (!(error instanceof TypcastError)) {
      failures.push(`${message}: the failure must be a TypcastError`);
      return;
    }
    const actual = error.diagnostics[0]?.code;
    if (actual !== code) {
      failures.push(`${message}: expected ${code}, got ${String(actual)}`);
    }
    return;
  }
  failures.push(`${message}: the call must fail`);
}

function expectPath(
  path: string,
  factory: () => unknown,
  message: string,
): void {
  try {
    factory();
  } catch (error) {
    if (!(error instanceof ValidationError)) {
      failures.push(`${message}: the failure must be a ValidationError`);
      return;
    }
    const actual = error.diagnostics[0]?.path;
    if (actual !== path) {
      failures.push(`${message}: expected ${path}, got ${String(actual)}`);
    }
    return;
  }
  failures.push(`${message}: the call must fail`);
}

// ---------------------------------------------------------------------------
// Immutability
// ---------------------------------------------------------------------------

function immutabilityTests(): void {
  const paragraph = new Paragraph([new Text("Body")]);
  check(Object.isFrozen(paragraph), "a paragraph must be frozen");
  check(Object.isFrozen(paragraph.content), "a span array must be frozen");
  check(
    Object.isFrozen(paragraph.content[0]),
    "a span must be frozen",
  );
  check(
    Object.isFrozen(new Length(2, "cm")),
    "a length must be frozen",
  );
  check(
    Object.isFrozen(new Margin(margin().top, margin().right, margin().bottom, margin().left)),
    "a margin must be frozen",
  );

  const content: Text[] = [new Text("Body")];
  const copied = new Paragraph(content);
  content.push(new Text("Added later"));
  checkEqual(copied.content.length, 1, "the constructor must copy the array");

  const contents: Block[] = [new Paragraph([new Text("Body")])];
  const built = buildDocument(undefined, undefined, contents);
  contents.push(new PageBreak());
  checkEqual(built.contents.length, 1, "the document must copy the contents");

  const table = new Table(
    [new TableColumn([new Text("Header")], "left")],
    [[[new Text("Cell")]]],
  );
  check(Object.isFrozen(table.columns), "the columns must be frozen");
  check(Object.isFrozen(table.rows), "the rows must be frozen");
  check(Object.isFrozen(table.rows[0]), "a row must be frozen");
  check(Object.isFrozen(table.rows[0]?.[0]), "a cell must be frozen");

  const items = ["currency"];
  const module = new Module("modules/format.typ", null, items);
  items.push("percent");
  checkEqual(module.items?.length, 1, "the module must copy the items");
}

// ---------------------------------------------------------------------------
// Constructor validation
// ---------------------------------------------------------------------------

function constructorTests(): void {
  expectCode(
    "TYPCAST-VAL-0006",
    () => new Metadata(""),
    "an empty title must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0011",
    () => new Metadata("Title", null, "2026-02-30"),
    "an impossible date must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0011",
    () => new Metadata("Title", null, "0000-01-01"),
    "the year zero must be rejected",
  );
  checkEqual(
    new Metadata("Title", null, "0001-01-01").date,
    "0001-01-01",
    "a date below the year 100 must be accepted",
  );
  checkEqual(
    new Metadata("Title", null, "0099-12-31").date,
    "0099-12-31",
    "the last date below the year 100 must be accepted",
  );
  expectCode(
    "TYPCAST-VAL-0011",
    () => new Metadata("Title", null, "1900-02-29"),
    "a day of a century that is not a leap year must be rejected",
  );
  checkEqual(
    new Metadata("Title", null, "2000-02-29").date,
    "2000-02-29",
    "a day of a leap year must be accepted",
  );
  expectCode(
    "TYPCAST-VAL-0011",
    () => new Metadata("Title", null, "\u0662\u0660\u0662\u0666-01-01"),
    "a date with Unicode digits must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0011",
    () => new Metadata("Title", null, "2026-01-01\n"),
    "a date with a trailing newline must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0013",
    () => new Metadata("T".repeat(513)),
    "a title of more than 512 code points must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0013",
    () => new Metadata("Title", "A".repeat(513)),
    "an author of more than 512 code points must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0013",
    () => new Metadata("\u{1f600}".repeat(513)),
    "more than 512 characters outside the basic multilingual plane must be rejected",
  );
  checkEqual(
    new Metadata("T".repeat(512)).title.length,
    512,
    "a title of 512 code points must be accepted",
  );
  checkEqual(
    new Metadata("\u{1f600}".repeat(512)).title.length,
    1024,
    "a character outside the basic multilingual plane must count as one code point",
  );
  expectCode(
    "TYPCAST-VAL-0003",
    () => new Page("a4", "diagonal" as "portrait", margin()),
    "an unknown orientation must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0004",
    () => new Length(-1, "cm"),
    "a negative length must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0004",
    () => new Length(1, "fr" as "cm"),
    "an unknown unit must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0004",
    () => new Length(Number.NaN, "cm"),
    "a non-finite length must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0005",
    () => new Heading(7, [new Text("Heading")]),
    "an invalid heading level must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0001",
    () => new Heading(1.5, [new Text("Heading")]),
    "a fractional heading level must be rejected",
  );
  checkEqual(
    new Heading(1.0, [new Text("Heading")]).level,
    1,
    "an integer valued float heading level must be accepted",
  );
  checkEqual(
    new Length(9007199254740993, "cm").value,
    9007199254740992,
    "a length that the number domain cannot hold must be narrowed",
  );
  expectCode(
    "TYPCAST-VAL-0004",
    () => new Length(Number.POSITIVE_INFINITY, "cm"),
    "a length that overflows the number domain must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0006",
    () => new Paragraph([]),
    "empty content must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0006",
    () => new Text(""),
    "empty text must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0008",
    () => new Module("modules/report.typ", "1report"),
    "an invalid module alias must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0008",
    () => new Module("modules/report.typ", "report\n"),
    "a module alias with a trailing newline must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0008",
    () => new Module("modules/report.typ", null, ["summary\n"]),
    "a module item with a trailing newline must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0008",
    () => new Module("modules/report.typ", { not: "a string" } as unknown as string),
    "a module alias of an unknown type must be rejected",
  );
  try {
    new Module("modules/report.typ", { not: "a string" } as unknown as string);
  } catch (error) {
    if (error instanceof ValidationError) {
      const text = JSON.stringify(error.diagnostics[0]?.details);
      check(
        text.includes('"value":"object"'),
        "the details of a diagnostic must be JSON-serializable",
      );
    }
  }
  try {
    new Module("modules/report.typ", Number.NaN as unknown as string);
  } catch (error) {
    if (error instanceof ValidationError) {
      const text = JSON.stringify(error.diagnostics[0]?.details);
      check(
        text.includes('"value":"NaN"'),
        "the details of a diagnostic must hold no non-finite number",
      );
    }
  }
  expectCode(
    "TYPCAST-VAL-0009",
    () => new Module("modules/report.typ", "report", ["currency"]),
    "an alias and items must be exclusive",
  );
  expectCode(
    "TYPCAST-VAL-0006",
    () => new Module("modules/report.typ", null, []),
    "empty module items must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0006",
    () => buildDocument(undefined, undefined, []),
    "empty document contents must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0003",
    () => new RawBlock("typst" as "markup", "value"),
    "an unknown raw format must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0006",
    () => new RawBlock("markup", ""),
    "an empty raw value must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0003",
    () => new TableColumn([new Text("Header")], "justify" as "left"),
    "an unknown alignment must be rejected",
  );
  expectCode(
    "TYPCAST-VAL-0001",
    () => new Paragraph([new Text("Body"), "not a span" as unknown as Text]),
    "a wrong element type must be rejected",
  );
  expectCode(
    "TYPCAST-IR-0002",
    () => new Document(new Metadata("Title"), new Page("a4", "portrait", margin()), [new Paragraph([new Text("Body")])], [], "2.0.0"),
    "an unsupported schema version must be rejected",
  );
  expectCode(
    "TYPCAST-IR-0002",
    () => new Document(new Metadata("Title"), new Page("a4", "portrait", margin()), [new Paragraph([new Text("Body")])], [], "\u0661.0.0"),
    "a schema version with Unicode digits must be rejected",
  );
  expectCode(
    "TYPCAST-IR-0002",
    () => new Document(new Metadata("Title"), new Page("a4", "portrait", margin()), [new Paragraph([new Text("Body")])], [], "1.0.0\n"),
    "a schema version with a trailing newline must be rejected",
  );
}

// ---------------------------------------------------------------------------
// Serialization
// ---------------------------------------------------------------------------

function serializationTests(): void {
  const text = buildDocument().toJSONString();
  check(text.endsWith("\n"), "the output must end with a newline");
  check(
    text.includes('\n  "schemaVersion": "1.0.0",\n'),
    "the output must use two-space indentation",
  );

  const value = buildDocument().toJSON();
  checkEqual(
    JSON.stringify(Object.keys(value)),
    JSON.stringify(["schemaVersion", "metadata", "page", "contents", "modules"]),
    "the fields must follow the order of the contract",
  );
  checkEqual(
    JSON.stringify(Object.keys(value["metadata"] as object)),
    JSON.stringify(["title"]),
    "an absent optional field must be omitted",
  );

  const integer = buildDocument(
    undefined,
    new Page("a4", "portrait", margin(2.0)),
  );
  check(
    integer.toJSONString().includes('"value": 2,'),
    "an integer-valued float must be written without a decimal point",
  );

  const fractional = buildDocument(
    undefined,
    new Page("a4", "portrait", margin(2.5)),
  );
  check(
    fractional.toJSONString().includes('"value": 2.5,'),
    "a fractional length must keep its shortest form",
  );

  const large = buildDocument(
    undefined,
    new Page("a4", "portrait", margin(9007199254740992)),
  );
  check(
    large.toJSONString().includes('"value": 9007199254740992,'),
    "a large number must be written in the number domain of the contract",
  );

  const unicode = buildDocument(new Metadata("보고서")).toJSONString();
  check(unicode.includes("보고서"), "the output must preserve Unicode");
  check(!unicode.includes("\\u"), "the output must not escape Unicode");

  expectCode(
    "TYPCAST-IR-0003",
    () => buildDocument(new Metadata("Title\uD800")).toJSONString(),
    "a lone surrogate must be rejected",
  );
  expectCode(
    "TYPCAST-IR-0003",
    () => buildDocument(new Metadata("Title\uDC00")).toJSONString(),
    "a lone trailing surrogate must be rejected",
  );

  const built = buildDocument(
    undefined,
    undefined,
    [
      new Heading(1, [new Text("Heading")]),
      new Paragraph([
        new Text("Text"),
        new Bold([new Text("Bold")]),
        new Italic([new Text("Italic")]),
        new Monospace([new Text("Monospace")]),
        new Link("https://example.com", [new Text("Link")]),
        new LineBreak(),
        new RawSpan("math", "x^2"),
      ]),
      new ListBlock(true, [[new Text("Item")]]),
      new Table(
        [new TableColumn([new Text("Header")], "left")],
        [[[new Text("Cell")]]],
      ),
      new Image("figures/logo.png", "Logo"),
      new PageBreak(),
      new RawBlock("markup", "#text()"),
    ],
    [new Module("modules/report.typ", "report")],
  );
  const serialized = built.toJSON();
  const blocks = serialized["contents"] as { type: string; content?: { type: string }[] }[];
  checkEqual(
    JSON.stringify(blocks.map((block) => block.type)),
    JSON.stringify([
      "heading",
      "paragraph",
      "list",
      "table",
      "image",
      "pageBreak",
      "raw",
    ]),
    "every block type must be serialized",
  );
  const spans = blocks[1]?.content ?? [];
  checkEqual(
    JSON.stringify(spans.map((span) => span.type)),
    JSON.stringify([
      "text",
      "bold",
      "italic",
      "monospace",
      "link",
      "lineBreak",
      "raw",
    ]),
    "every span type must be serialized",
  );
}

// ---------------------------------------------------------------------------
// Deserialization
// ---------------------------------------------------------------------------

function deserializationTests(): void {
  expectCode(
    "TYPCAST-IR-0001",
    () => Document.fromJSONString("{"),
    "malformed JSON must be rejected",
  );
  expectCode(
    "TYPCAST-IR-0004",
    () => Document.fromJSONString("[]"),
    "a non-object root must be rejected",
  );

  const unknownRoot = buildDocument().toJSON() as Record<string, unknown>;
  unknownRoot["theme"] = "dark";
  expectCode(
    "TYPCAST-VAL-0002",
    () => Document.fromJSON(unknownRoot),
    "an unknown root field must be rejected",
  );

  const missing = buildDocument().toJSON() as Record<string, unknown>;
  delete missing["metadata"];
  expectCode(
    "TYPCAST-VAL-0001",
    () => Document.fromJSON(missing),
    "a missing required field must be rejected",
  );

  const unknownNode = buildDocument().toJSON() as Record<string, unknown>;
  (unknownNode["contents"] as Record<string, unknown>[])[0]!["style"] = "lead";
  expectCode(
    "TYPCAST-VAL-0002",
    () => Document.fromJSON(unknownNode),
    "an unknown node field must be rejected",
  );

  const unknownType = buildDocument().toJSON() as Record<string, unknown>;
  (unknownType["contents"] as Record<string, unknown>[])[0]!["type"] = "quote";
  expectCode(
    "TYPCAST-VAL-0003",
    () => Document.fromJSON(unknownType),
    "an unknown discriminator must be rejected",
  );

  const inheritedType = buildDocument().toJSON() as Record<string, unknown>;
  (inheritedType["contents"] as Record<string, unknown>[])[0]!["type"] =
    "constructor";
  expectCode(
    "TYPCAST-VAL-0003",
    () => Document.fromJSON(inheritedType),
    "an inherited key must not be a block discriminator",
  );

  const inheritedSpanType = buildDocument().toJSON() as Record<string, unknown>;
  (
    (inheritedSpanType["contents"] as Record<string, unknown>[])[0]![
      "content"
    ] as Record<string, unknown>[]
  )[0]!["type"] = "toString";
  expectCode(
    "TYPCAST-VAL-0003",
    () => Document.fromJSON(inheritedSpanType),
    "an inherited key must not be a span discriminator",
  );

  const unsupported = buildDocument().toJSON() as Record<string, unknown>;
  unsupported["schemaVersion"] = "2.0.0";
  expectCode(
    "TYPCAST-IR-0002",
    () => Document.fromJSON(unsupported),
    "an unsupported version must be rejected",
  );

  const patch = buildDocument().toJSON() as Record<string, unknown>;
  patch["schemaVersion"] = "1.0.7";
  checkEqual(
    Document.fromJSON(patch).schemaVersion,
    "1.0.7",
    "a supported patch version must be accepted",
  );

  const unicodeDigits = buildDocument().toJSON() as Record<string, unknown>;
  unicodeDigits["schemaVersion"] = "\u0661.0.0";
  expectCode(
    "TYPCAST-IR-0002",
    () => Document.fromJSON(unicodeDigits),
    "a version with Unicode digits must be rejected",
  );

  const trailingNewline = buildDocument().toJSON() as Record<string, unknown>;
  trailingNewline["schemaVersion"] = "1.0.0\n";
  expectCode(
    "TYPCAST-IR-0002",
    () => Document.fromJSON(trailingNewline),
    "a version with a trailing newline must be rejected",
  );

  const floatLevel = buildDocument().toJSON() as Record<string, unknown>;
  floatLevel["contents"] = [
    { type: "heading", level: 1.0, content: [{ type: "text", value: "H" }] },
  ];
  const parsedLevel = Document.fromJSON(floatLevel).contents[0] as Heading;
  checkEqual(
    parsedLevel.level,
    1,
    "an integer valued float level must be accepted",
  );

  const overflow = buildDocument().toJSON() as Record<string, unknown>;
  const page = overflow["page"] as Record<string, unknown>;
  const margins = page["margin"] as Record<string, unknown>;
  const top = margins["top"] as Record<string, unknown>;
  top["value"] = 1e400;
  expectCode(
    "TYPCAST-IR-0004",
    () => Document.fromJSON(overflow),
    "a number that overflows the number domain must be rejected",
  );

  const nested = buildDocument().toJSON() as Record<string, unknown>;
  const nestedPage = nested["page"] as Record<string, unknown>;
  const nestedMargins = nestedPage["margin"] as Record<string, unknown>;
  (nestedMargins["top"] as Record<string, unknown>)["value"] = -1;
  expectPath(
    "/page/margin/top/value",
    () => Document.fromJSON(nested),
    "the path of a nested value must not be prefixed twice",
  );

  const nestedOptional = buildDocument().toJSON() as Record<string, unknown>;
  nestedOptional["contents"] = [
    {
      type: "image",
      path: "figure.png",
      alt: "Figure",
      width: { value: -2, unit: "cm" },
    },
  ];
  expectPath(
    "/contents/0/width/value",
    () => Document.fromJSON(nestedOptional),
    "the path of a nested optional value must not be prefixed twice",
  );

  const escaped = buildDocument().toJSON() as Record<string, unknown>;
  escaped["bad/name"] = 1;
  expectPath(
    "/bad~1name",
    () => Document.fromJSON(escaped),
    "an unknown field must be reported with an escaped pointer",
  );

  const escapedTilde = buildDocument().toJSON() as Record<string, unknown>;
  escapedTilde["a~b"] = 1;
  expectPath(
    "/a~0b",
    () => Document.fromJSON(escapedTilde),
    "an unknown field with a tilde must be escaped",
  );

  const withoutModules = buildDocument().toJSON() as Record<string, unknown>;
  delete withoutModules["modules"];
  checkEqual(
    Document.fromJSON(withoutModules).modules.length,
    0,
    "an absent modules field must default to an empty list",
  );

  try {
    Document.fromJSON(unknownNode);
  } catch (error) {
    if (error instanceof ValidationError) {
      checkEqual(
        error.diagnostics[0]?.path,
        "/contents/0/style",
        "the diagnostic path must point at the failing node",
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Round trip
// ---------------------------------------------------------------------------

function roundTripTests(): void {
  const text = buildDocument().toJSONString();
  checkEqual(
    Document.fromJSONString(text).toJSONString(),
    text,
    "the round trip must be stable",
  );

  const built = buildDocument(
    new Metadata("Title", "Author", "2026-11-24"),
    undefined,
    undefined,
    [new Module("modules/report.typ", null, ["currency"])],
  );
  const parsed = Document.fromJSONString(built.toJSONString());
  checkEqual(
    JSON.stringify(parsed.toJSON()),
    JSON.stringify(built.toJSON()),
    "the round trip must preserve the document",
  );
  checkEqual(parsed.metadata.author, "Author", "the author must survive");
  checkEqual(
    parsed.modules[0]?.items?.length,
    1,
    "the module items must survive",
  );
}

immutabilityTests();
constructorTests();
serializationTests();
deserializationTests();
roundTripTests();

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`ERROR ${failure}`);
  }
  console.error(`failures: ${failures.length}`);
  throw new Error(`${failures.length} unit test failures`);
}
console.log("failures: 0");
