# ADR-0023: Schema bundle validation and published identity

Status: Accepted
Date: 2026-11-24
Supersedes: ADR-0021
Superseded by: none

## Context

The schema sources use relative `$ref` values that point at generated files.
Those references resolve only after a Bazel build, because the referenced
schemas do not exist in the source tree.

The earlier baseline treated source-resolvable references as desirable. That
would require either checking generated output into the source tree or
restructuring the schema set, both of which duplicate or complicate the
generation pipeline.

The artifact that consumers actually use is the built bundle. ADR-0021 fixed the
bundle as the authoritative artifact set, but it also fixed the schema base URI
to a dedicated domain that the MVP does not operate. ADR-0022 replaces that
domain with versioned GitHub Raw URLs, so the base URI must change with it.

## Decision

- The built bundle is the authoritative artifact set. Schema validation runs
  against the bundle in `//specs/schemas:schema_tests`.
- Every `$ref` in the bundle must resolve inside the bundle. A dangling
  reference fails the test target.
- Source-tree `$ref` resolution is optional and is not a release requirement.
- The schema base URI is the versioned raw base
  `https://raw.githubusercontent.com/zuudevs/typcast/<VERSION>/specs/schemas/`,
  where `<VERSION>` is the release tag of the release that publishes the
  schema. The release build substitutes the version once, so templates and
  static schemas cannot drift.
- Every published schema declares an `$id` equal to its own versioned raw URL,
  so a relative `$ref` resolves to a sibling file at the same pinned tag.
- Generated schemas keep their relative paths so that the relative `$ref`
  values continue to resolve inside the bundle.
- The tagged commit contains the complete published bundle under
  `specs/schemas/`.

## Consequences

- The source tree stays clean, and there is one source of truth for each
  schema.
- Editors that cannot resolve build outputs show unresolved references; the
  bundle test is the authoritative check.
- The published bundle and the versioned raw URLs serve the same artifact set,
  so consumers see one consistent contract.
- The schema `$id` values become release-specific. The schema migration
  replaces the current placeholder identifiers with the versioned raw URLs
  before `1.0.0`.
- The schema test target must run on every pull request and on the release
  lane.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Check generated schemas into the source tree | Duplicates generated output and creates a second source of truth on the development branch. |
| Make the root schema self-contained with `$defs` | Possible later, but it conflicts with the modular schema layout for no MVP benefit. |
| Validate source files only | The source files are incomplete; the bundle is what consumers use. |
| A version-independent schema identifier | It does not resolve to a fetchable artifact, so a relative `$ref` cannot be followed by a consumer. |
| A `main` base URI | `main` is mutable and is a development reference, not a stable contract identity. |

## References

- `docs/specifications/schema.md`
- `docs/development/build.md`
- `SCH-002`, `SCH-007`, `SCH-008`, `SCH-009`
- `BUILD-015`
- `REL-030`
