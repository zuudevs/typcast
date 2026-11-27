/**
 * Unit tests for the validation engine of the TypeScript SDK.
 *
 * The tests cover the semantic rules of `docs/specifications/document-ir.md`:
 * the shape of a table, the uniqueness of a module alias, and the size of a
 * raw node. They also cover the configuration of the raw size limit and the
 * order of the diagnostics.
 */

import {
  Bold,
  ConfigError,
  Document,
  Heading,
  Image,
  Italic,
  Length,
  Link,
  ListBlock,
  Margin,
  Metadata,
  Module,
  Monospace,
  Page,
  Paragraph,
  RawBlock,
  RawSpan,
  Table,
  TableColumn,
  Text,
  TypcastError,
  utf8Length,
  validateDocument,
} from "../lib/src/index.js";
import type { Block, Diagnostic } from "../lib/src/index.js";

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

function margin(): Margin {
  return new Margin(
    new Length(2, "cm"),
    new Length(2, "cm"),
    new Length(2, "cm"),
    new Length(2, "cm"),
  );
}

function buildDocument(
  contents: readonly Block[],
  modules: readonly Module[] = [],
): Document {
  return new Document(
    new Metadata("Title"),
    new Page("a4", "portrait", margin()),
    contents,
    modules,
  );
}

function paragraph(...values: readonly string[]): Paragraph {
  return new Paragraph(values.map((value) => new Text(value)));
}

function table(columns: number, rows: readonly number[]): Table {
  return new Table(
    Array.from({ length: columns }, (_unused, index) =>
      new TableColumn([new Text(`Column ${index}`)], "left"),
    ),
    rows.map((count) =>
      Array.from({ length: count }, (_unused, cell) => [new Text(`Cell ${cell}`)]),
    ),
  );
}

function codes(diagnostics: readonly Diagnostic[]): string[] {
  return diagnostics.map((diagnostic) => diagnostic.code);
}

function paths(diagnostics: readonly Diagnostic[]): (string | null)[] {
  return diagnostics.map((diagnostic) => diagnostic.path);
}

function details(diagnostic: Diagnostic): Record<string, unknown> {
  return { ...diagnostic.details };
}

// ---------------------------------------------------------------------------
// The rules of the engine
// ---------------------------------------------------------------------------

function validDocumentTests(): void {
  const subject = buildDocument([paragraph("Body")]);
  checkEqual(
    subject.validate().length,
    0,
    "a valid document must report no diagnostic",
  );
  checkEqual(
    validateDocument(subject).length,
    0,
    "the function must agree with the method",
  );
}

function tableShapeTests(): void {
  const tooFew = buildDocument([table(2, [2, 1])]).validate();
  checkEqual(tooFew.length, 1, "a row with too few cells must be reported");
  checkEqual(tooFew[0]?.code, "TYPCAST-VAL-0007", "the code must be the table shape");
  checkEqual(tooFew[0]?.path, "/contents/0/rows/1", "the path must name the row");
  checkEqual(
    tooFew[0]?.message,
    "'/contents/0/rows/1' must hold 2 cells, got 1.",
    "the message must name the counts",
  );
  checkEqual(
    JSON.stringify(details(tooFew[0] as Diagnostic)),
    JSON.stringify({ columns: 2, cells: 1 }),
    "the details must name the counts",
  );
  checkEqual(tooFew[0]?.severity, "error", "the severity must be an error");
  checkEqual(
    tooFew[0]?.phase,
    "validation",
    "the phase must be the validation phase",
  );

  const tooMany = buildDocument([table(1, [2])]).validate();
  checkEqual(tooMany.length, 1, "a row with too many cells must be reported");
  checkEqual(tooMany[0]?.path, "/contents/0/rows/0", "the path must name the row");
  checkEqual(
    JSON.stringify(details(tooMany[0] as Diagnostic)),
    JSON.stringify({ columns: 1, cells: 2 }),
    "the details must name the counts",
  );

  const everyRow = buildDocument([table(2, [1, 3, 2])]).validate();
  checkEqual(everyRow.length, 2, "every broken row must be reported");
  checkEqual(
    JSON.stringify(paths(everyRow)),
    JSON.stringify(["/contents/0/rows/0", "/contents/0/rows/1"]),
    "the broken rows must come in the order of the table",
  );
}

