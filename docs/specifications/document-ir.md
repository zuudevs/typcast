# Document IR

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-25

## Purpose

The document IR is the language-neutral JSON representation of a Typcast
document. It is the contract between the builder, serializer, validator,
emitter, and cross-language tests. Python and TypeScript models serialize to the
same IR for the same input.

The IR version is `1.0.0`, and the JSON Schema in `specs/schemas/` implements
this document. The repository version is still `0.1.0`, because no release has
been published yet. The release lane bumps the package manifests and the
changelog to the release tag, and the publisher writes the identity of that
tag into every published schema.

## Root shape

```json
{
  "schemaVersion": "1.0.0",
  "metadata": {
    "title": "Quarterly Report",
    "author": "Example Corp",
    "date": "2026-11-24"
  },
  "page": {
    "paper": "a4",
    "orientation": "portrait",
    "margin": {
      "top": { "value": 2, "unit": "cm" },
      "right": { "value": 2, "unit": "cm" },
      "bottom": { "value": 2, "unit": "cm" },
      "left": { "value": 2, "unit": "cm" }
    }
  },
  "contents": [
    {
      "type": "heading",
      "level": 1,
      "content": [{ "type": "text", "value": "Quarterly Report" }]
    },
    {
      "type": "paragraph",
      "content": [
        { "type": "text", "value": "Revenue grew by " },
        {
          "type": "bold",
          "content": [{ "type": "text", "value": "12%" }]
        },
        { "type": "text", "value": "." }
      ]
    }
  ],
  "modules": []
}
```

## Root fields

| Field | Type | Required | Constraint |
|---|---|---|---|
| `schemaVersion` | string | Yes | Semantic version, for example `1.0.0`. |
| `metadata` | object | Yes | See metadata fields. |
| `page` | object | Yes | See page fields. |
| `contents` | array of block | Yes | At least one block. |
| `modules` | array of module | No | Defaults to an empty array. |

The root object is closed. Unknown fields are rejected.

## Metadata

| Field | Type | Required | Constraint |
|---|---|---|---|
| `title` | string | Yes | Non-empty, at most 512 Unicode code points. |
| `author` | string | No | At most 512 Unicode code points. |
| `date` | string | No | ISO 8601 calendar date, `YYYY-MM-DD`. |

Metadata is intentionally small. Subject, keywords, language, and custom fields
are Post-MVP.

## Page

| Field | Type | Required | Constraint |
|---|---|---|---|
| `paper` | string | Yes | One of the values in `specs/catalogs/enums/paper-variants.csv`. |
| `orientation` | string | Yes | `portrait` or `landscape`. |
| `margin` | object | Yes | Top, right, bottom, and left lengths. |

The page object is not nested inside another page object. The current prototype
that produces `page.paper.paper` is not normative.

### Length

