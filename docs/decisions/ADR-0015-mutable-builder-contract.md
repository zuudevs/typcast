# ADR-0015: Mutable builder contract

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The document model is immutable in both languages. The builder could follow the
same rule, or it could stay mutable for ergonomics. The earlier baseline
marked builder mutability as proposed.

A mutable builder is easier to use for report composition, where a document is
assembled step by step. It also introduces aliasing questions: whether a
builder can be shared, whether a built document can change afterward, and
whether concurrent use is safe.

## Decision

Keep the builder mutable and state the contract explicitly:

- The builder is a mutable convenience object.
- One builder produces one document at a time.
- `build()` returns an immutable snapshot; later builder calls do not change an
  already built document.
- Model constructors copy collection inputs, so caller mutation cannot change
  a model instance.
- The builder is not thread-safe and must not be shared across threads.
- A builder that needs to be reused is copied by the caller; the SDK does not
  provide a `copy()` helper in the MVP.

The model remains immutable. This ADR confirms the contract; it does not
change the model decision in ADR-0004.

## Consequences

- Builder usage is idiomatic in Python and TypeScript.
- Thread safety is explicitly out of scope and must be documented in the API
  reference.
- Cross-language parity is unaffected, because the builder is not part of the
  serialized contract.
- A future `copy()` helper is additive and does not require a major version.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Immutable builder with `with_*` methods | Verbose for report composition and awkward in Python. |
| Shared global builder | Breaks isolation and makes concurrency unsafe in a subtle way. |
| Thread-safe builder with locking | Adds cost and complexity for a use case the MVP does not target. |

## References

- `docs/specifications/sdk-api.md`
- `API-001`, `API-002`, `API-003`, `API-024`
- `ADR-0004`
