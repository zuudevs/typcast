# ADR-0021: Schema bundle validation

Status: Superseded
Date: 2026-11-24
Supersedes: none
Superseded by: ADR-0023

> Superseded by
> [ADR-0023](ADR-0023-schema-bundle-validation.md). The bundle validation rules
> are restated unchanged, and the schema base URI now uses the versioned raw
> base instead of a dedicated domain.

## Context

The schema sources use relative `$ref` values that point at generated files.
Those references resolve only after a Bazel build, because the referenced
schemas do not exist in the source tree.

The earlier baseline treated source-resolvable references as desirable. That
would require either checking generated output into the source tree or
restructuring the schema set, both of which duplicate or complicate the
generation pipeline.

The artifact that consumers actually use is the built bundle, published in the
release archive and referenced by the canonical schema domain.

## Decision

- The built bundle is the authoritative artifact set. Schema validation runs
  against the bundle in `//specs/schemas:schema_tests`.
- Every `$ref` in the bundle must resolve inside the bundle. A dangling
  reference fails the test target.
- Source-tree `$ref` resolution is optional and is not a release requirement.
- The schema base URI is `https://schemas.typcast.dev/`, defined once in the
  schema build rules so that templates and static schemas cannot drift.
- Generated schemas keep their relative paths so that the relative `$ref`
  values continue to resolve inside the bundle.

## Consequences

- The source tree stays clean, and there is one source of truth for each
  schema.
- Editors that cannot resolve build outputs show unresolved references; the
  bundle test is the authoritative check.
- The published archive and the canonical domain serve the same artifact set,
  so consumers see one consistent contract.
- The schema test target must run on every pull request and on the release
  lane.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Check generated schemas into the source tree | Duplicates generated output and creates a second source of truth. |
| Make the root schema self-contained with `$defs` | Possible later, but it conflicts with the modular schema layout for no MVP benefit. |
| Validate source files only | The source files are incomplete; the bundle is what consumers use. |

## References

- `docs/specifications/schema.md`
- `docs/development/build.md`
- `SCH-007`, `SCH-008`, `SCH-009`
- `BUILD-015`
