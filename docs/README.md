# Typcast documentation

Status: living index
Last updated: 2026-11-25

This directory contains the product, architecture, contract, and engineering
documentation for Typcast. The documents describe the approved MVP baseline. They
do not claim that the builder, the emitter, the compiler adapter, the packaging,
or the CI workflows are implemented.

## Reading order

1. `product/vision-and-scope.md`
2. `product/use-cases.md`
3. `architecture/overview.md`
4. `architecture/repository.md`
5. `specifications/document-ir.md`
6. `specifications/nodes.md`
7. `specifications/schema.md`
8. `specifications/sdk-api.md`
9. `specifications/emitter.md`
10. `specifications/compiler.md`
11. `specifications/diagnostics.md`
12. `specifications/assets.md`
13. `specifications/compatibility.md`
14. `development/build.md`
15. `development/testing.md`
16. `development/benchmarking.md`
17. `development/ci-cd.md`
18. `development/release.md`
19. `development/security.md`
20. `development/documentation.md`
21. `governance/contributing.md`
22. `requirements/traceability.md`

Architecture decisions are recorded in `decisions/`. The decision index is
`decisions/README.md`. The repository also carries the root-level policy files
`LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
`CHANGELOG.md`, `.gitattributes`, and `.editorconfig`.

## Document map

| No | Document | Scope | Status |
|---|---|---|---|
| 1 | [Vision and scope](product/vision-and-scope.md) | Product problem, audience, MVP boundary, success metrics | CONFIRMED |
| 2 | [Use cases](product/use-cases.md) | Report, invoice, documentation, and data-driven journeys | CONFIRMED |
| 3 | [Architecture overview](architecture/overview.md) | System context, components, data flow, trust boundaries | CONFIRMED |
| 4 | [Repository architecture](architecture/repository.md) | Module boundaries, dependency rules, Bazel layout | CONFIRMED |
| 5 | [Document IR](specifications/document-ir.md) | Normative document shape and serialization | CONFIRMED |
| 6 | [Node catalog](specifications/nodes.md) | Block and inline span semantics | CONFIRMED |
| 7 | [Schema contract](specifications/schema.md) | Schema conventions, validation, migration | CONFIRMED |
| 8 | [SDK API](specifications/sdk-api.md) | Shared API contract, Python and TypeScript surfaces | CONFIRMED |
| 9 | [Emitter](specifications/emitter.md) | Deterministic `.typ` generation | CONFIRMED |
| 10 | [Compiler adapter](specifications/compiler.md) | Typst discovery, version check, execution, workspace | CONFIRMED |
| 11 | [Diagnostics](specifications/diagnostics.md) | Error taxonomy, codes, mapping | CONFIRMED |
| 12 | [Assets and modules](specifications/assets.md) | Path resolution, module imports, security | CONFIRMED |
| 13 | [Compatibility](specifications/compatibility.md) | Platform, runtime, compiler, and version matrix | CONFIRMED |
| 14 | [Build](development/build.md) | Bazel, code generation, reproducibility | IMPLEMENTED / OPEN |
| 15 | [Testing](development/testing.md) | Test layers, fixtures, parity, gates | PROPOSED |
| 16 | [Benchmarking](development/benchmarking.md) | Harness, metrics, baselines | PROPOSED |
| 17 | [CI/CD](development/ci-cd.md) | Workflows, cache, permissions, release lanes | PROPOSED |
| 18 | [Release](development/release.md) | Packaging, versioning, distribution, gates | PROPOSED |
| 19 | [Security](development/security.md) | License, supply chain, threat model | CONFIRMED / PROPOSED |
| 20 | [Documentation](development/documentation.md) | Standards, docs CI, review rules | CONFIRMED / PROPOSED |
| 21 | [Contributing and governance](governance/contributing.md) | Contribution, review, commits, decisions | CONFIRMED |
| 22 | [Traceability](requirements/traceability.md) | Requirement index and verification mapping | CONFIRMED |

## Status vocabulary

| Status | Meaning |
|---|---|
| `CONFIRMED` | Approved as part of the MVP baseline. |
| `PROPOSED` | Recommended design or policy that still needs explicit approval. |
| `OPEN` | Decision or evidence is missing. It must not be silently assumed. |
| `DEFERRED` | Explicitly excluded from the MVP and assigned to a later phase. |
| `IMPLEMENTED` | Present in the repository and verified by a command or test. |

A document can contain more than one status. The status of each requirement is
recorded next to the requirement.

## Normative language

The key words `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are used as
described in RFC 2119 and RFC 8174. A requirement is normative when it has a
requirement ID and a status of `CONFIRMED` or `IMPLEMENTED`.

## Documentation rules

- Files are UTF-8 without a byte order mark.
- Files use LF line endings.
- No emoji, emoticons, or decorative dingbats.
- No mojibake or replacement characters.
- Mermaid is used for diagrams that benefit from a visual representation.
- Code fences declare a language.
- Requirement IDs are stable and are not renumbered after publication.
- A requirement is not marked `IMPLEMENTED` without a verification command,
  test, or repository artifact that proves it.

