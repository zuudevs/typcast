/**
 * Unit tests for the fluent builder of the TypeScript SDK.
 *
 * The tests cover the contract of `docs/specifications/sdk-api.md`: the
 * surface of the builder, the normalization of the content, the defaults of
 * the node catalog, the errors of the diagnostic taxonomy, and the
 * immutability of the snapshot that `build()` returns.
 */

import {
  ApiUsageError,
  Bold,
  Document,
  DocumentBuilder,
  Italic,
  Length,
  Link,
  ListBlock,
  Margin,
  Monospace,
  RawBlock,
  RawSpan,
  TableColumn,
  Text,
  TypcastError,
  ValidationError,
  bold,
  cell,
  column,
  italic,
  lineBreak,
  link,
  monospace,
  rawInline,
  text,
} from "../lib/src/index.js";
import type { Alignment, Block, Diagnostic } from "../lib/src/index.js";

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

function codes(diagnostics: readonly Diagnostic[]): readonly string[] {
  return diagnostics.map((diagnostic) => diagnostic.code);
}

/** Returns the content of a paragraph block. */
function paragraphContent(block: Block | undefined): readonly unknown[] {
  return block !== undefined && block.type === "paragraph" ? block.content : [];
}

function builderSurfaceTests(): void {
  const subject = new DocumentBuilder();
  check(subject instanceof DocumentBuilder, "the builder must need no argument");

  for (const name of [
    "title",
    "author",
    "date",
    "page",
    "heading",
    "paragraph",
    "bulletList",
    "numberedList",
    "table",
    "image",
    "pageBreak",
    "raw",
    "module",
    "build",
  ] as const) {
    check(
      typeof subject[name] === "function",
      `the builder must expose '${name}'`,
    );
  }

  for (const helper of [
    text,
    bold,
    italic,
    monospace,
    link,
    lineBreak,
    rawInline,
    column,
    cell,
  ]) {
    check(typeof helper === "function", "the helpers must be functions");
  }

  check(
    subject.title("Title") === subject,
    "title must return the builder",
  );
  check(
    subject.author("Author") === subject,
    "author must return the builder",
  );
  check(subject.date("2026-11-24") === subject, "date must return the builder");
  check(subject.page() === subject, "page must return the builder");
  check(
    subject.heading(1, "Heading") === subject,
    "heading must return the builder",
  );
  check(subject.paragraph("Body") === subject, "paragraph must return the builder");
  check(
    subject.bulletList(["Item"]) === subject,
    "bulletList must return the builder",
  );
  check(
    subject.numberedList(["Item"]) === subject,
    "numberedList must return the builder",
  );
  check(
    subject.table({ columns: [column("A")], rows: [[["x"]]] }) === subject,
    "table must return the builder",
  );
  check(
    subject.image("a.png", { alt: "Alt" }) === subject,
    "image must return the builder",
  );
  check(subject.pageBreak() === subject, "pageBreak must return the builder");
  check(subject.raw("#value") === subject, "raw must return the builder");
  check(subject.module("a.typ") === subject, "module must return the builder");
}

function documentedExampleTests(): void {
  const document = new DocumentBuilder()
    .title("Quarterly Report")
    .author("Example Corp")
    .date("2026-11-24")
    .page({ paper: "a4", orientation: "portrait", margin: Length.cm(2.0) })
    .heading(1, "Quarterly Report")
    .paragraph("Revenue grew by ", bold("12%"), ".")
    .bulletList(["Revenue", "Cost", "Headcount"])
    .table({
      columns: [column("Metric", "left"), column("Value", "right")],
      rows: [
        [["Revenue"], ["1,200"]],
        [["Cost"], ["800"]],
      ],
    })
    .image("figures/revenue.png", { alt: "Revenue chart", caption: "Figure 1" })
    .pageBreak()
    .raw('#figure(image("logo.png"), caption: [Logo])', { format: "markup" })
    .module("modules/format.typ", { items: ["currency"] })
    .build();

  check(document instanceof Document, "the builder must return a document");
  checkEqual(document.contents.length, 7, "the document must hold seven blocks");
  checkEqual(document.modules.length, 1, "the document must hold one module");
}

