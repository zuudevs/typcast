# SDK API

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-28

## Purpose

This document defines the public API contract shared by the Python and
TypeScript SDKs. The API has two layers:

- An immutable document model that is serializable and language-neutral.
- A fluent builder that constructs the model ergonomically.

The builder is the primary API. Public model constructors are supported for
advanced use and deserialization. Both layers validate their inputs and produce
the same IR.

## Naming conventions

| Concept | Python | TypeScript |
|---|---|---|
| Methods and fields | `snake_case` | `camelCase` |
| Types and classes | `PascalCase` | `PascalCase` |
| Constants | `UPPER_SNAKE_CASE` | `UPPER_SNAKE_CASE` |
| JSON fields | `camelCase` | `camelCase` |

JSON field names are defined by the IR and do not change between languages.

## Public model types

| Type | Responsibility |
|---|---|
| `Document` | Root immutable document. |
| `Metadata` | Title, author, and date. |
| `Page` | Paper, orientation, and margin. |
| `Margin` | Top, right, bottom, and left lengths. |
| `Length` | Numeric value and unit. The value lives in the binary64 number domain of ECMAScript. `Length.cm(value)` returns a length in centimeters. |
| `Heading` | Heading block. |
| `Paragraph` | Paragraph block. |
| `ListBlock` | Ordered or unordered list block. |
| `Table` | Table block. |
| `TableColumn` | Header content and alignment. |
| `Image` | Image block. |
| `PageBreak` | Page break block. |
| `RawBlock` | Verbatim Typst block. |
| `Text` | Plain text span. |
| `Bold` | Bold span. |
| `Italic` | Italic span. |
| `Monospace` | Monospace span. |
| `Link` | Link span. |
| `LineBreak` | Line break span. |
| `RawSpan` | Verbatim inline Typst span. |
| `Module` | Module import declaration. |
| `Diagnostic` | Structured diagnostic. |
| `CompileResult` | PDF bytes or path, diagnostics, and compiler metadata. |
| `TypcastConfig` | Configuration of the validation engine. The compilation fields arrive with the compiler adapter. |

## Immutability

- `Document` and all model types are immutable.
- Python uses frozen dataclasses and immutable tuples.
- TypeScript uses readonly properties and readonly arrays.
- The builder is mutable and is not thread-safe or safe for concurrent use.
- `build()` returns an immutable snapshot. Later builder changes do not mutate a
  previously built document.
- Model constructors copy collection inputs so that caller mutation cannot
  change a model instance.

Builder mutability is `CONFIRMED` as an explicit contract: the builder is a
mutable convenience object, one builder produces one document at a time, and a
builder must not be shared across threads. Model immutability is `CONFIRMED`.

## Builder surface

### Python

```python
from typcast import DocumentBuilder, Length, bold, column

document = (
    DocumentBuilder()
    .title("Quarterly Report")
    .author("Example Corp")
    .date("2026-11-24")
    .page(paper="a4", orientation="portrait", margin=Length.cm(2.0))
    .heading(1, "Quarterly Report")
    .paragraph("Revenue grew by ", bold("12%"), ".")
    .bullet_list(["Revenue", "Cost", "Headcount"])
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
    .image(
        "figures/revenue.png",
        alt="Revenue chart",
        caption="Figure 1",
    )
    .page_break()
    .raw("#figure(image(\"logo.png\"), caption: [Logo])", format="markup")
    .module("modules/format.typ", items=["currency"])
    .build()
)
```

### TypeScript

```typescript
import { DocumentBuilder, Length, bold, column } from "typcast";

const document = new DocumentBuilder()
  .title("Quarterly Report")
  .author("Example Corp")
  .date("2026-11-24")
  .page({
    paper: "a4",
    orientation: "portrait",
    margin: Length.cm(2),
  })
  .heading(1, "Quarterly Report")
  .paragraph("Revenue grew by ", bold("12%"), ".")
  .bulletList(["Revenue", "Cost", "Headcount"])
  .table({
    columns: [
      column("Metric", "left"),
      column("Value", "right"),
    ],
    rows: [
      [["Revenue"], ["1,200"]],
      [["Cost"], ["800"]],
    ],
  })
  .image("figures/revenue.png", {
    alt: "Revenue chart",
    caption: "Figure 1",
  })
  .pageBreak()
  .raw("#figure(image(\"logo.png\"), caption: [Logo])", {
    format: "markup",
  })
  .module("modules/format.typ", { items: ["currency"] })
  .build();
```