## Current implementation snapshot

| Area | Current state | Evidence |
|---|---|---|
| Bazel build | Implemented | `bazel build //...` succeeds with 59 targets. |
| Bazel test | Implemented for codegen, the publisher, the release version check, the release preparation, the release rehearsal, the repository structure checks, the documentation checks, the link check, the schema bundle, the release tag, the document model, and the cross-language contract | `bazel test //...` runs seventeen of the nineteen test rules, because the two transitive type-check rules are tagged `manual`: sixteen unittest cases, 45 publisher cases, 15 version cases, 20 release preparation cases, 6 release rehearsal cases, 43 repository structure cases, 4 release tag cases, 32 documentation gate cases, 4 link check cases, the documentation check, the schema bundle check, 74 document model cases, 6 contract fixture cases, and the TypeScript model, contract, and type-check targets. |
| Documentation checks | Implemented | `//scripts:docs_checks` validates the documents, the Markdown structure, the Mermaid diagrams, the requirement index, the ADR index, the schema references, the workflow files, and the CODEOWNERS file. |
| Repository structure checks | Implemented | `//scripts:repository_checks` validates the dependency direction, the Python packages, the toolchain, the committed lock file, the TypeScript compiler version, the ADR template, the committed generated schemas, the Bazel package structure, the pinned Bazel version, the security configuration, the npm package name, and the scope document. |
| External link check | Implemented | `//scripts:check_links` checks the external links with a timeout and reports warnings only. |
| JSON Schema generator | Implemented | `tools/codegen/` and `bazel/codegen.bzl`. The generator accepts only standard JSON, so the constants `NaN`, `Infinity`, and `-Infinity` are errors. |
| Schema bundle | Implemented | `//specs/schemas:schema_bundle` builds six files that implement the document IR. |
| Schema bundle validation | Implemented | `//specs/schemas:schema_tests` validates the built bundle and reports no violation, and `//specs/schemas:release_tag_tests` covers the release tag pattern of the identity rule. |
| Schema publisher | Implemented | `//tools/publish:publish_schemas` writes the published bundle with the identity of a release tag and verifies the versioned raw URLs. |
| Schema archive | Implemented | `//specs/schemas:archive` builds a deterministic gzip tarball of the bundle. |
| Release version check | Implemented | `//scripts:check_version` compares the manifests, the contract version of every schema source, and the changelog with the tag. |
| Release preparation | Implemented | `//scripts:prepare_release` sets the release version, publishes the bundle under `specs/schemas/`, verifies the result, and removes the generated published files from the development branch. |
| Python SDK | Implemented for the document model | `packages/python/src/typcast/` holds the immutable model, the diagnostics, and the JSON serialization. The builder, the emitter, the compiler adapter, and the validation engine are not implemented. |
| TypeScript SDK | Implemented for the document model | `packages/typescript/src/` holds the immutable model, the diagnostics, and the JSON serialization. The package is still private. |
| Document model | Implemented | The immutable model of both SDKs, with the JSON reader and writer. |
| Builder API, emitter, compiler adapter | Not implemented | No source files exist. |
| Typst compiler adapter | Not implemented | No source files or tests exist. |
| Packaging and release | Not implemented | No wheel, npm tarball, or publishing job exists. |
| Schema distribution | Decided, tooling implemented | Versioned raw URLs at the release tag; see ADR-0022 and ADR-0023. The publisher, the release preparation, and the release lane carry the distribution. No release exists yet. |
| CI workflows | Implemented for build, test, and verification | `.github/workflows/pr.yml`, `main.yml`, and `release.yml`; the first pull request run passed on Windows and Linux. |
| Pull request template | Implemented | `.github/PULL_REQUEST_TEMPLATE.md`. |
| License | Implemented | `LICENSE` at the repository root. |
| Security policy | Implemented | `SECURITY.md` at the repository root. |
| Contributing guide | Implemented | `CONTRIBUTING.md` at the repository root. |
| Code of conduct | Implemented | `CODE_OF_CONDUCT.md` at the repository root, Contributor Covenant 2.1. |
| Changelog | Implemented | `CHANGELOG.md` at the repository root, Keep a Changelog style. |
| Text file normalization | Implemented | `.gitattributes` and `.editorconfig` at the repository root. |

## Change control

Changes to a `CONFIRMED` requirement require one of the following:

- An approved ADR that supersedes the decision.
- A documented scope change with an impact assessment.
- A correction that removes an inconsistency without changing behavior.

The traceability index in `requirements/traceability.md` is updated in the same
change as the requirement it affects.

## Decision status

Every requirement in the Phase 0 baseline is now decided. There are no `OPEN`
requirements. The decisions that closed the previously open items are listed in
the "Resolved decisions" table in `requirements/traceability.md`, and the
architecture-level decisions are recorded as ADR-0014 through ADR-0023.

The remaining gaps are implementation gaps, not decision gaps: the builder,
the emitter, the compiler adapter, the validation engine, the packaging targets,
and the release process do not exist yet.