function orderTests(): void {
  const document = new DocumentBuilder()
    .title("Title")
    .heading(1, "First")
    .paragraph("Second")
    .pageBreak()
    .build();
  checkEqual(
    JSON.stringify(document.contents.map((block) => block.type)),
    JSON.stringify(["heading", "paragraph", "pageBreak"]),
    "the blocks must keep the order of the calls",
  );

  const withModules = new DocumentBuilder()
    .title("Title")
    .paragraph("Body")
    .module("a.typ", { alias: "first" })
    .module("b.typ", { alias: "second" })
    .build();
  checkEqual(
    JSON.stringify(withModules.modules.map((module) => module.path)),
    JSON.stringify(["a.typ", "b.typ"]),
    "the modules must keep the order of the calls",
  );
}

function contentNormalizationTests(): void {
  const paragraph = new DocumentBuilder()
    .title("Title")
    .paragraph("Body")
    .build().contents[0];
  check(
    paragraph !== undefined && paragraph.type === "paragraph",
    "the builder must add a paragraph",
  );
  checkEqual(
    JSON.stringify(paragraphContent(paragraph)),
    JSON.stringify([new Text("Body")]),
    "a string must become a text span",
  );

  const boldParagraph = new DocumentBuilder()
    .title("Title")
    .paragraph(bold("Body"))
    .build().contents[0];
  checkEqual(
    JSON.stringify(paragraphContent(boldParagraph)),
    JSON.stringify([new Bold([new Text("Body")])]),
    "a span must be kept",
  );

  const mixed = new DocumentBuilder()
    .title("Title")
    .paragraph("A ", bold("B"), " C")
    .build().contents[0];
  checkEqual(
    JSON.stringify(paragraphContent(mixed)),
    JSON.stringify([new Text("A "), new Bold([new Text("B")]), new Text(" C")]),
    "the order of the content must be kept",
  );

  const twoStrings = new DocumentBuilder()
    .title("Title")
    .paragraph("A", "B")
    .build().contents[0];
  checkEqual(
    JSON.stringify(paragraphContent(twoStrings)),
    JSON.stringify([new Text("A"), new Text("B")]),
    "two strings must not be merged",
  );

  const nested = new DocumentBuilder()
    .title("Title")
    .paragraph(bold("A", italic("B")))
    .build().contents[0];
  checkEqual(
    JSON.stringify(paragraphContent(nested)),
    JSON.stringify([new Bold([new Text("A"), new Italic([new Text("B")])])]),
    "the emphasis must nest",
  );

  const list = new DocumentBuilder()
    .title("Title")
    .bulletList(["Plain", ["Mixed ", bold("bold")]])
    .build().contents[0];
  check(
    list !== undefined && list.type === "list",
    "the builder must add a list",
  );
  checkEqual(
    JSON.stringify(list?.type === "list" ? list.items : []),
    JSON.stringify([
      [new Text("Plain")],
      [new Text("Mixed "), new Bold([new Text("bold")])],
    ]),
    "a list item must be normalized",
  );

  const table = new DocumentBuilder()
    .title("Title")
    .table({ columns: [column("Metric")], rows: [[["1,200"]]] })
    .build().contents[0];
  check(
    table !== undefined && table.type === "table",
    "the builder must add a table",
  );
  checkEqual(
    JSON.stringify(table?.type === "table" ? table.columns[0]?.header : []),
    JSON.stringify([new Text("Metric")]),
    "a table header must be normalized",
  );
  checkEqual(
    JSON.stringify(table?.type === "table" ? table.rows[0]?.[0] : []),
    JSON.stringify([new Text("1,200")]),
    "a table cell must be normalized",
  );

  const emptyCell = new DocumentBuilder()
    .title("Title")
    .table({ columns: [column("Metric")], rows: [[[]]] })
    .build().contents[0];
  checkEqual(
    JSON.stringify(emptyCell?.type === "table" ? emptyCell.rows[0]?.[0] : []),
    JSON.stringify([]),
    "an empty table cell must be kept",
  );

  const image = new DocumentBuilder()
    .title("Title")
    .image("a.png", { alt: "Alt", caption: "Figure 1" })
    .build().contents[0];
  check(
    image !== undefined && image.type === "image",
    "the builder must add an image",
  );
  checkEqual(
    JSON.stringify(image?.type === "image" ? image.caption : []),
    JSON.stringify([new Text("Figure 1")]),
    "an image caption must be normalized",
  );

  const linked = new DocumentBuilder()
    .title("Title")
    .paragraph(link("https://example.com", "Example"))
    .build().contents[0];
  checkEqual(
    JSON.stringify(paragraphContent(linked)),
    JSON.stringify([new Link("https://example.com", [new Text("Example")])]),
    "a link content must be normalized",
  );

  check(text("A") instanceof Text, "text must return a text span");
  check(bold("A") instanceof Bold, "bold must return a bold span");
  check(italic("A") instanceof Italic, "italic must return an italic span");
  check(monospace("A") instanceof Monospace, "monospace must return a monospace span");
  check(link("u", "A") instanceof Link, "link must return a link span");
  check(lineBreak() instanceof Object, "lineBreak must return a line break");
  check(rawInline("x", "code") instanceof RawSpan, "rawInline must return a raw span");
  check(column("A") instanceof TableColumn, "column must return a table column");
}

