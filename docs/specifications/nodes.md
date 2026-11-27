# Node catalog

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-25

## Purpose

This catalog defines the block and inline span types in the MVP, their
constraints, and their Typst mapping. The JSON shape is defined in
`document-ir.md`; this document defines semantics and emission behavior.

## Block types

| Type | Children | Required fields | Typst mapping |
|---|---|---|---|
| `heading` | Inline spans | `level`, `content` | `=` repeated by level, followed by content. |
| `paragraph` | Inline spans | `content` | Markup paragraph separated by a blank line. |
| `list` | Inline span arrays | `ordered`, `items` | `-` or `+` list markers. |
| `table` | Columns and cells | `columns`, `rows` | `#table(...)` with `table.header`. |
| `image` | Caption spans | `path`, `alt` | `#figure(image(...), caption: [...])`. |
| `pageBreak` | None | None | `#pagebreak()`. |
| `raw` | None | `format`, `value` | Verbatim insertion. |

## Inline span types

| Type | Children | Required fields | Typst mapping |
|---|---|---|---|
| `text` | None | `value` | Escaped markup text. |
| `bold` | Inline spans | `content` | `*content*`. |
| `italic` | Inline spans | `content` | `_content_`. |
| `monospace` | Inline spans | `content` | Backtick-delimited content. |
| `link` | Inline spans | `href`, `content` | `#link("href")[content]`. |
| `lineBreak` | None | None | `#linebreak()`. |
| `raw` | None | `format`, `value` | Verbatim insertion. |

The JSON Schema in `specs/schemas/definitions/node.schema.json` implements this
catalog. It holds one union branch per block type and per inline span type,
each with a `type` discriminator and a `const` value, and it rejects an unknown
type. The schema enforces the constraints that JSON Schema can express. The
semantics below stay with the SDK.

## Defaults

Defaults are applied by the builder before the immutable model is created. They
are not implicit in the emitter.

| Field | Default |
|---|---|
| `page.paper` | `a4` |
| `page.orientation` | `portrait` |
| `page.margin` | 2.5 cm on all sides |
| `list.ordered` | `false` when the builder method is `bullet_list` |
| `modules` | Empty array |
| `image.width` | Unset; Typst determines the width |
| `image.caption` | Unset |

Direct model construction requires all fields that the schema marks required.
The builder may supply defaults for convenience.

## Heading semantics

- Level 1 is the document title level, but Typcast does not enforce a single
  level-1 heading.
- Levels 2 to 6 are section headings.
- Heading numbering, labels, and references are Post-MVP.
- A heading with empty content is invalid.

Typst mapping:

```typst
= Heading level 1
== Heading level 2
```

## Paragraph semantics

- A paragraph contains one or more inline spans.
- Consecutive paragraphs are separated by a blank line.
- Paragraph indentation and justification are compiler defaults in the MVP.
- A paragraph with only a line break is valid but discouraged.

## List semantics

- `ordered: false` emits bullet items.
- `ordered: true` emits numbered items.
- Items are emitted in order.
- Nested lists are Post-MVP.
- An item with empty content is invalid.

Typst mapping:

```typst
- First item
- Second item
```

```typst
+ First item
+ Second item
```

## Table semantics

- `columns` defines the number of columns, header content, and alignment.
- `rows` contains cell arrays in row-major order.
- Every row must have exactly one cell per column.
- Header cells are emitted with `table.header`.
- Cell content is inline spans and may be empty.
- Table captions, merged cells, row spans, and column spans are Post-MVP.
- Numeric alignment is achieved with `align: right`; Typcast does not parse
  numbers.

Typst mapping:

```typst
#table(
  columns: 2,
  align: (left, right),
  table.header([Metric], [Value]),
  [Revenue], [1,200],
  [Cost], [800],
)
```

## Image semantics

- `path` is relative to `assetRoot` and uses `/` separators in the IR.
- `alt` is required for accessibility.
- `caption` is optional and accepts inline spans.
- `width` is optional; when present, it is emitted as a length.
- Images are emitted inside a `figure` so that captions are associated with the
  image.
- Remote images are not supported.
- Image dimensions, fit, and scaling are compiler defaults in the MVP.

Typst mapping:

```typst
#figure(
  image("figures/revenue.png", alt: "Revenue chart", width: 12cm),
  caption: [Figure 1],
)
```

If the supported Typst version does not accept the `alt` parameter, the adapter
MUST report a compatibility diagnostic rather than silently dropping the
accessibility text.

## Page break semantics

- A page break is a block-level explicit break.
- It does not create an empty page by itself.
- Multiple consecutive page breaks are allowed but may produce blank pages.

Typst mapping:

```typst
#pagebreak()
```

## Raw semantics

- `format: "markup"` inserts Typst markup.
- `format: "code"` inserts Typst code.
- `format: "math"` inserts Typst math.
- Raw content is opaque to Typcast. It is not parsed, normalized, or escaped.
- Raw content is trusted input. Applications must not pass untrusted raw Typst.
- A raw block is separated from surrounding blocks by newlines.
- A raw inline span is inserted at its position without surrounding newlines.
- Empty raw content is invalid.
- The default maximum size is 1 MiB per raw node, configurable through
  `max_raw_bytes`. The limit is enforced during validation at `build()` and
  again before emission.