function moduleAliasTests(): void {
  const duplicated = buildDocument(
    [paragraph("Body")],
    [new Module("modules/a.typ", "report"), new Module("modules/b.typ", "report")],
  ).validate();
  checkEqual(duplicated.length, 1, "a duplicated alias must be reported");
  checkEqual(
    duplicated[0]?.code,
    "TYPCAST-VAL-0008",
    "the code must be the module alias code",
  );
  checkEqual(
    duplicated[0]?.path,
    "/modules/1/alias",
    "the path must name the later declaration",
  );
  checkEqual(
    duplicated[0]?.message,
    "'/modules/1/alias' is already used by the module at '/modules/0/alias'.",
    "the message must name the first use",
  );
  checkEqual(
    JSON.stringify(details(duplicated[0] as Diagnostic)),
    JSON.stringify({ alias: "report", duplicateOf: "/modules/0/alias" }),
    "the details must name the alias and the first use",
  );

  const everyDuplicate = buildDocument(
    [paragraph("Body")],
    [
      new Module("modules/a.typ", "report"),
      new Module("modules/b.typ", "report"),
      new Module("modules/c.typ", "report"),
    ],
  ).validate();
  checkEqual(everyDuplicate.length, 2, "every duplicate must be reported");
  checkEqual(
    JSON.stringify(paths(everyDuplicate)),
    JSON.stringify(["/modules/1/alias", "/modules/2/alias"]),
    "the duplicates must come in the order of the declaration",
  );

  const distinct = buildDocument(
    [paragraph("Body")],
    [new Module("modules/a.typ", "first"), new Module("modules/b.typ", "second")],
  ).validate();
  checkEqual(distinct.length, 0, "distinct aliases must be accepted");

  // A module that names no alias takes the name of its file, which the asset
  // layer resolves, so the engine cannot compare it.
  const withoutAlias = buildDocument(
    [paragraph("Body")],
    [
      new Module("modules/report.typ"),
      new Module("modules/summary.typ"),
      new Module("modules/format.typ", null, ["currency"]),
    ],
  ).validate();
  checkEqual(
    withoutAlias.length,
    0,
    "a module that names no alias must take no part in the check",
  );
}

