# ADR-0014: Diagnostic warning policy

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The MVP defines a structured diagnostic taxonomy with `error`, `warning`, and
`info` severities. The earlier baseline left the warning behavior open: which
conditions warn, whether warnings fail a build, where warnings are returned,
and whether a caller can promote them to errors.

Undecided warning behavior causes cross-language drift, because Python and
TypeScript can easily disagree about whether a condition raises, returns a
diagnostic, or is silently ignored.

## Decision

Use a closed warning policy:

- Only three conditions warn in the MVP:
  1. The compiler adapter used `allow_unsupported_typst`.
  2. The Typst CLI emitted a warning.
  3. A deprecated public API was used.
- Every other condition is an error.
- Warnings never raise. `build()`, `to_typst()`, and `compile_pdf()` raise only
  for error diagnostics.
- `validate()` returns warnings and errors together, in document order.
- `CompileResult.diagnostics` contains the warnings produced during
  compilation, including compiler warnings.
- Warnings never fail a build, a test lane, or a release gate in the MVP.
- Warnings cannot be promoted to errors by configuration in the MVP.
- Python and TypeScript produce identical warnings for identical input.

## Consequences

- Warning behavior is part of the public contract and is covered by parity
  tests.
- The set of warning conditions is small and can grow only through a documented
  change.
- Applications that need strict behavior inspect `diagnostics` themselves.
- Promotion, warning configuration, and warning-specific exit codes are
  Post-MVP.
- The `info` severity stays reserved; it has no conditions in the MVP.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| No warnings at all | Compiler warnings would be lost, and the compiler severity would have no mapping. |
| Warnings fail the build | A compiler warning would block unrelated work and reduce trust in the diagnostic system. |
| Configurable warning severity | Adds configuration surface before the taxonomy is proven; deferred. |
| Warnings returned only from `compile_pdf()` | Builder-time warnings, such as deprecated API use, would be unobservable. |

## References

- `docs/specifications/diagnostics.md`
- `docs/specifications/sdk-api.md`
- `DIAG-011`
- `API-007`