## Inline text semantics

- Text is UTF-8 and preserved without Unicode normalization.
- Empty text spans are invalid.
- Leading and trailing spaces are preserved.
- Typst markup characters are escaped by the emitter.
- The emitter MUST NOT concatenate adjacent text spans in a way that changes
  visible content; it MAY preserve them as separate escaped segments.

## Emphasis semantics

- Bold, italic, and monospace may nest.
- Emphasis content must contain at least one span.
- The emitter must escape delimiters inside the content.
- Underline, strike-through, color, highlight, and font size are Post-MVP.

## Link semantics

- `href` is a non-empty URI string.
- Display content is required.
- The emitter escapes quotes and backslashes in the URL.
- Link validation does not fetch the target.
- Relative links are allowed only if the application resolves them; Typcast does
  not rewrite them.
- Link checking is a documentation concern, not a document validation concern.

## Line break semantics

- A line break is an inline span.
- It emits `#linebreak()`.
- A line break inside a heading is allowed but discouraged.

## Escaping rules

The emitter escapes the following characters in text spans:

| Character | Escape |
|---|---|
| `\` | `\\` |
| `#` | `\#` |
| `*` | `\*` |
| `_` | `\_` |
| `` ` `` | `` \` `` |
| `$` | `\$` |
| `[` | `\[` |
| `]` | `\]` |
| `<` | `\<` |
| `>` | `\>` |
| `@` | `\@` |

A hyphen at the beginning of a line is escaped when it could be interpreted as a
list marker. The emitter is responsible for context-sensitive escaping.

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| NODE-001 | The MVP MUST support exactly the block types listed in this catalog. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the model holds the seven block types of this catalog and no other. |
| NODE-002 | The MVP MUST support exactly the inline span types listed in this catalog. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the model holds the seven inline span types of this catalog and no other. |
| NODE-003 | Heading levels MUST be integers from 1 to 6. | IMPLEMENTED | The constructor of both SDKs rejects another level with `TYPCAST-VAL-0005`. |
| NODE-004 | Headings and paragraphs MUST reject empty content. | IMPLEMENTED | The constructor of both SDKs rejects empty content with `TYPCAST-VAL-0006`. |
| NODE-005 | Lists MUST support ordered and unordered modes. | CONFIRMED | Emitter test. |
| NODE-006 | Nested lists MUST be rejected in the MVP. | CONFIRMED | Negative test. |
| NODE-007 | Tables MUST support header rows and per-column alignment. | CONFIRMED | Emitter test. |
| NODE-008 | Table rows MUST match the column count. | CONFIRMED | Semantic validation test. |
| NODE-009 | Tables MUST NOT support merged cells in the MVP. | CONFIRMED | Schema review. |
| NODE-010 | Images MUST require alt text. | IMPLEMENTED | The constructor of both SDKs requires a non-empty `alt` value. |
| NODE-011 | Images MUST support an optional caption. | IMPLEMENTED | The model of both SDKs holds an optional caption, and the canonical JSON omits the field when it is absent. |
| NODE-012 | Images MUST NOT support remote URLs. | CONFIRMED | Asset test. |
| NODE-013 | Page breaks MUST emit `#pagebreak()`. | CONFIRMED | Golden test. |
| NODE-014 | Raw content MUST be emitted verbatim. | CONFIRMED | Golden test. |
| NODE-015 | Raw content MUST NOT be escaped or parsed. | CONFIRMED | Golden test. |
| NODE-016 | Text spans MUST be escaped according to the table above. | CONFIRMED | Escaping test. |
| NODE-017 | Emphasis spans MUST be nestable. | CONFIRMED | Emitter test. |
| NODE-018 | Links MUST emit display text and a URL. | CONFIRMED | Emitter test. |
| NODE-019 | Line breaks MUST emit `#linebreak()`. | CONFIRMED | Golden test. |
| NODE-020 | The emitter MUST reject unknown node types. | CONFIRMED | Negative test. |
| NODE-021 | The emitter MUST preserve block order. | CONFIRMED | Golden test. |
| NODE-022 | The emitter MUST preserve span order. | CONFIRMED | Golden test. |
| NODE-023 | The raw size limit MUST be enforced during validation at `build()` and again before emit. | CONFIRMED | Validation test. |
| NODE-024 | The node catalog MUST be extensible without changing existing node semantics. | CONFIRMED | Schema compatibility review. |
| NODE-025 | The node catalog MUST NOT include math, citation, TOC, footnote, or header/footer nodes in the MVP. | CONFIRMED | Scope review. |

## Open questions

- Should table cells allow block content, or only inline spans, in a future
  version?
- Should images support `height`, `fit`, or `scaling` in the MVP?
- Should headings support explicit labels for future cross-references?

## Related documents

- [Document IR](document-ir.md)
- [Emitter](emitter.md)
- [Assets and modules](assets.md)
- [Testing](../development/testing.md)
- [ADR-0017](../decisions/ADR-0017-resource-limits.md)