function rawSizeTests(): void {
  const atTheLimit = buildDocument([new RawBlock("markup", "12345678")]).validate({
    maxRawBytes: 8,
  });
  checkEqual(
    atTheLimit.length,
    0,
    "a raw value of exactly the limit must be accepted",
  );

  const overTheLimit = buildDocument([new RawBlock("markup", "123456789")]).validate({
    maxRawBytes: 8,
  });
  checkEqual(overTheLimit.length, 1, "a raw value over the limit must be reported");
  checkEqual(
    overTheLimit[0]?.code,
    "TYPCAST-VAL-0010",
    "the code must be the raw size code",
  );
  checkEqual(
    overTheLimit[0]?.path,
    "/contents/0/value",
    "the path must name the raw value",
  );
  checkEqual(
    overTheLimit[0]?.message,
    "'/contents/0/value' must not hold more than 8 bytes, got 9.",
    "the message must name the limit and the size",
  );
  checkEqual(
    JSON.stringify(details(overTheLimit[0] as Diagnostic)),
    JSON.stringify({ maxBytes: 8, bytes: 9 }),
    "the details must name the limit and the size",
  );

  // The limit counts bytes and not code points.
  const multibyte = buildDocument([new RawBlock("markup", "한글한글")]);
  checkEqual(
    multibyte.validate({ maxRawBytes: 12 }).length,
    0,
    "a raw value of twelve bytes must be accepted",
  );
  const tooManyBytes = multibyte.validate({ maxRawBytes: 11 });
  checkEqual(
    tooManyBytes.length,
    1,
    "a raw value of twelve bytes must be rejected by a limit of eleven",
  );
  checkEqual(
    JSON.stringify(details(tooManyBytes[0] as Diagnostic)),
    JSON.stringify({ maxBytes: 11, bytes: 12 }),
    "the details must count the bytes",
  );

  const defaultLimit = buildDocument([
    new RawBlock("markup", "x".repeat(1_048_576)),
  ]).validate();
  checkEqual(
    defaultLimit.length,
    0,
    "the default limit must accept one mebibyte",
  );
  const overDefault = buildDocument([
    new RawBlock("markup", "x".repeat(1_048_577)),
  ]).validate();
  checkEqual(
    overDefault.length,
    1,
    "the default limit must reject one byte more than a mebibyte",
  );
  checkEqual(
    JSON.stringify(details(overDefault[0] as Diagnostic)),
    JSON.stringify({ maxBytes: 1_048_576, bytes: 1_048_577 }),
    "the default limit must be one mebibyte",
  );
}

function rawSpanTests(): void {
  const raw = new RawSpan("code", "12345");
  const cases: readonly (readonly [readonly Block[], readonly string[]])[] = [
    [[new Paragraph([raw])], ["/contents/0/content/0/value"]],
    [[new Heading(1, [raw])], ["/contents/0/content/0/value"]],
    [[new ListBlock(false, [[raw]])], ["/contents/0/items/0/0/value"]],
    [
      [
        new Paragraph([
          new Bold([raw]),
          new Italic([raw]),
          new Monospace([raw]),
          new Link("https://example.com", [raw]),
        ]),
      ],
      [
        "/contents/0/content/0/content/0/value",
        "/contents/0/content/1/content/0/value",
        "/contents/0/content/2/content/0/value",
        "/contents/0/content/3/content/0/value",
      ],
    ],
    [
      [new Image("a.png", "A", [raw])],
      ["/contents/0/caption/0/value"],
    ],
    [
      [
        new Table(
          [new TableColumn([new Text("A")], "left")],
          [[[raw]]],
        ),
      ],
      ["/contents/0/rows/0/0/0/value"],
    ],
    [
      [
        new Table(
          [new TableColumn([raw], "left")],
          [[[new Text("Cell")]]],
        ),
      ],
      ["/contents/0/columns/0/header/0/value"],
    ],
  ];
  for (const [blocks, expected] of cases) {
    const diagnostics = buildDocument(blocks).validate({ maxRawBytes: 4 });
    checkEqual(
      JSON.stringify(paths(diagnostics)),
      JSON.stringify(expected),
      `the raw spans must be reported at ${expected.join(", ")}`,
    );
    for (const diagnostic of diagnostics) {
      checkEqual(
        diagnostic.code,
        "TYPCAST-VAL-0010",
        "the code must be the raw size code",
      );
    }
  }
}

// ---------------------------------------------------------------------------
// The order and the delivery of the diagnostics
// ---------------------------------------------------------------------------

function orderTests(): void {
  const subject = buildDocument(
    [
      table(2, [2, 1, 3]),
      new Paragraph([new RawSpan("code", "12345")]),
    ],
    [new Module("modules/a.typ", "report"), new Module("modules/b.typ", "report")],
  );
  const diagnostics = subject.validate({ maxRawBytes: 4 });
  checkEqual(
    JSON.stringify(codes(diagnostics)),
    JSON.stringify([
      "TYPCAST-VAL-0007",
      "TYPCAST-VAL-0007",
      "TYPCAST-VAL-0010",
      "TYPCAST-VAL-0008",
    ]),
    "the diagnostics must come in the order of the document",
  );
  checkEqual(
    JSON.stringify(paths(diagnostics)),
    JSON.stringify([
      "/contents/0/rows/1",
      "/contents/0/rows/2",
      "/contents/1/content/0/value",
      "/modules/1/alias",
    ]),
    "the paths must come in the order of the document",
  );
  check(
    Array.isArray(diagnostics),
    "the engine must return an array",
  );
}

