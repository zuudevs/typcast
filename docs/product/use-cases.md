# Use cases

Status: CONFIRMED
Scope: Explanatory and normative
Last updated: 2026-11-24

## Purpose

This document defines the first report-oriented use cases that the MVP must
support. Each use case is expressed as a journey, a minimal API shape, and
acceptance criteria. The use cases constrain the node catalog and fixtures; they
do not add nodes outside the approved MVP scope.

## UC-001: Quarterly business report

A developer receives revenue, cost, and headcount data from an application and
builds a multi-page report with a title page, headings, paragraphs, a table, a
chart image, and a conclusion.

### Journey

1. Create a document with title, author, and date.
2. Configure A4 paper, portrait orientation, and 2 cm margins.
3. Add a title and section headings.
4. Add paragraphs with bold and italic emphasis.
5. Add a table with a header row and right-aligned numeric cells.
6. Add a chart image with alt text and caption.
7. Build the document and validate it.
8. Emit `.typ`.
9. Compile PDF with a supported Typst CLI.
10. Write the PDF to an output path.

### Acceptance criteria

| ID | Criterion | Status |
|---|---|---|
| AC-001 | The document contains at least two pages and one table. | CONFIRMED |
| AC-002 | The chart image is resolved relative to `assetRoot`. | CONFIRMED |
| AC-003 | The emitted `.typ` is identical in Python and TypeScript for the same fixture. | CONFIRMED |
| AC-004 | The PDF starts with a valid PDF header and is non-empty. | CONFIRMED |
| AC-005 | A missing image produces `TYPCAST-IO-0001`, not an unhandled compiler error. | CONFIRMED |

## UC-002: Invoice

A developer generates an invoice from line items, a customer record, and a logo.
The document uses a table for line items, right-aligned amounts, a total row, and
a footer-like final paragraph.

### Journey

1. Create a document with invoice metadata.
2. Add a logo image with alt text.
3. Add customer and invoice detail paragraphs.
4. Add a line-item table with columns for description, quantity, unit price, and
   amount.
5. Add a total paragraph with bold emphasis.
6. Build, validate, emit, and compile.
7. Return the PDF bytes to a web response or write it to disk.

### Acceptance criteria

| ID | Criterion | Status |
|---|---|---|
| AC-006 | Numeric table cells can be right-aligned without raw Typst. | CONFIRMED |
| AC-007 | The total row is expressible with the core table node. | CONFIRMED |
| AC-008 | `compile_pdf()` can return bytes without writing a file. | CONFIRMED |
| AC-009 | `write_pdf(path)` writes the same bytes returned by the result object. | CONFIRMED |

## UC-003: Technical documentation

A developer generates a short technical document from Markdown-like data:
headings, paragraphs, bullet lists, links, and code snippets. The code snippets
may require raw Typst when the core node set is insufficient.

### Journey

1. Create a document with a title and author.
2. Add headings and paragraphs.
3. Add bullet and numbered lists.
4. Add links with display text.
5. Add a raw code block for a Typst-specific example.
6. Build and emit.
7. Compile and inspect diagnostics if the raw content is invalid.

### Acceptance criteria

| ID | Criterion | Status |
|---|---|---|
| AC-010 | Links render with display text and a URL. | CONFIRMED |
| AC-011 | Raw code is emitted verbatim and is not escaped. | CONFIRMED |
| AC-012 | Invalid raw content is reported as a compiler diagnostic, not a Typcast validation error. | CONFIRMED |
| AC-013 | The document remains valid when no image or table is present. | CONFIRMED |

## UC-004: Data-driven batch report

A service generates many reports from JSON payloads. The service validates each
payload, emits `.typ`, compiles PDFs, and records diagnostics without crashing
the process.

### Journey

1. Receive a JSON document that conforms to the published schema.
2. Deserialize it into the immutable model.
3. Validate it against the supported schema version.
4. Emit `.typ`.
5. Compile with a configured Typst path and timeout.
6. Persist the PDF and structured diagnostics.
7. Continue with the next payload.

### Acceptance criteria

| ID | Criterion | Status |
|---|---|---|
| AC-014 | Deserialization rejects an unsupported major schema version. | CONFIRMED |
| AC-015 | A validation failure is catchable as a typed error with diagnostics. | CONFIRMED |
| AC-016 | A compiler timeout is reported as `TYPCAST-COMPILER-0003`. | CONFIRMED |
| AC-017 | A failed document does not leave a partial PDF at the requested output path. | CONFIRMED |
| AC-018 | Batch processing does not share mutable builder state between documents. | CONFIRMED |

## Example API shape

The following example is illustrative. The normative API is in
`specifications/sdk-api.md`.

```python
from pathlib import Path
from typcast import DocumentBuilder, Length, bold, column

document = (
    DocumentBuilder()
    .title("Quarterly Report")
    .author("Example Corp")
    .page(paper="a4", orientation="portrait", margin=Length.cm(2.0))
    .heading(1, "Quarterly Report")
    .paragraph("Revenue grew by ", bold("12%"), ".")
    .table(
        columns=[
            column("Metric", align="left"),
            column("Value", align="right"),
        ],
        rows=[
            [["Revenue"], ["1,200"]],
            [["Cost"], ["800"]],
        ],
    )
    .image("figures/revenue.png", alt="Revenue chart", caption="Figure 1")
    .build()
)

result = document.compile_pdf(
    asset_root=Path("assets"),
    output_path=Path("out/report.pdf"),
)
```

```typescript
import { DocumentBuilder, Length, bold, column } from "typcast";

const document = new DocumentBuilder()
  .title("Quarterly Report")
  .author("Example Corp")
  .page({
    paper: "a4",
    orientation: "portrait",
    margin: Length.cm(2),
  })
  .heading(1, "Quarterly Report")
  .paragraph("Revenue grew by ", bold("12%"), ".")
  .table({
    columns: [column("Metric", "left"), column("Value", "right")],
    rows: [
      [["Revenue"], ["1,200"]],
      [["Cost"], ["800"]],
    ],
  })
  .build();

const result = await document.compilePdf({
  assetRoot: "assets",
  outputPath: "out/report.pdf",
});
```

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| UCR-001 | The MVP MUST support at least one complete report journey end to end. | CONFIRMED | Example integration test. |
| UCR-002 | The MVP MUST support table header rows and per-column alignment. | CONFIRMED | Node and emitter tests. |
| UCR-003 | The MVP MUST support images with alt text and optional captions. | CONFIRMED | Node and emitter tests. |
| UCR-004 | The MVP MUST support links with display text. | CONFIRMED | Node and emitter tests. |
| UCR-005 | The MVP MUST support raw Typst as an escape hatch. | CONFIRMED | Emitter test. |
| UCR-006 | The MVP MUST allow PDF bytes to be returned without filesystem output. | CONFIRMED | Compiler API test. |
| UCR-007 | The MVP MUST report validation and compiler failures without terminating the host process. | CONFIRMED | Negative tests. |

## Open questions

- Should the MVP ship a canonical invoice example in addition to the report
  example?
- Should batch processing have a dedicated helper, or is a user loop sufficient?
- Which examples are normative for documentation screenshots and fixtures?

## Related documents

- [Vision and scope](vision-and-scope.md)
- [Document IR](../specifications/document-ir.md)
- [Node catalog](../specifications/nodes.md)
- [SDK API](../specifications/sdk-api.md)
- [Testing](../development/testing.md)
