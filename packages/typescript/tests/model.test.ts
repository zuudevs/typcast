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
  PAPER_VARIANTS,
  Page,
  PageBreak,
  Paragraph,
  RawBlock,
  RawSpan,
  SCHEMA_VERSION,
  Table,
  TableColumn,
  Text,
  TypcastError,
  ValidationError,
  VERSION,
} from "../lib/src/index.js";
import type { Block } from "../lib/src/index.js";
import { assertEncodable } from "../lib/src/canonical.js";

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

function expectMessage(
  expected: string,
  factory: () => unknown,
  message: string,
): void {
  try {
    factory();
  } catch (error) {
    if (!(error instanceof TypcastError)) {
      failures.push(`${message}: the failure must be a TypcastError`);
      return;
    }
    const actual = error.diagnostics[0]?.message;
    if (actual !== expected) {
      failures.push(`${message}: expected ${expected}, got ${String(actual)}`);
    }
    return;
  }
  failures.push(`${message}: the call must fail`);
}

/**
 * Returns the details of a diagnostic with the keys sorted.
 *
 * The order of the keys of a JSON object belongs to no contract, so the two
 * SDKs may write the same details in another order.
 */
function sortedDetails(
  details: Readonly<Record<string, unknown>>,
): Record<string, unknown> {
  const sorted: Record<string, unknown> = {};
  for (const key of Object.keys(details).sort()) {
    sorted[key] = details[key];
  }
  return sorted;
}

/** Checks a diagnostic against an expectation. */
function expectDiagnostic(
  code: string,
  path: string | null,
  message: string,
  details: Readonly<Record<string, unknown>>,
  factory: () => unknown,
  context: string,
): void {
  try {
    factory();
  } catch (error) {
    if (!(error instanceof TypcastError)) {
      failures.push(`${context}: the failure must be a TypcastError`);
      return;
    }
    const diagnostic = error.diagnostics[0];
    checkEqual(diagnostic?.code ?? "", code, `${context}: the code must match`);
    checkEqual(
      diagnostic?.path ?? "",
      path ?? "",
      `${context}: the path must match`,
    );
    checkEqual(
      diagnostic?.message ?? "",
      message,
      `${context}: the message must match`,
    );
    check(
      JSON.stringify(sortedDetails(diagnostic?.details ?? {})) ===
        JSON.stringify(sortedDetails(details)),
      `${context}: the details must match`,
    );
    return;
  }
  failures.push(`${context}: the call must fail`);
}

// ---------------------------------------------------------------------------
// Rejected values
// ---------------------------------------------------------------------------

