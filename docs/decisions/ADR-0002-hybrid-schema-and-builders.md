# ADR-0002: Hybrid schema and idiomatic builders

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The repository has four potential sources of truth:

1. JSON Schema templates and CSV catalogs.
2. Static JSON Schema files.
3. Generated schemas in `bazel-bin`.
4. The SDK models, which do not exist yet.

Generating the entire public API from JSON Schema would produce a rigid builder
and would still not describe emitter semantics. Letting the SDK model become the
source of truth would make cross-language drift likely.

## Decision

Use a hybrid contract:

- JSON Schema is normative for document data, serialization, and validation.
- Python and TypeScript models and builders are written by hand for idiomatic
  APIs.
- Types and validators may be generated where practical.
- Emitter and builder behavior are defined by shared conformance fixtures.
- Cross-language parity tests compare the same JSON input and the same expected
  `.typ` output.

## Consequences

- The data contract is language-neutral.
- Builders remain ergonomic and can follow language conventions.
- Two implementations must be maintained.
- Parity tests are mandatory, not optional.
- Schema limitations do not automatically become API limitations.
- A behavioral contract is needed for defaults, validation timing, error codes,
  and raw content.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Full schema-first code generation | JSON Schema cannot describe emitter semantics; the API would be rigid. |
| Code-first with generated schema | Cross-language drift and a harder neutral contract. |
| Neutral IDL or DSL | Too much upfront cost and risk of over-engineering for the MVP. |
| Single shared runtime | Not practical across Python and TypeScript. |

## References

- `docs/specifications/schema.md`
- `docs/specifications/sdk-api.md`
- `docs/specifications/emitter.md`
- `SCH-001` to `SCH-020`
- `API-001` to `API-025`