```json
{ "value": 2, "unit": "cm" }
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `value` | number | Yes | Finite, greater than or equal to zero, and inside the binary64 number domain of ECMAScript. |
| `unit` | string | Yes | `pt`, `mm`, `cm`, `in`, or `em`. |

Relative units `%` and `fr` are not part of the MVP. A future addition requires a
schema minor version and emitter support.

### Margin

| Field | Type | Required |
|---|---|---|
| `top` | length | Yes |
| `right` | length | Yes |
| `bottom` | length | Yes |
| `left` | length | Yes |

Builder defaults are 2.5 cm on all sides. Direct model construction requires all
four values.

## Blocks

Every block has a `type` discriminator. The MVP block types are:

| Type | Purpose |
|---|---|
| `heading` | Section heading with level 1 to 6. |
| `paragraph` | Paragraph containing inline spans. |
| `list` | Ordered or unordered list of inline span arrays. |
| `table` | Table with columns, header cells, and rows. |
| `image` | Image with alt text and optional caption. |
| `pageBreak` | Explicit page break. |
| `raw` | Verbatim Typst markup, code, or math. |

Block objects are closed. A block with an unknown `type` is invalid.

### Heading

```json
{
  "type": "heading",
  "level": 2,
  "content": [{ "type": "text", "value": "Revenue" }]
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `level` | integer | Yes | 1 to 6. |
| `content` | array of span | Yes | At least one span. |

### Paragraph

```json
{
  "type": "paragraph",
  "content": [{ "type": "text", "value": "A paragraph." }]
}
```

`content` is required and contains at least one span.

### List

```json
{
  "type": "list",
  "ordered": false,
  "items": [
    [{ "type": "text", "value": "First item" }],
    [{ "type": "text", "value": "Second item" }]
  ]
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `ordered` | boolean | Yes | `true` emits a numbered list. |
| `items` | array of span arrays | Yes | At least one item; each item has at least one span. |

Nested lists are Post-MVP.

### Table

```json
{
  "type": "table",
  "columns": [
    {
      "header": [{ "type": "text", "value": "Metric" }],
      "align": "left"
    },
    {
      "header": [{ "type": "text", "value": "Value" }],
      "align": "right"
    }
  ],
  "rows": [
    [
      [{ "type": "text", "value": "Revenue" }],
      [{ "type": "text", "value": "1,200" }]
    ]
  ]
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `columns` | array of column | Yes | At least one column. |
| `rows` | array of row | Yes | At least one row; every row has the same number of cells as `columns`. |

A column has `header` (array of spans, possibly empty) and `align` (`left`,
`center`, or `right`). A cell is an array of spans and may be empty. Table
captions are Post-MVP.

### Image

```json
{
  "type": "image",
  "path": "figures/revenue.png",
  "alt": "Revenue chart",
  "caption": [{ "type": "text", "value": "Figure 1" }],
  "width": { "value": 12, "unit": "cm" }
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `path` | string | Yes | Relative POSIX path; no absolute path or traversal. |
| `alt` | string | Yes | Non-empty accessibility description. |
| `caption` | array of span | No | At least one span if present. |
| `width` | length | No | Positive length. |

### Page break

```json
{ "type": "pageBreak" }
```

No additional fields are allowed.

### Raw block

```json
{
  "type": "raw",
  "format": "markup",
  "value": "#figure(image(\"logo.png\"), caption: [Logo])"
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `format` | string | Yes | `markup`, `code`, or `math`. |
| `value` | string | Yes | Non-empty, valid UTF-8, at most the configured raw size limit. |

The value is opaque to Typcast and is emitted verbatim. The default raw size
limit is 1 MiB and is configurable through `max_raw_bytes`.

## Inline spans

Every inline span has a `type` discriminator. The MVP span types are:

| Type | Purpose |
|---|---|
| `text` | Plain text. |
| `bold` | Bold content. |
| `italic` | Italic content. |
| `monospace` | Monospace content. |
| `link` | Link with display text and target. |
| `lineBreak` | Explicit line break. |
| `raw` | Verbatim inline Typst. |

### Text

```json
{ "type": "text", "value": "Revenue grew by " }
```

`value` is a non-empty string. Empty text spans are invalid; remove them instead.

### Emphasis

```json
{
  "type": "bold",
  "content": [{ "type": "text", "value": "12%" }]
}
```

`bold`, `italic`, and `monospace` have the same shape: a required `content`
array with at least one span. Emphasis may contain other spans, including links.

### Link

```json
{
  "type": "link",
  "href": "https://example.com/report",
  "content": [{ "type": "text", "value": "Report" }]
}
```

`href` is a non-empty URI string. `content` is required and contains at least one
span. The emitter escapes the URL and display text.

### Line break

```json
{ "type": "lineBreak" }
```

No additional fields are allowed.

### Raw inline

```json
{ "type": "raw", "format": "math", "value": "x^2 + y^2" }
```

Same constraints as the raw block. Raw inline is inserted verbatim.

## Modules

```json
{
  "modules": [
    { "path": "modules/report.typ", "alias": "report" },
    { "path": "modules/format.typ", "items": ["currency"] }
  ]
}
```

| Field | Type | Required | Constraint |
|---|---|---|---|
| `path` | string | Yes | Relative POSIX path; no absolute path or traversal. |
| `alias` | string | No | Identifier matching `^[A-Za-z_][A-Za-z0-9_]*$`. |
| `items` | array of string | No | Non-empty identifiers. |

`alias` and `items` are mutually exclusive. Module imports are emitted at the top
of the document, in declaration order. Remote modules are not supported.

## Serialization

- `to_json` MUST produce UTF-8 JSON with two-space indentation and a trailing
  newline.
- Object keys MUST follow the field order defined in this document.
- `from_json` MUST reject unknown fields, missing required fields, and
  unsupported schema versions.
- Round-trip `from_json(to_json(document))` MUST produce an equivalent document.
- JSON number formatting MUST be deterministic. Integers are emitted without a
  decimal point; non-integers use the shortest round-trippable representation.
- The numbers of a document live in the binary64 number domain of ECMAScript,
  because the canonical text follows the number format of that type. A value
  that the domain cannot hold exactly is rounded to the nearest representable
  value by both SDKs, and a value that overflows the domain is an error.
- Unicode is preserved as-is; Typcast does not normalize text.

## Validation rules

| Rule | Description |
|---|---|
| Required fields | Every field marked required must be present. |
| Closed objects | Unknown fields are errors. |
| Discriminator | `type` must be one of the supported values. |
| Table shape | Every row must have the same number of cells as `columns`. |
| Table alignment | `align` must be `left`, `center`, or `right`. |
| Length | Value must be finite and non-negative; unit must be supported. |
| Image width | The width of an image must be a positive length. |
| Number domain | Every number must be finite and must live in the binary64 domain of ECMAScript. |
| Text length | `title` and `author` hold at most 512 Unicode code points. |
| Image path | Must be relative, normalized, and inside `assetRoot`. |
| Module path | Must be relative, normalized, and inside `assetRoot`. |
| Module alias | Must be a valid identifier and unique within the document. |
| Raw size | Must not exceed the configured raw size limit. |
| Schema version | Major version must be supported; minor version must not exceed the supported minor. |

The rules are enforced by three layers. The current release implements the
first two layers only.

| Layer | Rules | State |
|---|---|---|
| Model and reader | Required fields, closed objects, discriminator, table alignment, length, image width, number domain, text length, module alias, raw value, schema version. | Implemented. |
| Validation engine | Table shape, module alias uniqueness, raw size. | Not implemented. |
| Asset layer | Image path, module path. | Not implemented. |

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| IR-001 | The root object MUST contain `schemaVersion`, `metadata`, `page`, and `contents`. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the reader rejects a missing required field. |
| IR-002 | `page` MUST contain `paper`, `orientation`, and `margin` without additional nesting. | IMPLEMENTED | The reader of both SDKs rejects an unknown field of the page object. |
| IR-003 | `contents` MUST be a non-empty array of typed blocks. | IMPLEMENTED | The constructor of both SDKs rejects empty contents, and the reader rejects a block without a supported discriminator. |
| IR-004 | Every block and span MUST have a supported `type` discriminator. | IMPLEMENTED | The reader rejects an unknown discriminator with `TYPCAST-VAL-0003`; the negative fixture `unknown-discriminator.json`. |
| IR-005 | Heading level MUST be an integer from 1 to 6. | IMPLEMENTED | The constructor of both SDKs rejects a level outside the range with `TYPCAST-VAL-0005`. |
| IR-006 | Table rows MUST match the column count. | CONFIRMED | Semantic validation test. |
| IR-007 | Table alignment MUST be `left`, `center`, or `right`. | IMPLEMENTED | The constructor of both SDKs rejects another value with `TYPCAST-VAL-0003`. |
| IR-008 | Length units MUST be `pt`, `mm`, `cm`, `in`, or `em`. | IMPLEMENTED | The constructor of both SDKs rejects another unit with `TYPCAST-VAL-0004`. |
| IR-009 | Image and module paths MUST be relative and traversal-safe. | CONFIRMED | Asset tests. |
| IR-010 | Module aliases MUST be unique identifiers. | CONFIRMED | Semantic validation test. |
| IR-011 | Raw values MUST be non-empty and valid UTF-8. | IMPLEMENTED | The constructor of both SDKs rejects an empty raw value, and the raw value is a Unicode string in both SDKs. |
| IR-012 | `schemaVersion` MUST be a semantic version. | IMPLEMENTED | The reader rejects a malformed or an unsupported version with `TYPCAST-IR-0002`; the negative fixtures `malformed-version.json`, `version-leading-zero.json`, and `unsupported-version.json`. |
| IR-013 | `to_json` MUST be deterministic across Python and TypeScript. | IMPLEMENTED | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; every shared fixture is written back byte for byte, including the fixture `large-number.json`. |
| IR-014 | `from_json` MUST reject unknown fields and unsupported versions. | IMPLEMENTED | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the negative fixtures of the manifest. |
| IR-015 | Round-trip serialization MUST preserve the document. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the round-trip cases. |
| IR-016 | The IR MUST NOT contain absolute paths or remote asset URLs. | CONFIRMED | Schema and asset tests. |
| IR-017 | The IR MUST NOT require a Typst compiler to be constructed or validated. | IMPLEMENTED | The SDKs depend on no compiler; the model and the contract tests run without a Typst installation. |
| IR-018 | The IR MUST remain language-neutral and contain no language-specific objects. | IMPLEMENTED | The shared fixtures under `tests/fixtures/documents/` are language-neutral JSON and are read by both SDKs. |
| IR-019 | The raw size limit MUST default to 1 MiB, be configurable through `max_raw_bytes`, and be documented. | CONFIRMED | Validation test and configuration review. |
| IR-020 | The IR MUST reserve `schemaVersion` major compatibility rules for future evolution. | CONFIRMED | Compatibility review. |
| IR-021 | Every number of the IR MUST live in the binary64 number domain of ECMAScript. | IMPLEMENTED | Both SDKs narrow a value to that domain and reject a value that overflows it; the number-domain cases of both SDKs and the fixture `large-number.json`. |
| IR-022 | The width of an image MUST be a positive length. | IMPLEMENTED | The constructor of both SDKs rejects a width of zero with `TYPCAST-VAL-0004`; the negative fixture `invalid-image-width.json`. |

## Open questions

- Should `metadata.author` be a string or an array of authors?
- Should `metadata.date` accept a full timestamp in addition to a calendar date?
- Should table cells support row spans or column spans in a later minor version?
- Should the raw size limit be configurable per document in addition to per
  configuration?

## Related documents

- [Node catalog](nodes.md)
- [Schema contract](schema.md)
- [SDK API](sdk-api.md)
- [Emitter](emitter.md)
- [Assets and modules](assets.md)
- [ADR-0017](../decisions/ADR-0017-resource-limits.md)