function defaultTests(): void {
  const document = new DocumentBuilder().title("Title").paragraph("Body").build();
  checkEqual(document.page.paper, "a4", "the default paper must be a4");
  checkEqual(
    document.page.orientation,
    "portrait",
    "the default orientation must be portrait",
  );

  for (const side of [
    document.page.margin.top,
    document.page.margin.right,
    document.page.margin.bottom,
    document.page.margin.left,
  ]) {
    check(
      side.value === 2.5 && side.unit === "cm",
      "the default margin must be two and a half centimeters",
    );
  }

  const bullet = new DocumentBuilder().title("Title").bulletList(["Item"]).build()
    .contents[0];
  check(
    bullet !== undefined && bullet.type === "list" && !bullet.ordered,
    "a bullet list must be unordered",
  );

  const numbered = new DocumentBuilder().title("Title").numberedList(["Item"]).build()
    .contents[0];
  check(
    numbered !== undefined && numbered.type === "list" && numbered.ordered,
    "a numbered list must be ordered",
  );

  checkEqual(document.modules.length, 0, "the modules must be empty by default");
  check(document.metadata.author === null, "the author must be unset by default");
  check(document.metadata.date === null, "the date must be unset by default");

  const value = document.toJSON() as Record<string, unknown>;
  const metadata = value["metadata"] as Record<string, unknown>;
  check(!("author" in metadata), "the canonical JSON must hold no author");
  check(!("date" in metadata), "the canonical JSON must hold no date");

  const page = value["page"] as Record<string, unknown>;
  checkEqual(page["paper"], "a4", "the canonical JSON must hold the default paper");
  checkEqual(
    page["orientation"],
    "portrait",
    "the canonical JSON must hold the default orientation",
  );
  const marginValue = page["margin"] as Record<string, unknown>;
  checkEqual(
    JSON.stringify(marginValue["top"]),
    JSON.stringify({ value: 2.5, unit: "cm" }),
    "the canonical JSON must hold the default margin",
  );
  checkEqual(
    JSON.stringify(value["modules"]),
    JSON.stringify([]),
    "the canonical JSON must hold no module",
  );

  const image = new DocumentBuilder()
    .title("Title")
    .image("a.png", { alt: "Alt" })
    .build().contents[0];
  check(
    image !== undefined && image.type === "image" && image.caption === null,
    "an image without a caption must hold no caption",
  );
  check(
    image !== undefined && image.type === "image" && image.width === null,
    "an image without a width must hold no width",
  );

  const uniform = new DocumentBuilder()
    .title("Title")
    .page({ margin: Length.cm(2.0) })
    .paragraph("Body")
    .build();
  for (const side of [
    uniform.page.margin.top,
    uniform.page.margin.right,
    uniform.page.margin.bottom,
    uniform.page.margin.left,
  ]) {
    check(
      side.value === 2 && side.unit === "cm",
      "a uniform margin must be the margin of every side",
    );
  }

  const margin = new Margin(
    Length.cm(1.0),
    Length.cm(2.0),
    Length.cm(3.0),
    Length.cm(4.0),
  );
  const named = new DocumentBuilder()
    .title("Title")
    .page({ margin })
    .paragraph("Body")
    .build();
  check(
    named.page.margin.top.value === 1 &&
      named.page.margin.right.value === 2 &&
      named.page.margin.bottom.value === 3 &&
      named.page.margin.left.value === 4,
    "a margin must name every side",
  );
}