## Builder methods

| Operation | Python | TypeScript |
|---|---|---|
| Metadata | `.title(value)`, `.author(value)`, `.date(value)` | `.title(value)`, `.author(value)`, `.date(value)` |
| Page | `.page(paper, orientation, margin)` | `.page({ paper, orientation, margin })` |
| Heading | `.heading(level, *content)` | `.heading(level, ...content)` |
| Paragraph | `.paragraph(*content)` | `.paragraph(...content)` |
| Bullet list | `.bullet_list(items)` | `.bulletList(items)` |
| Numbered list | `.numbered_list(items)` | `.numberedList(items)` |
| Table | `.table(columns, rows)` | `.table({ columns, rows })` |
| Image | `.image(path, alt, caption=None, width=None)` | `.image(path, { alt, caption, width })` |
| Page break | `.page_break()` | `.pageBreak()` |
| Raw block | `.raw(value, format="markup")` | `.raw(value, { format })` |
| Module | `.module(path, alias=None, items=None)` | `.module(path, { alias, items })` |
| Build | `.build(config=None)` | `.build(options?)` |

Builder content arguments accept strings or span objects. A string is normalized
to a `Text` span. This applies to headings, paragraphs, list items, table cells,
image captions, and link content.

### Span helpers

| Python | TypeScript | Result |
|---|---|---|
| `text(value)` | `text(value)` | Text span. |
| `bold(*content)` | `bold(...content)` | Bold span. |
| `italic(*content)` | `italic(...content)` | Italic span. |
| `monospace(*content)` | `monospace(...content)` | Monospace span. |
| `link(href, *content)` | `link(href, ...content)` | Link span. |
| `line_break()` | `lineBreak()` | Line break span. |
| `raw_inline(value, format)` | `rawInline(value, format)` | Raw inline span. |

### Table helpers

| Python | TypeScript | Result |
|---|---|---|
| `column(header, align="left")` | `column(header, align)` | Table column. |
| `cell(*content)` | `cell(...content)` | Table cell. |

A table row is a sequence of cells. A cell is a sequence of strings or spans. A
row with the wrong number of cells is rejected at build time.

### Builder behavior

- Every mutating method returns the builder, so a document is one chain of
  calls.
- The builder is mutable, one builder produces one document at a time, and a
  builder must not be shared across threads. `build()` returns an immutable
  snapshot, and a later call of the builder does not change a document that was
  already built.
- The builder copies the collections that it receives, so a caller cannot
  change a document with a list that the caller keeps.
- The builder applies the defaults of the node catalog before it creates the
  model: the paper `a4`, the orientation `portrait`, a margin of 2.5 cm on
  every side, an unordered bullet list, no module, and no caption and no width
  for an image.
- A string that is passed as content becomes a `Text` span, and a span is kept
  as it is. Two strings are never merged, because a merge would change the
  structure of the content.
- `Length.cm(value)` returns a length in centimeters. Every other unit is
  written with the constructor, because the contract names no factory for it.
- A single `Length` on `margin` is the margin of every side of the page, and a
  `Margin` names every side itself.
- The builder checks the type of its arguments itself and raises
  `ApiUsageError` with `TYPCAST-API-0001` and the phase `api`. The rules of a
  node stay with the constructors of the model and raise `ValidationError`
  with a code of the `TYPCAST-VAL-*` family.
- `build()` runs the validation engine and raises `ValidationError` when the
  engine reports an error. The error carries every error diagnostic of the
  document, in the order of the document, and its message is the message of the
  first diagnostic.
- `build()` takes the configuration of the validation engine, so the raw size
  limit of the build is the limit of the call. A call that names no
  configuration uses the default limit of the engine. The configuration is
  passed per call and is never stored in the document, so a later `validate()`
  of the document uses the default limit again.
