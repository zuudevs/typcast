# ADR-0005: Two-phase validation and structured diagnostics

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

Validation can run eagerly on every builder call, at `build()`, before emit, or
only in the compiler. Each choice affects feedback speed, partial construction,
and cross-language parity.

Free-form error messages are easy to produce but unstable for programmatic
handling. The compiler also produces diagnostics that need a consistent mapping.

## Decision

Use two-phase validation:

- Validate at `build()`.
- Validate again before emit and compile.
- Deserialization validates its input; serialization of an already-built model
  does not re-validate.

Use structured diagnostics with:

- Stable namespaced codes.
- Severity and phase.
- JSON Pointer paths.
- Compiler source locations.
- JSON-serializable details.
- A stable cause identifier.

Python and TypeScript expose the same diagnostic shape and error hierarchy.

## Consequences

- Invalid documents are caught early.
- Deserialized or externally modified models are checked again.
- Error codes become public API and must follow SemVer.
- A code catalog and parity tests are required.
- Eager validation and compiler-only validation are rejected.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Eager validation on every call | Partial construction is awkward and overhead is higher. |
| Lazy result object only | Errors arrive late and invalid models can spread. |
| Compiler-only validation | The schema contract is not enforced; diagnostics are poor. |
| Free-form errors | Not stable for automation or parity. |

## References

- `docs/specifications/diagnostics.md`
- `docs/specifications/sdk-api.md`
- `DIAG-001` to `DIAG-012`
- `API-006` to `API-016`