function assertError(
  code: string,
  phase: string,
  path: string,
  factory: () => unknown,
  errorType: typeof ValidationError = ValidationError,
): TypcastError {
  let thrown: unknown;
  try {
    factory();
  } catch (error) {
    thrown = error;
  }
  check(thrown instanceof errorType, `the error must be a ${errorType.name}`);
  if (thrown instanceof TypcastError) {
    const diagnostic = thrown.diagnostics[0] as Diagnostic;
    checkEqual(diagnostic.code, code, "the code must match");
    checkEqual(diagnostic.severity, "error", "the severity must be an error");
    checkEqual(diagnostic.phase, phase, "the phase must match");
    checkEqual(diagnostic.path, path, "the path must match");
    return thrown;
  }
  return new TypcastError("no error");
}

function validationTests(): void {
  assertError(
    "TYPCAST-VAL-0001",
    "validation",
    "/metadata/title",
    () => new DocumentBuilder().build(),
  );
  assertError(
    "TYPCAST-VAL-0006",
    "validation",
    "/contents",
    () => new DocumentBuilder().title("Title").build(),
  );
  assertError(
    "TYPCAST-VAL-0006",
    "validation",
    "/contents/0/content",
    () => new DocumentBuilder().title("Title").heading(1),
  );
  assertError(
    "TYPCAST-VAL-0006",
    "validation",
    "/contents/0/content",
    () => new DocumentBuilder().title("Title").paragraph(),
  );
  assertError(
    "TYPCAST-VAL-0006",
    "validation",
    "/contents/0/items",
    () => new DocumentBuilder().title("Title").bulletList([]),
  );
  assertError(
    "TYPCAST-VAL-0006",
    "validation",
    "/contents/0/items/0",
    () => new DocumentBuilder().title("Title").bulletList([[]]),
  );
  assertError(
    "TYPCAST-VAL-0007",
    "validation",
    "/contents/0/rows/0",
    () =>
      new DocumentBuilder()
        .title("Title")
        .table({ columns: [column("A"), column("B")], rows: [[["x"]]] })
        .build(),
  );
  assertError(
    "TYPCAST-VAL-0007",
    "validation",
    "/contents/0/rows/0",
    () =>
      new DocumentBuilder()
        .title("Title")
        .table({ columns: [column("A")], rows: [[["x"], ["y"]]] })
        .build(),
  );
  assertError(
    "TYPCAST-VAL-0008",
    "validation",
    "/modules/1/alias",
    () =>
      new DocumentBuilder()
        .title("Title")
        .paragraph("Body")
        .module("a.typ", { alias: "report" })
        .module("b.typ", { alias: "report" })
        .build(),
  );
  assertError(
    "TYPCAST-VAL-0009",
    "validation",
    "/modules/0/alias",
    () =>
      new DocumentBuilder()
        .title("Title")
        .module("a.typ", { alias: "report", items: ["currency"] }),
  );
  assertError(
    "TYPCAST-VAL-0008",
    "validation",
    "/modules/0/alias",
    () => new DocumentBuilder().title("Title").module("a.typ", { alias: "1report" }),
  );
  assertError(
    "TYPCAST-VAL-0005",
    "validation",
    "/contents/0/level",
    () => new DocumentBuilder().title("Title").heading(7, "Heading"),
  );
  assertError(
    "TYPCAST-VAL-0003",
    "validation",
    "/align",
    () =>
      new DocumentBuilder()
        .title("Title")
        .table({ columns: [column("A", "middle" as Alignment)], rows: [[["x"]]] }),
  );
  assertError(
    "TYPCAST-VAL-0003",
    "validation",
    "/contents/0/format",
    () => new DocumentBuilder().title("Title").raw("x", { format: "latex" as "code" }),
  );
  assertError(
    "TYPCAST-VAL-0011",
    "validation",
    "/metadata/date",
    () => new DocumentBuilder().title("Title").date("2026-13-01").build(),
  );
  assertError(
    "TYPCAST-VAL-0010",
    "validation",
    "/contents/0/value",
    () => new DocumentBuilder().title("Title").raw("x".repeat(1_048_577)).build(),
  );

  const atLimit = new DocumentBuilder()
    .title("Title")
    .raw("x".repeat(1_048_576))
    .build().contents[0];
  check(
    atLimit !== undefined && atLimit.type === "raw" && atLimit.value.length === 1_048_576,
    "a raw node at the limit must be accepted",
  );
  check(
    atLimit !== undefined && atLimit.type === "raw",
    "the raw node must be a raw block",
  );
}