function configurationTests(): void {
  let thrown: unknown;
  try {
    buildDocument([paragraph("Body")]).validate({ maxRawBytes: -1 });
  } catch (error) {
    thrown = error;
  }
  check(thrown instanceof ConfigError, "a negative limit must raise a config error");
  if (thrown instanceof ConfigError) {
    const diagnostic = thrown.diagnostics[0] as Diagnostic;
    checkEqual(
      diagnostic.code,
      "TYPCAST-CONFIG-0004",
      "the code must be the raw limit code",
    );
    checkEqual(diagnostic.phase, "config", "the phase must be the config phase");
    checkEqual(
      diagnostic.path,
      "/max_raw_bytes",
      "the path must name the limit",
    );
    checkEqual(
      diagnostic.message,
      "'/max_raw_bytes' must not be negative, got '-1'.",
      "the message must name the rule",
    );
    checkEqual(
      JSON.stringify(details(diagnostic)),
      JSON.stringify({ value: -1 }),
      "the details must name the value",
    );
  }

  for (const value of [1.5, Number.NaN, Number.POSITIVE_INFINITY]) {
    let failed = false;
    try {
      buildDocument([paragraph("Body")]).validate({ maxRawBytes: value });
    } catch {
      failed = true;
    }
    check(failed, `a limit of ${String(value)} must be rejected`);
  }

  checkEqual(
    buildDocument([paragraph("Body")]).validate({ maxRawBytes: 0 }).length,
    0,
    "a limit of zero must be accepted",
  );
}

function argumentTests(): void {
  let thrown: unknown;
  try {
    validateDocument("not a document" as unknown as Document);
  } catch (error) {
    thrown = error;
  }
  check(thrown instanceof TypcastError, "a value that is not a document must be rejected");
  if (thrown instanceof TypcastError) {
    const diagnostic = thrown.diagnostics[0] as Diagnostic;
    checkEqual(
      diagnostic.code,
      "TYPCAST-VAL-0001",
      "the code must be the required field code",
    );
    checkEqual(diagnostic.path, "/", "the path must name the document");
    checkEqual(
      diagnostic.message,
      "'/' must be a Document.",
      "the message must name the expected type",
    );
    checkEqual(
      JSON.stringify(details(diagnostic)),
      JSON.stringify({ expected: "Document" }),
      "the details must name the expected type",
    );
  }
}

// ---------------------------------------------------------------------------
// The measurement of the size of a text
// ---------------------------------------------------------------------------

function encodingTests(): void {
  checkEqual(utf8Length(""), 0, "an empty text takes no byte");
  checkEqual(utf8Length("abc"), 3, "an ASCII text takes one byte per character");
  checkEqual(utf8Length("é"), 2, "a Latin-1 text takes two bytes per character");
  checkEqual(utf8Length("한"), 3, "a Hangul text takes three bytes per character");
  checkEqual(utf8Length("😀"), 4, "an astral text takes four bytes per character");
  checkEqual(
    utf8Length("\ud800"),
    3,
    "a surrogate that UTF-8 cannot encode takes three bytes",
  );
}

validDocumentTests();
tableShapeTests();
moduleAliasTests();
rawSizeTests();
rawSpanTests();
orderTests();
configurationTests();
argumentTests();
encodingTests();

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`ERROR ${failure}`);
  }
  console.error(`failures: ${failures.length}`);
  throw new Error(`${failures.length} unit test failures`);
}
console.log("failures: 0");