- The builder checks the type of the configuration itself, because the
  configuration is an argument of a public method. An argument that is not a
  configuration raises `ApiUsageError` with `TYPCAST-API-0001`, the phase
  `api`, and the path `/build`.
- The builder reads the configuration before it does any work, so an invalid
  configuration is reported before a problem of the document. A limit that is
  not an integer that is finite and not negative raises `ConfigError` with
  `TYPCAST-CONFIG-0004`, the phase `config`, and the path `/max_raw_bytes`.
  Python checks the limit when the configuration is built, because the
  configuration is a frozen dataclass that checks its value; TypeScript checks
  the limit when the call resolves it. Both report the same diagnostic.

## Document methods

| Operation | Python | TypeScript |
|---|---|---|
| Validate | `document.validate(config=None)` | `document.validate(options?)` |
| Validate against the schema contract | `document.validate_schema()` | `document.validateSchema()` |
| Serialize to canonical JSON | `document.to_json()` | `document.toJSONString()` |
| Serialize to a JSON value | `document.to_dict()` | `document.toJSON()` |
| Deserialize from JSON | `Document.from_json(source)` | `Document.fromJSONString(source)` |
| Deserialize from a value | `Document.from_dict(value)` | `Document.fromJSON(value)` |
| Emit Typst | `document.to_typst(config=None)` | `document.toTypst(options?)` |
| Compile PDF | `document.compile_pdf(output_path=None, config=None)` | `document.compilePdf(options?)` |
| Write PDF | `document.write_pdf(path, config=None)` | `document.writePdf(path, options?)` |
| Schema version | `document.schema_version` | `document.schemaVersion` |

`validate()` returns a tuple or array of diagnostics and does not raise for
validation errors. `build()`, `to_typst()`, and `compile_pdf()` raise a typed
error when an error diagnostic is present. `to_json()` does not validate again:
the serialization of a built model writes the document as it is, because
ADR-0005 keeps the validation in the build step and in the reader.

The current release implements the model types of the list above, the
serialization rows of this table, `validate()`, `validate_schema()`, the error
hierarchy, the fluent builder with its span helpers and its table helpers, and
`to_typst()`. `compile_pdf()` and `write_pdf()` are part of the contract and
are not implemented yet.

## Typst emission

| Operation | Python | TypeScript |
|---|---|---|
| Emit Typst | `document.to_typst(config=None)` | `document.toTypst(options?)` |

The method returns the Typst source of the document as a string. The decision
is recorded in ADR-0028.

Behavior:

- The method runs the semantic validation engine before it emits, and raises
  `ValidationError` with every error diagnostic when the engine reports an
  error. The raw size limit is therefore enforced again before the emission.
- The configuration holds the limits of the validation run, it is passed per
  call, and it is never stored in the document.
- A configuration that is not a configuration object raises `ApiUsageError`
  with `TYPCAST-API-0001` and the path `/to_typst`.
- The method reads no file, invokes no compiler, and writes no file. The
  caller decides where the source goes.
- The output is deterministic. Two calls with the same document produce the
  same bytes.
- The output of both SDKs is identical, because both compare their output with
  the same golden file under `tests/fixtures/expected/`.
- A value that the emitter cannot represent raises `EmitError` with one
  diagnostic of the family `TYPCAST-EMIT-*` and the phase `emit`.

## Schema validation

The schema contract of the project is the normative data contract of the
document IR. Each SDK carries it as a generated source file, so a published
package holds the contract and needs no file of the repository at run time.

| Operation | Python | TypeScript |
|---|---|---|
| Validate a JSON value | `validate_schema(value)` | `validateSchema(value)` |
| Validate a document | `document.validate_schema()` | `document.validateSchema()` |

The function checks any JSON value, and the method checks the JSON value of the
document. Both return the diagnostics of the rules that the value breaks, they
report every broken rule at once, and they raise no error.

Behavior:

- The check is opt-in. The reader of the document IR keeps its own error
  contract, and the builder does not call the schema validation.
- The check is a layer of its own and is separate from the semantic engine of
  the next section. The two layers report different problems and can be called
  independently.