function rejectedValueTests(): void {
  // The Python SDK writes the same messages, and the shared fixtures of the
  // contract name them.
  expectDiagnostic(
    "TYPCAST-VAL-0003",
    "/orientation",
    "'/orientation' must be one of landscape, portrait, got 'di\\'\\\"\\\\'.",
    { allowed: ["landscape", "portrait"], value: "di'\"\\" },
    () => new Page("a4", "di'\"\\" as "portrait", margin()),
    "a rejected value must escape the quotes and the backslash",
  );
  expectDiagnostic(
    "TYPCAST-VAL-0003",
    "/orientation",
    "'/orientation' must be one of landscape, portrait, got 'di\\n\\r\\t'.",
    { allowed: ["landscape", "portrait"], value: "di\n\r\t" },
    () => new Page("a4", "di\n\r\t" as "portrait", margin()),
    "a rejected value must escape the control characters",
  );
  expectDiagnostic(
    "TYPCAST-VAL-0003",
    "/orientation",
    "'/orientation' must be one of landscape, portrait, got 'di\\u0000\\u001f\\u007f'.",
    { allowed: ["landscape", "portrait"], value: "di\u0000\u001f\u007f" },
    () => new Page("a4", "di\u0000\u001f\u007f" as "portrait", margin()),
    "a rejected value must escape the other control characters",
  );
  expectDiagnostic(
    "TYPCAST-VAL-0011",
    "/date",
    "'/date' must be a calendar date in YYYY-MM-DD form, got '2026-01-01\\'\\\"\\\\'.",
    { value: "2026-01-01'\"\\" },
    () => new Metadata("Title", null, "2026-01-01'\"\\"),
    "a rejected date must escape the value",
  );
  expectDiagnostic(
    "TYPCAST-VAL-0011",
    "/date",
    "'/date' is not a calendar date: '2026-02-30'.",
    { value: "2026-02-30" },
    () => new Metadata("Title", null, "2026-02-30"),
    "an impossible date must name the value",
  );
  expectDiagnostic(
    "TYPCAST-VAL-0011",
    "/date",
    "'/date' must be a calendar date in YYYY-MM-DD form, got '2026-01-01\\n'.",
    { value: "2026-01-01\n" },
    () => new Metadata("Title", null, "2026-01-01\n"),
    "a date with a trailing newline must escape the value",
  );
  expectDiagnostic(
    "TYPCAST-IR-0002",
    "/schemaVersion",
    "'schemaVersion' must be a semantic version, got '1.0.0\\'\\\"\\\\'.",
    { value: "1.0.0'\"\\" },
    () => new Document(new Metadata("Title"), new Page("a4", "portrait", margin()), [new Paragraph([new Text("Body")])], [], "1.0.0'\"\\"),
    "a rejected version must escape the value",
  );
  expectDiagnostic(
    "TYPCAST-IR-0002",
    "/schemaVersion",
    "'schemaVersion' '2.0.0' is not supported; this SDK reads 1.0.x.",
    { value: "2.0.0", supportedMajor: 1, supportedMinor: 0 },
    () => new Document(new Metadata("Title"), new Page("a4", "portrait", margin()), [new Paragraph([new Text("Body")])], [], "2.0.0"),
    "an unsupported version must name the value",
  );

  // The length of the shown value is counted in code points, as the Python
  // SDK counts it.
  try {
    new Page("a4", "😀".repeat(100) as "portrait", margin());
    failures.push("a long enum value must be rejected");
  } catch (error) {
    if (error instanceof TypcastError) {
      const message = error.diagnostics[0]?.message ?? "";
      check(
        message.includes("😀".repeat(64)),
        "a shortened value must count code points",
      );
      check(
        !message.includes("😀".repeat(65)),
        "a shortened value must hold at most 64 code points",
      );
    }
  }
}

// ---------------------------------------------------------------------------
// Encodability
// ---------------------------------------------------------------------------

function encodabilityTests(): void {
  expectDiagnostic(
    "TYPCAST-IR-0003",
    "/metadata/title",
    "'/metadata/title' holds a surrogate that UTF-8 cannot encode.",
    {},
    () => buildDocument(new Metadata("Title\uD800")).toJSONString(),
    "a lone surrogate must be rejected",
  );
  expectDiagnostic(
    "TYPCAST-IR-0003",
    "/metadata/title",
    "'/metadata/title' holds a surrogate that UTF-8 cannot encode.",
    {},
    () => buildDocument(new Metadata("Title\uDC00")).toJSONString(),
    "a lone trailing surrogate must be rejected",
  );
  expectDiagnostic(
    "TYPCAST-IR-0003",
    "/contents/0/content/0/value",
    "'/contents/0/content/0/value' holds a surrogate that UTF-8 cannot encode.",
    {},
    () =>
      buildDocument(
        undefined,
        undefined,
        [new Paragraph([new Text("Body\uD800")])],
      ).toJSONString(),
    "a surrogate in a nested string must be rejected",
  );
  expectCode(
    "TYPCAST-IR-0003",
    () => assertEncodable({ "a\uD800b": "value" }, ""),
    "a surrogate in the name of a property must be rejected",
  );
  check(
    buildDocument(new Metadata("Title😀")).toJSONString().includes("😀"),
    "a character outside the basic multilingual plane must be accepted",
  );
  expectCode(
    "TYPCAST-IR-0003",
    () => buildDocument(new Metadata("Title\uD800")).toJSON(),
    "the JSON value of a document must hold no surrogate",
  );
}