function apiErrorTests(): void {
  assertError(
    "TYPCAST-API-0001",
    "api",
    "/metadata/title",
    () => new DocumentBuilder().title(42 as unknown as string),
    ApiUsageError,
  );
  assertError(
    "TYPCAST-API-0001",
    "api",
    "/contents/0/content/0",
    () => new DocumentBuilder().title("Title").paragraph(42 as unknown as string),
    ApiUsageError,
  );
  assertError(
    "TYPCAST-API-0001",
    "api",
    "/contents/0/level",
    () => new DocumentBuilder().title("Title").heading("1" as unknown as number, "Heading"),
    ApiUsageError,
  );
  assertError(
    "TYPCAST-API-0001",
    "api",
    "/page/margin",
    () => new DocumentBuilder().title("Title").page({ margin: 42 as unknown as Length }),
    ApiUsageError,
  );
  assertError(
    "TYPCAST-API-0001",
    "api",
    "/contents/0/columns/0",
    () =>
      new DocumentBuilder()
        .title("Title")
        .table({ columns: ["Metric" as unknown as TableColumn], rows: [[["x"]]] }),
    ApiUsageError,
  );
  assertError(
    "TYPCAST-API-0001",
    "api",
    "/contents/0/items/0",
    () => new DocumentBuilder().title("Title").bulletList([42 as unknown as string]),
    ApiUsageError,
  );
  assertError(
    "TYPCAST-API-0001",
    "api",
    "/modules/0/items/0",
    () =>
      new DocumentBuilder()
        .title("Title")
        .module("a.typ", { items: [42 as unknown as string] }),
    ApiUsageError,
  );

  let thrown: unknown;
  try {
    new DocumentBuilder().title(42 as unknown as string);
  } catch (error) {
    thrown = error;
  }
  if (thrown instanceof ApiUsageError) {
    checkEqual(thrown.diagnostics.length, 1, "an API error must carry one diagnostic");
    checkEqual(
      thrown.diagnostics[0]?.phase,
      "api",
      "an API error must carry the api phase",
    );
  }
}

