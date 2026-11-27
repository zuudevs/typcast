# ADR-0025: Catalog-driven enum constants in the SDKs

Status: Accepted
Date: 2026-11-28
Supersedes: none
Superseded by: none

## Context

The catalog `specs/catalogs/enums/paper-variants.csv` is the source of truth of
the paper variants of the document IR. The JSON Schema of a page names the
variants, and the model of a page must reject a value that the catalog does
not name.

The values must reach the SDK in a way that cannot drift from the catalog, and
the SDK must stay usable outside the repository. A published wheel or npm
tarball holds no catalog file, and a package must not read a file of the
repository at runtime.

ADR-0002 decided that the catalog is normative for the document data and that
types and validators may be generated where practical. It did not decide how
a catalog reaches an SDK that enforces it at runtime.

## Decision

Expand a column of a CSV catalog into a constant of the source of an SDK at
build time.

- The tool `//tools/enumgen:typcast_enumgen` reads a CSV catalog and writes a
  source file of the Python SDK or of the TypeScript SDK.
- The Starlark rule `typcast_enum_source` in `bazel/enumgen.bzl` calls the
  tool. The catalog is the only input of the rule, so a change of the catalog
  changes the source of the SDK in the same build.
- The generated file is a build output under `bazel-bin/`. It is never
  committed, because `BUILD-009` forbids a committed generated artifact.
- The values keep the order of the catalog, and the diagnostic of a rejected
  value names them in that order.
- The tool reads no file of the SDK, and it imports no SDK code, so the SDKs
  and the tool stay independent of each other.
- A single-node value constraint that a catalog owns belongs to the model of
  the node, like the orientation of a page. The model of a page rejects a
  paper value that the catalog does not name, with `TYPCAST-VAL-0003`.

## Consequences

- The catalog stays the single source of truth of a public enum, and neither
  SDK holds a hand-written copy of it.
- A change of the catalog is a contract change that reaches both SDKs in one
  build, and the cross-language fixtures prove that both SDKs agree.
- The package of an SDK must carry the generated file. The packaging targets
  build the SDK from the output of the build, so they take the generated file
  with them.
- The generator is a second build tool next to the schema generator, and the
  two read a CSV catalog the same way.
- The values of a catalog that grows large stay in the source of the SDK, so
  the diagnostic of a rejected value names them all.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Reading the CSV at runtime | A published package holds no catalog file, and the SDK must not depend on the layout of the repository. |
| A hand-written constant in each SDK | The copy drifts from the catalog, and the drift is invisible until a document is rejected. |
| Validating the value against the JSON Schema only | The instance validation of the schema is not implemented yet, and it would reject a whole document instead of the value of one node. |
| Generating the constant from the JSON Schema of the page | The schema is itself generated from the catalog, so the catalog is the shorter and the more direct path. |

## References

- `docs/specifications/document-ir.md`
- `docs/architecture/repository.md`
- `docs/development/build.md`
- `IR-025`, `BUILD-023`, `REPO-013`
- [ADR-0002](ADR-0002-hybrid-schema-and-builders.md)
- [ADR-0024](ADR-0024-semantic-validation-engine-and-configuration.md)
