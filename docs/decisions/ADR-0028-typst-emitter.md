# ADR-0028: The Typst emitter of the document IR

Status: Accepted
Date: 2026-11-28
Supersedes: none
Superseded by: none

## Context

The two SDKs could build a document, validate it, and serialize it to the
document IR, but they could not turn a document into Typst. The specification
of the emitter existed, and it named an output contract, an emission order, a
set of block forms, and a list of requirements, but no implementation existed.
A caller that wanted a `.typ` file had to write the translation of the IR to
Typst markup by itself, which meant that every caller repeated the same
escaping rules, produced different files, and had no way to test the result.

Several decisions of the emitter were open, and each of them changes the bytes
of the output:

- The shape of the public API: a method on the document, a free function, or a
  writer that takes a path.
- The escaping of a text that starts a line. Typst reads a hyphen at the start
  of a line as the marker of a list, so a paragraph whose text starts with a
  hyphen would change its meaning.
- The form of a monospace span. The raw text of Typst holds no escape
  sequence, so the escaping table of the node catalog cannot be applied inside
  it.
- The diagnostics of a failure. An emitter that meets a value it cannot
  represent needs a code and a phase, so that a caller can handle the failure
  without reading the message.

The SDKs are dependency-free by contract (`REPO-003`), and the emitter is a
pure function: it reads no asset, invokes no compiler, and writes no file. The
compiler adapter and the asset layer arrive in later releases, and they need
the output of the emitter, so the emitter comes first.

## Decision

Give both SDKs an emitter that turns a validated document into Typst source,
and keep the compiler adapter, the asset layer, and the writer out of it.

- The public API is the method `Document.to_typst(config=None)` in Python and
  `Document.toTypst(options?)` in TypeScript. The method returns the source as
  a string. The configuration holds the limits of the validation run, it is
  passed per call, and it is never stored in the document.
- The method runs the semantic validation engine before it emits, and raises
  `ValidationError` with every error diagnostic when the engine reports an
  error. The raw size limit is therefore enforced again before the emission,
  as `NODE-023` requires.
- The emitter is a pure function of the document. It reads no file, invokes no
  compiler, writes no file, and holds no state between two calls.
- The output follows the contract of `docs/specifications/emitter.md`: the fixed
  header, the module imports, the page setup, the document metadata, and the
  blocks in the order of the document. One blank line separates the sections,
  the output is UTF-8 without a byte order mark, the line endings are LF, and
  the output ends with exactly one newline.
- A text span escapes every character of the table of `nodes.md`. In addition,
  the emitter escapes a list marker at the start of a line when the marker
  could open a list: a hyphen or a plus that is followed by a space or that
  ends the value. The rule is context-sensitive, so the emitter applies it to
  the first span of a paragraph, of a table cell, of an image caption, and of
  the content of a link.
- A monospace span is emitted as the raw text of Typst. The raw text holds no
  escape sequence, so the content of a monospace span is emitted verbatim, and
  the escaping table of the node catalog does not apply inside it. A span of
  another type and a backtick cannot be represented in the raw text, so the
  emitter rejects them with `TYPCAST-EMIT-0003` and returns no partial output.
- The emitter dispatches on the `type` discriminator of a node. A block or a
  span of an unknown type is rejected with `TYPCAST-EMIT-0002`, and an
  invariant of the model that does not hold is rejected with
  `TYPCAST-EMIT-0001`.
- The diagnostics of the emitter use the family `TYPCAST-EMIT-*` with the
  phase `emit`. The codes are the ones that the diagnostics specification
  already reserved for the emitter, so no new number is needed.
- The golden files are shared. Every valid document of the shared set has a
  golden file under `tests/fixtures/expected/`, and both SDKs compare their
  output with that file byte for byte. A drift in either SDK fails one of the
  two contract runners.

## Consequences

- A caller can turn a document into Typst with the package it already
  installs, and the result is the same in both SDKs, because both compare
  their output with the same golden file.
- The escaping rules live in one place, in the emitter of each SDK, and the
  node catalog names the characters they cover.
- A document that cannot be represented in Typst fails with a diagnostic of
  the emitter instead of producing a file that the compiler rejects later.
- The emitter holds no configuration of its own. A caller that needs an asset
  root or a compiler path configures those in the asset layer and the compiler
  adapter, which arrive later.
- The raw text of Typst cannot hold an escape sequence, so a monospace span
  that holds a backtick is rejected. A caller that needs a backtick in a
  monospace span must use a raw node, which the IR keeps opaque.
- The emitter is a second implementation of the block forms of the
  specification, and it can drift from it. The drift is caught by the golden
  files, because a change of the output changes the golden file and the review
  of that change explains it.
- The emitter writes nothing, so the caller decides where the source goes.
  The writer that writes a file atomically arrives with the compiler adapter.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| A template engine that renders the document | It would add a dependency to two packages that carry none, and it would hide the escaping rules of the node catalog in the template. |
| A writer that takes a path and writes the file | The emitter would then own the file system, and the rule that the emitter reads no file and writes no file would be lost. The caller decides where the source goes. |
| Escaping the content of a monospace span with the text table | The raw text of Typst holds no escape sequence, so a backslash is a literal backslash and the escaped characters would appear in the output. |
| A code block of Typst for a monospace span | It changes the layout and the meaning of a span: a code block is a block, and a monospace span is inline. |
| Dropping the content of a monospace span that holds a backtick | It would silently change the document. The emitter rejects the value instead. |
| One golden file per SDK | A drift between the two SDKs would stay invisible until a caller compared the files. One golden file for both makes the drift a failing test. |
| Emitting the date of the run in the header | It would change the output on every run and would make the golden files change on every release. |

## References

- `docs/specifications/emitter.md`
- `docs/specifications/nodes.md`
- `docs/specifications/sdk-api.md`
- `docs/specifications/diagnostics.md`
- `EMIT-001` to `EMIT-024`, `API-017`, `API-030`, `DIAG-020`, `NODE-016`,
  `NODE-023`, `TEST-035`
- [ADR-0002](ADR-0002-hybrid-schema-and-builders.md)
- [ADR-0003](ADR-0003-typed-block-ir.md)
- [ADR-0005](ADR-0005-two-phase-validation-and-diagnostics.md)
- [ADR-0012](ADR-0012-explicit-asset-root-and-raw.md)
- [ADR-0026](ADR-0026-semantic-validation-engine-configuration-and-build.md)
