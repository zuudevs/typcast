# Requirements traceability

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-24

## Purpose

This index connects requirements to their source documents, verification
methods, and implementation status. It is the entry point for release reviews and
change impact analysis.

## Requirement families

| Family | Source | Range | Primary verification |
|---|---|---|---|
| Product | `product/vision-and-scope.md` | `PRD-001` to `PRD-017` | Release review, integration tests. |
| Use cases | `product/use-cases.md` | Journey IDs `UC-001` to `UC-004`; acceptance criteria `AC-001` to `AC-018`; requirements `UCR-001` to `UCR-007` | Example and integration tests. |
| Architecture | `architecture/overview.md` | `ARC-001` to `ARC-015` | Design review, parity tests. |
| Repository | `architecture/repository.md` | `REPO-001` to `REPO-012` | Bazel build, dependency review. |
| Document IR | `specifications/document-ir.md` | `IR-001` to `IR-020` | Schema and contract tests. |
| Nodes | `specifications/nodes.md` | `NODE-001` to `NODE-025` | Golden and emitter tests. |
| Schema | `specifications/schema.md` | `SCH-001` to `SCH-021` | Schema lint and bundle tests. |
| SDK API | `specifications/sdk-api.md` | `API-001` to `API-025` | API and parity tests. |
| Emitter | `specifications/emitter.md` | `EMIT-001` to `EMIT-022` | Byte-level golden tests. |
| Compiler | `specifications/compiler.md` | `COMP-001` to `COMP-022` | Compiler integration tests. |
| Diagnostics | `specifications/diagnostics.md` | `DIAG-001` to `DIAG-012` | Negative and parity tests. |
| Assets | `specifications/assets.md` | `ASSET-001` to `ASSET-020` | Path and workspace tests. |
| Compatibility | `specifications/compatibility.md` | `COMPAT-001` to `COMPAT-019` | CI matrix. |
| Build | `development/build.md` | `BUILD-001` to `BUILD-020` | Bazel commands. |
| Testing | `development/testing.md` | `TEST-001` to `TEST-025` | Test inventory. |
| Benchmarking | `development/benchmarking.md` | `PERF-001` to `PERF-015` | Benchmark job. |
| CI/CD | `development/ci-cd.md` | `CI-001` to `CI-026` | Workflow review. |
| Release | `development/release.md` | `REL-001` to `REL-031` | Release checklist. |
| Security | `development/security.md` | `SEC-001` to `SEC-025` | Security review. |
| Documentation | `development/documentation.md` | `DOC-001` to `DOC-021` | Docs gate. |
| Governance | `governance/contributing.md` | `GOV-001` to `GOV-021` | Repository settings. |
| Traceability | This document | `TRACE-001` to `TRACE-005` | Review. |

## Critical end-to-end traces

| Goal | Requirements | Verification |
|---|---|---|
| Typed cross-language document builder | `PRD-008`, `ARC-001`, `IR-001`, `API-001`, `API-017` | Contract and parity tests. |
| Deterministic `.typ` output | `PRD-009`, `EMIT-001`, `EMIT-002`, `EMIT-022` | Byte-level golden tests. |
| PDF through Typst | `PRD-009`, `COMP-001`, `COMP-004`, `COMP-013`, `REL-024` | Compiler integration and release review. |
| Two-phase validation | `PRD-013`, `API-006`, `API-008`, `DIAG-001` | Validation and diagnostics tests. |
| Warning handling | `DIAG-011`, `API-007`, `API-012` | Warning-policy and parity tests. |
| Safe asset resolution | `ASSET-003`, `ASSET-005`, `ASSET-006`, `SEC-015`, `TEST-020` | Path, symlink, and negative tests. |
| Stable diagnostics | `DIAG-002`, `DIAG-003`, `DIAG-004`, `API-016` | Diagnostics parity tests. |
| Public distribution | `PRD-015`, `REL-005`, `REL-006`, `REL-008`, `CI-016` | Install tests and release check. |
| Schema distribution | `SCH-021`, `REL-029`, `REL-030`, `REL-031`, `COMPAT-019`, `CI-026` | Release check and URL verification. |
| Apache-2.0 licensing | `PRD-016`, `SEC-001`, `SEC-002`, `REL-010`, `REL-022` | Package and license checks. |
| Stable `1.0.0` gate | `PRD-017`, `REL-003`, `REL-013`, `CI-006` | Release checklist. |
| Documentation quality | `DOC-001`, `DOC-002`, `DOC-012`, `CI-014` | Docs gate. |
| Vulnerability response | `SEC-003`, `SEC-024`, `SEC-025` | Policy review and release check. |

## Status summary

| Status | Meaning | Release impact |
|---|---|---|
| `CONFIRMED` | Approved requirement. | Must be satisfied for `1.0.0`. |
| `PROPOSED` | Recommended but not approved. | Must be resolved or explicitly deferred. |
| `OPEN` | Missing decision or evidence. | Must be resolved or accepted with rationale. |
| `DEFERRED` | Excluded from the MVP. | Must not block the MVP. |
| `IMPLEMENTED` | Present and verified. | Evidence must exist. |