- A diagnostic of the check uses the family `TYPCAST-SCH-*` with the phase
  `validation`. `TYPCAST-SCH-0001` names an instance that breaks a rule of the
  schema, and `TYPCAST-SCH-0002` names a keyword of the schema that the
  validator does not implement.
- The details of a diagnostic name the keyword of the broken rule, so that a
  caller can act on the rule without reading the message.
- Both SDKs report the same diagnostics for the same value, in the same order.

The decision is recorded in ADR-0027.

## Validation

The semantic validation engine is a separate layer of both SDKs. It checks the
rules of the document IR that span more than one node:

| Rule | Diagnostic code |
|---|---|
| The shape of a table: every row holds as many cells as the table holds columns. | `TYPCAST-VAL-0007` |
| The uniqueness of a module alias within the document. | `TYPCAST-VAL-0008` |
| The size of a raw node: the bytes of the UTF-8 encoding of the value stay within the raw size limit. | `TYPCAST-VAL-0010` |

Behavior:

- `validate()` reports every problem it finds and raises no error for a
  semantic problem, so that a caller can show all of the problems at once.
- The diagnostics come in the order of the document: the blocks in the order of
  the contents, the spans in the order of their content, the rows of a table in
  the order of the table, and the modules in the order of their declaration.
- The configuration is passed per call and is never stored in the document.
- An invalid configuration raises `ConfigError` with `TYPCAST-CONFIG-0004`,
  the phase `config`, and the path `/max_raw_bytes`.

The engine is called explicitly through `validate()`. The builder calls it
again before it returns a document, with the configuration of the call, and the
emitter and the compiler adapter call it before they use a document.

## Configuration

The configuration of the validation engine holds the limits that the semantic
rules use. In this release it holds the raw size limit only, because the asset
root, the compiler path, and the timeout belong to the asset layer and the
compiler adapter, which arrive later.

### Python

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class TypcastConfig:
    max_raw_bytes: int = 1_048_576
```

### TypeScript

```typescript
interface TypcastOptions {
  maxRawBytes?: number;
}
```

The limit is a number of bytes, so it must be an integer that is finite and
that is not negative. A value that breaks the rule raises `ConfigError` with
`TYPCAST-CONFIG-0004`. The limit applies to every raw node on its own, and a
value of exactly the limit is valid. The same configuration is the argument of
`validate()` and of `build()`.

The asset root, the compiler path, the timeout, and the flag that allows an
unsupported Typst version arrive with the asset layer and the compiler adapter.
The asset root is required for compilation when the document contains images or
modules. It is not required to construct, to validate, or to serialize a
document.

## Compile result

```python
@dataclass(frozen=True)
class CompileResult:
    pdf: bytes | None
    path: Path | None
    diagnostics: tuple[Diagnostic, ...]
    compiler_version: str
    duration_ms: int