// ---------------------------------------------------------------------------
// Number domain
// ---------------------------------------------------------------------------

function numberDomainTests(): void {
  // The numbers of the IR live in the binary64 domain of ECMAScript, so a
  // value that the domain cannot hold exactly is narrowed to the nearest
  // representable value.
  const length = new Length(9007199254740993, "cm");
  checkEqual(
    length.value,
    9007199254740992,
    "a length that the number domain cannot hold must be narrowed",
  );
  const built = buildDocument(
    undefined,
    new Page("a4", "portrait", margin(9007199254740993)),
  );
  const text = built.toJSONString();
  check(
    text.includes('"value": 9007199254740992,'),
    "the narrowed length must be written exactly",
  );
  check(
    JSON.stringify(Document.fromJSONString(text).toJSON()) ===
      JSON.stringify(built.toJSON()),
    "the narrowed length must survive the round trip",
  );

  expectMessage(
    "'/value' must not be negative, got -1e-7.",
    () => new Length(-1e-7, "cm"),
    "a negative length must show the canonical number",
  );
  check(
    buildDocument(
      undefined,
      new Page("a4", "portrait", margin(-0)),
    ).toJSONString().includes('"value": 0,'),
    "a negative zero must be written as zero",
  );
  check(
    buildDocument(
      undefined,
      new Page("a4", "portrait", margin(1e-7)),
    ).toJSONString().includes('"value": 1e-7,'),
    "a small number must be written in the exponential form",
  );
  check(
    buildDocument(
      undefined,
      new Page("a4", "portrait", margin(1e21)),
    ).toJSONString().includes('"value": 1e+21,'),
    "a large number must be written in the exponential form",
  );
  check(
    buildDocument(
      undefined,
      new Page("a4", "portrait", margin(5e-324)),
    ).toJSONString().includes('"value": 5e-324,'),
    "the smallest number of the domain must be written exactly",
  );
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
  expectDiagnostic(
    "TYPCAST-VAL-0004",
    "/value",
    "'/value' must be a finite number.",
    { value: "-Infinity" },
    () => new Length(Number.NEGATIVE_INFINITY, "cm"),
    "a length that overflows the number domain must keep its sign",
  );
  expectCode(
    "TYPCAST-VAL-0004",
    () => new Image("figures/logo.png", "Logo", null, new Length(0, "cm")),
    "an image width of zero must be rejected",
  );
  checkEqual(
    new Length(0, "cm").value,
    0,
    "a zero length of a margin must be accepted",
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
    () => new Module("modules/report.typ", null, [1 as unknown as string]),
    "a module item of another type must be rejected",
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
  try {
    new Module(
      "modules/report.typ",
      Number.POSITIVE_INFINITY as unknown as string,
    );
  } catch (error) {
    if (error instanceof ValidationError) {
      const text = JSON.stringify(error.diagnostics[0]?.details);
      check(
        text.includes('"value":"Infinity"'),
        "the details of a diagnostic must hold no non-finite number",
      );
    }
  }
  try {
    new Module("modules/report.typ", `1${"a".repeat(200)}`);
  } catch (error) {
    if (error instanceof ValidationError) {
      const message = error.diagnostics[0]?.message ?? "";
      check(
        message.length < 200 && message.includes("…"),
        "a long identifier must be shortened in the message",
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
// Diagnostic messages
// ---------------------------------------------------------------------------

function diagnosticMessageTests(): void {
  // The Python SDK writes the same messages, and the shared fixtures of the
  // contract name them.
  expectMessage(
    "'/orientation' must be one of landscape, portrait, got 'diagonal'.",
    () => new Page("a4", "diagonal" as "portrait", margin()),
    "an enum message must name the rejected value",
  );
  expectMessage(
    "'/content' must be an array of Span values.",
    () => new Paragraph("Body" as unknown as readonly Text[]),
    "a collection message must name the array",
  );
  expectMessage(
    "'/content/0' must be a Span.",
    () => new Paragraph([1 as unknown as Text]),
    "an element message must name the type",
  );
  expectMessage(
    "'/items/0' must be an array of Span values.",
    () => new ListBlock(true, [1 as unknown as readonly Text[]]),
    "a nested collection message must name the arrays",
  );

  // The message shows at most 64 characters of the rejected value.
  try {
    new Page("a4", "d".repeat(200) as "portrait", margin());
    failures.push("a long enum value must be rejected");
  } catch (error) {
    if (error instanceof TypcastError) {
      const message = error.diagnostics[0]?.message ?? "";
      check(message.includes("…"), "a long enum value must be shortened");
      check(message.length < 200, "a short message must stay short");
    }
  }

  // The length of the shown value is counted in code points, as the Python
  // SDK counts it.
  try {
    new Page("a4", "😀".repeat(200) as "portrait", margin());
    failures.push("a long enum value must be rejected");
  } catch (error) {
    if (error instanceof TypcastError) {
      const message = error.diagnostics[0]?.message ?? "";
      check(
        message.includes("😀".repeat(64)),
        "a shortened value must count code points",
      );
      check(
        !message.includes("😀".repeat(65)),
        "a shortened value must hold at most 64 code points",
      );
    }
  }

  // The reason of the parser belongs to the details, so that the message is
  // the same in both SDKs.
  try {
    Document.fromJSONString("{");
    failures.push("malformed JSON must be rejected");
  } catch (error) {
    if (error instanceof TypcastError) {
      checkEqual(
        error.diagnostics[0]?.message,
        "The source is not valid JSON.",
        "a malformed JSON message must not name the parser",
      );
      check(
        error.diagnostics[0]?.details?.["reason"] !== undefined,
        "the details of a malformed JSON diagnostic must hold the reason",
      );
    }
  }

  // The details of a diagnostic name the same things in both SDKs.
  try {
    new Metadata("Title", null, "2026-02-30");
    failures.push("an impossible date must be rejected");
  } catch (error) {
    if (error instanceof TypcastError) {
      checkEqual(
        JSON.stringify(error.diagnostics[0]?.details),
        JSON.stringify({ value: "2026-02-30" }),
        "the details of an invalid date must hold no cause",
      );
    }
  }
  try {
    new Paragraph("Body" as unknown as readonly Text[]);
    failures.push("a wrong collection must be rejected");
  } catch (error) {
    if (error instanceof TypcastError) {
      checkEqual(
        JSON.stringify(error.diagnostics[0]?.details),
        JSON.stringify({ expected: "Span" }),
        "the details of a collection error must name the element",
      );
    }
  }
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

  const prototypeType = buildDocument().toJSON() as Record<string, unknown>;
  const prototypeBlock = Object.create({
    type: "pageBreak",
  }) as Record<string, unknown>;
  (prototypeType["contents"] as unknown[])[0] = prototypeBlock;
  expectCode(
    "TYPCAST-VAL-0003",
    () => Document.fromJSON(prototypeType),
    "a discriminator of the prototype must not be a block discriminator",
  );

  const longComponent = buildDocument().toJSON() as Record<string, unknown>;
  longComponent["schemaVersion"] = `${"1".repeat(5000)}.0.0`;
  expectCode(
    "TYPCAST-IR-0002",
    () => Document.fromJSON(longComponent),
    "a version component of more than 4300 digits must be rejected",
  );

  const longPatch = buildDocument().toJSON() as Record<string, unknown>;
  longPatch["schemaVersion"] = `1.0.${"1".repeat(5000)}`;
  checkEqual(
    Document.fromJSON(longPatch).schemaVersion,
    longPatch["schemaVersion"],
    "a patch component of more than 4300 digits must be accepted",
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

  for (const version of ["01.0.0", "1.00.0", "1.0.00"]) {
    const leadingZero = buildDocument().toJSON() as Record<string, unknown>;
    leadingZero["schemaVersion"] = version;
    expectCode(
      "TYPCAST-IR-0002",
      () => Document.fromJSON(leadingZero),
      "a version with a leading zero must be rejected",
    );
  }

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

  // The grammar of JSON holds no key that is not a string. A symbol key is
  // the only key of a JavaScript object that is not a string, and the reader
  // must reject it as it rejects another key in the Python SDK.
  const symbolKey = buildDocument().toJSON() as Record<string, unknown>;
  const symbolMetadata = symbolKey["metadata"] as Record<string, unknown>;
  Object.defineProperty(symbolMetadata, Symbol("key"), {
    value: "not a field",
    enumerable: true,
    configurable: true,
    writable: true,
  });
  expectDiagnostic(
    "TYPCAST-IR-0004",
    "/metadata",
    "'/metadata' must be a JSON object whose keys are strings.",
    { keyType: "non-string" },
    () => Document.fromJSON(symbolKey),
    "a nested object with a key that is not a string must be rejected",
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

  const longToken = buildDocument()
    .toJSONString()
    .replace('"value": 2,', `"value": ${"1".repeat(5000)},`);
  expectCode(
    "TYPCAST-IR-0004",
    () => Document.fromJSONString(longToken),
    "a long integer token must be rejected as an overflow",
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

  const zeroWidth = buildDocument().toJSON() as Record<string, unknown>;
  zeroWidth["contents"] = [
    {
      type: "image",
      path: "figure.png",
      alt: "Figure",
      width: { value: 0, unit: "cm" },
    },
  ];
  expectPath(
    "/contents/0/width/value",
    () => Document.fromJSON(zeroWidth),
    "an image width of zero must be rejected at the width",
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

function versionTests(): void {
  check(
    /^\d+\.\d+\.\d+$/.test(String(VERSION)),
    "the package version must be exported",
  );
  check(
    String(VERSION) !== String(SCHEMA_VERSION),
    "the package version must not be the schema version",
  );
}

// ---------------------------------------------------------------------------
// Paper catalog
// ---------------------------------------------------------------------------

function paperCatalogTests(): void {
  // The catalog of the paper variants lives in the contract layer, and the
  // values reach the SDK through a generated source file, so the SDK holds no
  // hand-written copy of the catalog that could drift.
  check(
    PAPER_VARIANTS.includes("a4"),
    "the package must export the variants of the paper catalog",
  );
  checkEqual(
    new Set(PAPER_VARIANTS).size,
    PAPER_VARIANTS.length,
    "the variants of the paper catalog must be unique",
  );
  checkEqual(
    PAPER_VARIANTS[0],
    "a0",
    "the first variant of the paper catalog must be the first of the catalog",
  );
  checkEqual(
    PAPER_VARIANTS[PAPER_VARIANTS.length - 1],
    "presentation-4-3",
    "the last variant of the paper catalog must be the last of the catalog",
  );
  checkEqual(
    new Page("a4", "portrait", margin()).paper,
    "a4",
    "a variant of the paper catalog must be accepted",
  );
  expectDiagnostic(
    "TYPCAST-VAL-0003",
    "/paper",
    "'/paper' must be a variant of the paper catalog, got 'a4x'.",
    { allowed: [...PAPER_VARIANTS], value: "a4x" },
    () => new Page("a4x", "portrait", margin()),
    "a paper that is not a variant of the catalog must be rejected",
  );
  const badPaper = buildDocument().toJSON() as Record<string, unknown>;
  (badPaper["page"] as Record<string, unknown>)["paper"] = "a4x";
  expectDiagnostic(
    "TYPCAST-VAL-0003",
    "/page/paper",
    "'/paper' must be a variant of the paper catalog, got 'a4x'.",
    { allowed: [...PAPER_VARIANTS], value: "a4x" },
    () => Document.fromJSON(badPaper),
    "the reader must reject a paper that is not a variant of the catalog",
  );
}

immutabilityTests();
constructorTests();
rejectedValueTests();
encodabilityTests();
numberDomainTests();
diagnosticMessageTests();
serializationTests();
deserializationTests();
roundTripTests();
versionTests();
paperCatalogTests();

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`ERROR ${failure}`);
  }
  console.error(`failures: ${failures.length}`);
  throw new Error(`${failures.length} unit test failures`);
}
console.log("failures: 0");