## Open requirements

No requirement is currently undecided. Every `OPEN` or `PROPOSED` requirement
from the Phase 0 baseline was resolved on 2026-11-24. The decisions are
recorded below and in the linked ADRs.

## Resolved decisions

| Requirement | Decision | Recorded in |
|---|---|---|
| `SCH-009` | The built bundle is the authoritative artifact set; source-tree `$ref` resolution is optional. | ADR-0023 |
| `SCH-021` | A published schema is referenced by the versioned raw URL of its release tag; a `main` URL is a development reference only. | ADR-0022 |
| `IR-019` | The raw size limit defaults to 1 MiB and is configurable through `max_raw_bytes`. | ADR-0017 |
| `NODE-023` | The raw size limit is enforced at `build()` and again before emit. | ADR-0017 |
| `API-024` | The builder is mutable, single-document, and not thread-safe. | ADR-0015 |
| `API-025` | The npm package is ESM-only for `1.0.0`; CommonJS is deferred. | ADR-0016 |
| `DIAG-011` | Warnings follow the closed policy: three warning conditions, never raising, never gating a release. | ADR-0014 |
| `ASSET-017` | Asset limits are 1024-character paths, 50 MiB per image, 10 MiB per module, 500 MiB per compilation. | ADR-0017 |
| `COMPAT-008` | The supported Typst range is `>=0.15.0 <0.16.0`, tested with 0.15.1. | ADR-0018 |
| `COMPAT-016` | Linux CI proves the current `.bazelrc` starts; the symlink flag moves to a Windows-only rc file if it is rejected. | ADR-0018 |
| `COMPAT-017` | The npm package is ESM-only for `1.0.0`. | ADR-0016 |
| `COMPAT-019` | A consumer pins an exact schema release tag and does not use a floating reference. | ADR-0022 |
| `BUILD-012` | Same as `COMPAT-016`. | ADR-0018 |
| `BUILD-014` | Packaging targets are `//packages/python:wheel`, `//packages/python:sdist`, `//packages/typescript:npm_package`, and `//specs/schemas:archive`. | ADR-0022 |
| `BUILD-015` | Schema validation runs in `//specs/schemas:schema_tests` against the built bundle. | ADR-0023 |
| `BUILD-016` | Unreferenced convenience filegroups are removed; `schema_bundle` stays as the published entry point. | ADR-0022 |
| `BUILD-018` | CI builds from a clean checkout to prove reproducibility. | ADR-0018 |
| `BUILD-019` | Bazel outputs are cached per operating system, keyed by version, lockfile, and build files. | ADR-0018 |
| `TEST-014` | Coverage is critical-path based, not a numeric threshold. | ADR-0019 |
| `TEST-015` | CI does not retry failed tests; quarantined tests are reported separately. | ADR-0019 |
| `TEST-024` | Test reports are retained for 14 days. | ADR-0019 |
| `PERF-004` | Peak memory is measured on Linux only, where it is reliable. | ADR-0019 |
| `PERF-012` | Benchmark artifacts are retained for 90 days. | ADR-0019 |
| `PERF-013` | A median wall-time regression above 10 percent warns and does not fail the build. | ADR-0019 |
| `CI-024` | The matrix covers Windows and Linux, Python 3.11 to 3.14, Node.js 22 and 24, and Typst 0.15.1. | ADR-0018 |
| `CI-026` | The release lane verifies the published schema bundle and the versioned raw URLs. | ADR-0022 |
| `REL-027` | Artifact target names are fixed as listed in `BUILD-014`. | ADR-0022 |
| `REL-028` | The SBOM is CycloneDX 1.6 JSON attached to the release. | ADR-0022 |
| `REL-029` | The canonical schema reference is the versioned raw URL under the release tag; the MVP requires no dedicated schema domain. | ADR-0022 |
| `REL-030` | The tagged release commit contains the complete published bundle under `specs/schemas/`. | ADR-0022 |
| `REL-031` | A published release tag is immutable; a correction ships in a new tag. | ADR-0022 |
| `SEC-024` | Response targets are 3 business days to acknowledge, 7 to triage, and 30 calendar days for a critical fix. | ADR-0022 |
| `SEC-025` | The SBOM is CycloneDX 1.6 JSON attached to each release. | ADR-0022 |
| `DOC-010` | Unreachable external links warn; only broken internal links block. | `development/documentation.md` |
| `GOV-006` | One pull request template at `.github/PULL_REQUEST_TEMPLATE.md` covers tests, documentation, changelog, and version impact. | `governance/contributing.md` |
| `GOV-007` | Issue templates are deferred for the MVP; an issue is a free-form report. | `governance/contributing.md` |
| `GOV-018` | The project adopts the Contributor Covenant 2.1 and adds `CODE_OF_CONDUCT.md` before public contributions. | `governance/contributing.md` |
| `GOV-021` | The template records the commands that were run and their results, and allows an inapplicable section or checkbox to be removed or marked "Not applicable". | `governance/contributing.md` |

