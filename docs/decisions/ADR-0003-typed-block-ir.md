# ADR-0003: Typed block sequence and inline spans

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The MVP targets structured reports. The document IR needs to be easy to
validate, serialize, and emit from both languages. A generic recursive node tree
would be flexible but difficult to constrain. A Typst call AST would be close to
the compiler but weak as a typed API.

The existing prototype also double-nests `paper` and `margin`, which makes the
page shape ambiguous.

## Decision

Use:

- A root object with `schemaVersion`, `metadata`, `page`, `contents`, and optional
  `modules`.
- A `page` object containing `paper`, `orientation`, and `margin` exactly once.
- `contents` as a sequence of typed blocks with a `type` discriminator.
- Inline content as a sequence of typed spans with a `type` discriminator.
- Raw Typst as explicit block and span nodes.
- Closed objects with explicit required fields.

## Consequences

- The schema can use `oneOf` and `const` discriminators.
- The emitter is a straightforward tree walk.
- Invalid structures are rejected early.
- The model is less flexible than a generic tree.
- New node types require schema and emitter work.
- Table cells and nested lists need explicit future decisions.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Recursive generic node tree | Harder to validate and emit; invalid shapes are easy. |
| Typst call AST | Too close to syntax; weak typed API and validation. |
| Flat text-only blocks | Insufficient for report formatting. |
| HTML-like tree | Adds a second document language and does not map cleanly to Typst. |

## References

- `docs/specifications/document-ir.md`
- `docs/specifications/nodes.md`
- `docs/specifications/emitter.md`
- `IR-001` to `IR-020`
- `NODE-001` to `NODE-025`