function diagnosticCollectionTests(): void {
  let thrown: unknown;
  try {
    new DocumentBuilder()
      .title("Title")
      .table({ columns: [column("A"), column("B")], rows: [[["x"]]] })
      .module("a.typ", { alias: "report" })
      .module("b.typ", { alias: "report" })
      .build();
  } catch (error) {
    thrown = error;
  }
  check(thrown instanceof ValidationError, "the error must be a validation error");
  if (thrown instanceof ValidationError) {
    checkEqual(
      JSON.stringify(codes(thrown.diagnostics)),
      JSON.stringify(["TYPCAST-VAL-0007", "TYPCAST-VAL-0008"]),
      "the error must carry every diagnostic",
    );
    checkEqual(
      JSON.stringify(
        thrown.diagnostics.map((diagnostic) => diagnostic.path),
      ),
      JSON.stringify(["/contents/0/rows/0", "/modules/1/alias"]),
      "the paths must come in the order of the document",
    );
    checkEqual(
      thrown.message,
      thrown.diagnostics[0]?.message,
      "the message must name the first diagnostic",
    );
  }
}

function snapshotTests(): void {
  const builder = new DocumentBuilder().title("Title").paragraph("First");
  const document = builder.build();
  const before = document.toJSONString();
  builder.paragraph("Second").title("Another title");
  checkEqual(document.toJSONString(), before, "a later call must not change a document");
  checkEqual(document.contents.length, 1, "a later call must not add a block");

  const first = builder.build();
  const second = builder.build();
  checkEqual(first.contents.length, 2, "the first build must hold two blocks");
  checkEqual(second.contents.length, 2, "the second build must hold two blocks");

  const items = ["First"];
  const listDocument = new DocumentBuilder().title("Title").bulletList(items).build();
  const listBefore = listDocument.toJSONString();
  items.push("Second");
  checkEqual(
    listDocument.toJSONString(),
    listBefore,
    "a caller must not change a document with an input list",
  );

  const rows: (string[])[][] = [[["First"]]];
  const tableDocument = new DocumentBuilder()
    .title("Title")
    .table({ columns: [column("A")], rows })
    .build();
  const tableBefore = tableDocument.toJSONString();
  rows[0]?.push(["Second"]);
  rows[0]?.[0]?.push("Changed");
  checkEqual(
    tableDocument.toJSONString(),
    tableBefore,
    "a caller must not change a document with an input row",
  );

  const columns = [column("A")];
  const columnDocument = new DocumentBuilder()
    .title("Title")
    .table({ columns, rows: [[["x"]]] })
    .build();
  const columnBefore = columnDocument.toJSONString();
  columns.push(column("B"));
  checkEqual(
    columnDocument.toJSONString(),
    columnBefore,
    "a caller must not change a document with an input column",
  );

  const itemContent = [["First", bold("bold")]] as (string | ReturnType<typeof bold>)[][];
  const itemDocument = new DocumentBuilder().title("Title").bulletList(itemContent).build();
  const itemBefore = itemDocument.toJSONString();
  itemContent[0]?.push("Changed");
  checkEqual(
    itemDocument.toJSONString(),
    itemBefore,
    "a caller must not change a document with an input item",
  );
}

builderSurfaceTests();
documentedExampleTests();
orderTests();
contentNormalizationTests();
defaultTests();
validationTests();
apiErrorTests();
diagnosticCollectionTests();
snapshotTests();

if (failures.length > 0) {
  for (const failure of failures) {
    console.error(`ERROR ${failure}`);
  }
  console.error(`failures: ${failures.length}`);
  throw new Error(`${failures.length} unit test failures`);
}
console.log("failures: 0");
