# Vision and scope

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-24

## Problem

Developers who need a structured report often assemble it from application data,
templates, and ad hoc string concatenation. That approach has three recurring
problems:

- The document structure is not typed, so invalid shapes are discovered late.
- Python and JavaScript/TypeScript implementations drift in behavior and output.
- PDF generation depends on a toolchain that is difficult to reproduce and
  diagnose.

Typst provides a strong document language and compiler, but it is still a
language rather than a typed document API. Typcast fills that gap for a focused
set of report-oriented documents.

## Vision

Typcast is a typed document builder for Python and TypeScript that produces
deterministic Typst source and, when a supported Typst CLI is available, a PDF.
The same document model and the same fixtures drive both SDKs so that behavior
does not depend on the implementation language.

## Audience

| Audience | Need |
|---|---|
| Application developer | Generate a report or invoice from application data without hand-writing Typst. |
| Data engineer | Turn structured data into a repeatable PDF artifact. |
| Python or TypeScript library author | Embed document generation in an existing service or CLI. |
| Maintainer | Extend the node set without breaking cross-language parity. |

The MVP does not target non-developer end users, WYSIWYG editing, or academic
publishing workflows.

## Product principles

1. The document model is the contract. Builders are ergonomic constructors, not
   a second source of truth.
2. Cross-language parity is a product feature, not a testing detail.
3. Validation happens before emit and compile so users receive actionable
   diagnostics.
4. The compiler is an external dependency with an explicit compatibility range.
5. Raw Typst is an escape hatch, not a way to bypass the schema.
6. Generated artifacts are reproducible and never edited by hand.
7. The MVP is deliberately smaller than the Typst language.

## MVP scope

| Capability | Included | Notes |
|---|---|---|
| Python SDK | Yes | Typed model, builder, validation, emitter, compiler adapter. |
| TypeScript SDK | Yes | Same contract and fixtures as Python. |
| JavaScript consumption | Yes | Through compiled TypeScript output. |
| `.typ` output | Yes | Deterministic and golden-tested. |
| PDF output | Yes | Through an installed Typst CLI in the supported range. |
| Structured report nodes | Yes | Metadata, page, heading, paragraph, inline emphasis, list, table, image, link, page break, raw, modules. |
| Schema contract | Yes | JSON Schema draft 2020-12, closed objects, explicit required fields. |
| Packaging | Yes | Wheel, sdist, npm tarball, schema archive. |
| CI and release | Yes, after implementation | Three workflows, no publishing from pull requests. |
| Documentation | Yes | This document set and ADRs. |

## Non-goals for the MVP

The following are explicitly deferred:

- WYSIWYG or interactive document editing.
- Academic publishing features: math nodes, citations, bibliography,
  cross-references, footnotes, and figure numbering. Raw Typst remains an escape
  hatch for math, but Typcast provides no math node.
- Table of contents, headers, footers, and page numbering.
- Set and show rules exposed as first-class API.
- A bundled Typst binary or automatic compiler installation.
- Remote asset fetching.
- A plugin system or custom node registration.
- A hosted rendering service.
- Byte-for-byte PDF reproducibility across platforms.
- Signed artifacts and build provenance.

## Success criteria

| ID | Criterion | Status | Verification |
|---|---|---|---|
| PRD-001 | A developer can install `typcast` from PyPI and npm. | CONFIRMED | Install test in a clean environment. |
| PRD-002 | A developer can build a report with headings, paragraphs, lists, tables, images, links, and raw Typst. | CONFIRMED | Example and integration test. |
| PRD-003 | The same fixture produces identical `.typ` output in Python and TypeScript. | CONFIRMED | Cross-language parity test. |
| PRD-004 | A supported Typst CLI compiles the generated `.typ` to a valid PDF. | CONFIRMED | Compiler integration test. |
| PRD-005 | Invalid documents produce structured diagnostics with stable codes. | CONFIRMED | Negative tests and diagnostics parity test. |
| PRD-006 | The documentation gate passes for every changed document. | CONFIRMED | Documentation CI. |
| PRD-007 | The first stable release is `1.0.0` only after all MVP gates pass. | CONFIRMED | Release checklist. |

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| PRD-008 | Typcast MUST expose a typed document API in Python and TypeScript. | CONFIRMED | API contract review and parity tests. |
| PRD-009 | The MVP MUST emit `.typ` and compile PDF through an installed Typst CLI. | CONFIRMED | Golden and integration tests. |
| PRD-010 | The MVP MUST target structured reports, not general-purpose Typst authoring. | CONFIRMED | Scope review against node catalog. |
| PRD-011 | The MVP MUST support only the core report subset in `specifications/nodes.md`. | CONFIRMED | Node catalog review. |
| PRD-012 | Python and TypeScript MUST share the same document IR and fixtures. | CONFIRMED | Parity test. |
| PRD-013 | Documents MUST be validated before emit and before compile. | CONFIRMED | Validation tests. |
| PRD-014 | The SDK MUST NOT bundle or silently install a Typst binary in the MVP. | CONFIRMED | Compiler adapter review. |
| PRD-015 | The MVP MUST distribute Python to PyPI, TypeScript/JavaScript to npm, and schema artifacts to GitHub Releases. | CONFIRMED | Release checklist. |
| PRD-016 | The repository and published packages MUST use Apache-2.0. | CONFIRMED | License metadata check. |
| PRD-017 | The first stable release MUST be `1.0.0` and MUST NOT ship before all MVP gates pass. | CONFIRMED | Release checklist. |

## Assumptions

- The primary user is a developer writing code, not a non-developer editing a
  document.
- Typst CLI remains the only compiler backend in the MVP.
- Windows x64 is the current development environment, not the only supported
  platform.
- PyPI, npm, and GitHub Releases are the distribution channels.
- The document IR is language-neutral and serializable as JSON.

## Open questions

- Which exact report templates should ship as examples?
- Should the first public release be `1.0.0-alpha.N` before `1.0.0`?
- Which success metric has a hard threshold for release, beyond gate completion?

## Related documents

- [Use cases](use-cases.md)
- [Architecture overview](../architecture/overview.md)
- [Document IR](../specifications/document-ir.md)
- [Compatibility](../specifications/compatibility.md)
- [Release](../development/release.md)
