# ADR-0004: Immutable model and fluent builder

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The SDK needs an ergonomic construction API and a stable data representation.
A mutable model would make aliasing, validation timing, and cross-language parity
harder. A builder-only API would hide the IR and make deserialization and
advanced use cases awkward.

## Decision

Provide two layers:

- An immutable, serializable document model.
- A fluent builder that constructs the model.

`build()` returns an immutable snapshot. Python uses frozen dataclasses and
immutable tuples; TypeScript uses readonly properties and readonly arrays. Model
constructors are public and validated. The builder is the primary API.

The builder is mutable and not thread-safe. It is `PROPOSED` as an explicit
contract; the model immutability is `CONFIRMED`.

## Consequences

- Documents can be shared safely after construction.
- Serialization and deserialization have a clear target type.
- Parity tests can compare model serialization, not builder internals.
- The SDK has more types and more documentation.
- Builder mutation must not leak into a previously built document.
- Collection inputs must be copied.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Fluent builder only | IR is hidden; deserialization and advanced use are harder. |
| Data model plus functions | Transparent but verbose and less ergonomic. |
| Mutable fluent model | Aliasing and validation timing are harder to control. |
| Immutable builder with `with_*` methods | Ergonomic in some languages but verbose for report composition. |

## References

- `docs/specifications/sdk-api.md`
- `API-001` to `API-025`
- `IR-013` to `IR-015`