```

Behavior:

- If `output_path` is omitted, `pdf` contains the PDF bytes and `path` is `None`.
- If `output_path` is provided, the PDF is written atomically, `path` is set,
  and `pdf` is `None`.
- On failure, a `CompileError` is raised and no partial PDF is left at the
  requested output path.
- `diagnostics` may contain warnings even when compilation succeeds.
- `compiler_version` is the version reported by `typst --version`.
- `duration_ms` is wall-clock time for the compiler invocation.

TypeScript uses the same fields with `pdf: Uint8Array | null`, `path: string |
null`, and `durationMs: number`.

## Errors

| Error type | Code family | Raised when |
|---|---|---|
| `ApiUsageError` | `TYPCAST-API-*` | Builder or method is used with invalid argument types or state. |
| `ValidationError` | `TYPCAST-VAL-*` | A document violates the schema or semantic rules. |
| `SerializationError` | `TYPCAST-IR-*` | JSON cannot be parsed, serialized, or version-matched. |
| `EmitError` | `TYPCAST-EMIT-*` | The emitter cannot produce valid Typst for a valid model. |
| `CompileError` | `TYPCAST-COMPILER-*` | The compiler is missing, unsupported, times out, or fails. |
| `AssetError` | `TYPCAST-IO-*` | An asset is missing, unsafe, or unreadable. |
| `ConfigError` | `TYPCAST-CONFIG-*` | Configuration is invalid. |

All Typcast errors inherit from `TypcastError` and expose a `diagnostics`
collection. A single error may carry multiple diagnostics.

## Versioning and stability

- `typcast.__version__` and the TypeScript `VERSION` export MUST match the
  package version. The requirement `API-026` records the rule, and the
  repository gate compares every export with its manifest.
- The public API is stable from `1.0.0`.
- Adding a method or optional argument is a minor change.
- Removing or changing a public method, argument, field, or error code is a
  major change.
- Deprecations MUST be documented for at least one minor release before removal.
- Internal modules are not public API even if they are importable.

## Packaging and JavaScript consumption

- Python exports the public API from the `typcast` package root.
- TypeScript uses named exports and does not rely on a default export.
- The npm package MUST expose ESM and type declarations.
- The npm package is ESM-only for `1.0.0`. CommonJS support is `DEFERRED` to a
  later minor version and requires a separate consumer test.
- The JavaScript package is the compiled output of the TypeScript source; it is
  not a separate implementation.

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| API-001 | The SDK MUST expose an immutable document model and a fluent builder. | IMPLEMENTED | `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the surface cases of both SDKs, and the builder cases of `//tests/contract:builder_py` and `//tests/contract:builder_ts_test`. |
| API-002 | Builder methods MUST return the builder for chaining. | IMPLEMENTED | `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the chaining cases of both SDKs. |
| API-003 | `build()` MUST return an immutable snapshot. | IMPLEMENTED | `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the snapshot cases of both SDKs, which build a document, change the builder, and compare the canonical JSON. |
| API-004 | Model constructors MUST validate their inputs. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the constructor cases. |
| API-005 | Strings passed as content MUST be normalized to text spans. | IMPLEMENTED | `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the normalization cases of both SDKs, and the fixtures of `//tests/contract:builder_py` and `//tests/contract:builder_ts_test`. |
| API-006 | `build()` MUST raise `ValidationError` on error diagnostics. | IMPLEMENTED | `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the negative cases of both SDKs, and the fixtures of `//tests/contract:builder_py` and `//tests/contract:builder_ts_test`. |
| API-007 | `validate()` MUST return diagnostics without raising for validation errors. | IMPLEMENTED | `//packages/python/tests:validation_tests` and `//packages/typescript:validation_test_run`; the validation cases of both SDKs, and the fixtures of `//tests/contract:validation_py` and `//tests/contract:validation_ts_test`. |
| API-008 | `to_typst()` and `compile_pdf()` MUST validate again before use. | CONFIRMED | Validation test. |
| API-009 | `to_json()` MUST produce canonical JSON. | IMPLEMENTED | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; every shared fixture is written back byte for byte. |
| API-010 | `from_json()` MUST reject unknown fields and unsupported versions. | IMPLEMENTED | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the negative fixtures of the manifest. |
| API-011 | Round-trip serialization MUST preserve the document. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the round-trip cases. |
| API-012 | `compile_pdf()` MUST return a `CompileResult` with the documented fields. | CONFIRMED | Compiler API test. |
| API-013 | `compile_pdf()` MUST support bytes-only and path-only modes. | CONFIRMED | Compiler API test. |
| API-014 | `write_pdf()` MUST write atomically and MUST NOT leave partial output. | CONFIRMED | Failure test. |
| API-015 | Every error MUST inherit from `TypcastError` and expose diagnostics. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the error cases. |
| API-016 | Python and TypeScript MUST use the same diagnostic shape. | IMPLEMENTED | The `Diagnostic` shape of `typcast.diagnostics` and of `packages/typescript/src/diagnostics.ts`; the contract runners compare the code of every negative fixture. |
| API-017 | Python and TypeScript MUST produce identical `.typ` bytes for the same fixture. | IMPLEMENTED | `//tests/contract:typst_py` and `//tests/contract:typst_ts_test`; both runners compare their output with the same golden file under `tests/fixtures/expected/`. |
| API-018 | The package root MUST export the public API. | IMPLEMENTED | `//packages/python/tests:model_tests` imports every public type from `typcast`; `//packages/typescript:model_test_run` imports every public type from the package root. |
| API-019 | The npm package MUST expose ESM and type declarations. | CONFIRMED | Package test. |
| API-020 | The public API MUST be stable from `1.0.0`. | CONFIRMED | Release review. |
| API-021 | Deprecations MUST be documented for at least one minor release. | CONFIRMED | Release review. |
| API-022 | Internal modules MUST NOT be documented as public API. | CONFIRMED | API review. |
| API-023 | `asset_root` MUST be required only for compilation that needs assets. | CONFIRMED | API test. |
| API-024 | The builder MUST be documented as mutable, single-document, and not thread-safe. | IMPLEMENTED | The builder sections of this document, and `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the snapshot cases of both SDKs. |
| API-025 | The npm package MUST be ESM-only for `1.0.0`; CommonJS support is DEFERRED. | CONFIRMED | Package and consumer tests. |
| API-026 | The package root MUST export the version of the package, and the export MUST match the package manifest. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the version cases, and `//scripts:repository_checks` compares every export with its manifest. |
| API-027 | The validation configuration MUST be passed per call and MUST NOT be stored in the document; in this release it MUST hold the raw size limit only, and an invalid limit MUST raise `ConfigError` with `TYPCAST-CONFIG-0004`. | IMPLEMENTED | `//packages/python/tests:validation_tests` and `//packages/typescript:validation_test_run`; the configuration cases of both SDKs, and the `ConfigError` case of both SDKs. |
| API-028 | `build()` MUST take the validation configuration per call, MUST apply its raw size limit to the validation run of the build, and MUST NOT store it in the document; a configuration that is not a configuration object MUST raise `ApiUsageError` with `TYPCAST-API-0001` and the path `/build`. | IMPLEMENTED | `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the configuration cases of both SDKs, and the fixtures of `//tests/contract:builder_py` and `//tests/contract:builder_ts_test`. |
| API-029 | Each SDK MUST expose `validate_schema(value)` and `validateSchema(value)` and the method `Document.validate_schema()` and `Document.validateSchema()`, MUST report every rule that the value breaks without raising, and MUST keep the check separate from the reader and from the semantic engine. | IMPLEMENTED | `//packages/python/tests:schema_tests` and `//packages/typescript:schema_test_run`; the cases of both SDKs, and the fixtures of `//tests/contract:schema_py` and `//tests/contract:schema_ts_test`. |
| API-030 | Each SDK MUST expose `to_typst(config=None)` and `toTypst(options?)` on the document, MUST return the Typst source of the document as a string, MUST validate the document again before the emission, MUST raise `ValidationError` on error diagnostics, MUST NOT read assets or invoke the compiler, and MUST NOT store the configuration in the document. | IMPLEMENTED | `//packages/python/tests:emitter_tests` and `//packages/typescript:emitter_test_run`; the cases of both SDKs, and the runners `//tests/contract:typst_py` and `//tests/contract:typst_ts_test`. |

## Open questions

- Should `Document` expose a public constructor, or only `from_json` and the
  builder?
- Should `CompileResult.pdf` always be returned when an output path is set?
- Should the builder offer a `copy()` helper for reusing a partially built
  document?

## Related documents

- [Document IR](document-ir.md)
- [Node catalog](nodes.md)
- [Emitter](emitter.md)
- [Compiler adapter](compiler.md)
- [Diagnostics](diagnostics.md)
- [ADR-0004](../decisions/ADR-0004-immutable-model-and-builder.md)
- [ADR-0015](../decisions/ADR-0015-mutable-builder-contract.md)
- [ADR-0016](../decisions/ADR-0016-esm-only-npm-package.md)
- [ADR-0026](../decisions/ADR-0026-semantic-validation-engine-configuration-and-build.md)
- [ADR-0027](../decisions/ADR-0027-instance-validation-against-the-json-schema-contract.md)
- [ADR-0028](../decisions/ADR-0028-typst-emitter.md)