## Implementation evidence

Only these requirements are currently `IMPLEMENTED`. Every other requirement is
a target for the MVP and is not yet verified in the repository.

| Requirement | Evidence | Verified by |
|---|---|---|
| `BUILD-010` | The generator accepts absolute input and output paths and creates the output parent directory. | Manual run documented in `development/build.md`; `test_output_parent_directory_is_created` in `//tools/codegen/tests:unit_tests`. |
| `BUILD-015` | `//specs/schemas:schema_tests` validates the bundle that `//specs/schemas:schema_bundle` produces, against the rules in `specifications/schema.md`. | `//specs/schemas:schema_tests`; 5 bundle files checked, 26 tracked prototype violations, 0 errors. |
| `BUILD-017` | The documentation checks run with the hermetic Python toolchain and need no SDK installation and no network access. | `//scripts:docs_checks`; `scripts/validate_docs.py` uses the standard library only. |
| `BUILD-016` | `//specs/schemas/templates/api/types:schema_templates` and `//specs/catalogs/enums:enum_catalogs` were removed; `schema_bundle` remains the bundle entry point. | `bazel query "rdeps(//..., //specs/schemas:schema_bundle)"` and `bazel build //...`. |
| `SCH-011` | `read_csv_column` rejects an empty value in the selected column. | `test_empty_value_in_selected_column_reports_an_error` in `//tools/codegen/tests:unit_tests`. |
| `SCH-012` | `read_csv_column` skips fully blank rows. | `test_fully_blank_rows_are_skipped` in `//tools/codegen/tests:unit_tests`. |
| `SCH-009` | The schema contract is validated against the built bundle, not against the source tree. | `//specs/schemas:schema_tests`; 5 bundle files checked, 26 tracked prototype violations, 0 errors. |
| `DOC-015` | The root `README.md` uses standard code fences and LF line endings. | Documentation validation script run on 2026-11-24. |
| `DOC-016` | `.gitattributes` pins LF for text files and `.editorconfig` pins UTF-8, LF, final newline, and indentation. | Files present at the repository root. |
| `DOC-021` | `scripts/validate_docs.py` validates the documents, the requirement index, the ADR index, and the schema references with the standard library only. | `//scripts:docs_checks`; 53 files and 439 requirements checked with 0 errors. |
| `TEST-016` | `//specs/schemas:schema_tests` validates every bundle file and resolves every relative `$ref`; the one dangling reference is tracked as `SCH-D01`. | `//specs/schemas:schema_tests`; 5 bundle files checked, 26 tracked prototype violations, 0 errors. |
| `SEC-002` | The Apache-2.0 license text is present at the repository root. | `LICENSE`, compared byte for byte with the canonical Apache-2.0 text. |
| `SEC-003` | The vulnerability reporting policy is present at the repository root. | `SECURITY.md`. |
| `GOV-019` | Contributions are accepted under Apache-2.0. | `LICENSE`. |
| `GOV-006` | The repository has exactly one pull request template at `.github/PULL_REQUEST_TEMPLATE.md`, with the summary, classification, scope, requirement traceability, architecture and API impact, testing and verification, documentation, compatibility and release impact, security, final checklist, and reviewer notes sections. | `.github/PULL_REQUEST_TEMPLATE.md`. |
| `GOV-021` | The template records the commands that were run and their results, and states that an inapplicable section or checkbox is removed or marked "Not applicable". | `.github/PULL_REQUEST_TEMPLATE.md`. |

## Traceability rules

| ID | Rule | Status |
|---|---|---|
| TRACE-001 | Requirement IDs MUST be unique across the project. | CONFIRMED |
| TRACE-002 | Every confirmed requirement MUST have a verification method. | CONFIRMED |
| TRACE-003 | Every implemented requirement MUST link to evidence. | CONFIRMED |
| TRACE-004 | Requirement changes MUST update this index in the same change. | CONFIRMED |
| TRACE-005 | Open requirements MUST be listed with the decision they need. | CONFIRMED |

## How to update

1. Add or change the requirement in its source document.
2. Assign a new ID; do not reuse a removed ID.
3. Update the family range and verification in this document.
4. Add an end-to-end trace if the requirement affects a release gate.
5. Update the open requirements table if the status is `OPEN` or `PROPOSED`.
6. Link the approving ADR or scope change for a confirmed requirement change.

## Related documents

- [Documentation index](../README.md)
- [Vision and scope](../product/vision-and-scope.md)
- [Architecture overview](../architecture/overview.md)
- [Release](../development/release.md)
- [Documentation](../development/documentation.md)
