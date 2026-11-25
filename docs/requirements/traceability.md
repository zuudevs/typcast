# Requirements traceability

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-25

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
| Build | `development/build.md` | `BUILD-001` to `BUILD-021` | Bazel commands. |
| Testing | `development/testing.md` | `TEST-001` to `TEST-032` | Test inventory. |
| Benchmarking | `development/benchmarking.md` | `PERF-001` to `PERF-015` | Benchmark job. |
| CI/CD | `development/ci-cd.md` | `CI-001` to `CI-029` | Workflow review. |
| Release | `development/release.md` | `REL-001` to `REL-036` | Release checklist. |
| Security | `development/security.md` | `SEC-001` to `SEC-025` | Security review. |
| Documentation | `development/documentation.md` | `DOC-001` to `DOC-027` | Docs gate. |
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
| Release artifacts | `REL-005`, `REL-006`, `REL-007`, `REL-008`, `REL-035`, `BUILD-014`, `BUILD-021` | Artifact build and checksum check. |
| Apache-2.0 licensing | `PRD-016`, `SEC-001`, `SEC-002`, `REL-010`, `REL-022` | Package and license checks. |
| Stable `1.0.0` gate | `PRD-017`, `REL-003`, `REL-013`, `CI-006` | Release checklist. |
| Documentation quality | `DOC-001`, `DOC-002`, `DOC-012`, `DOC-024`, `CI-014` | Docs gate and link check. |
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
| `SCH-020` | The schema contract is migrated to the document IR before `1.0.0`, and the ten prototype defects are closed. | `specifications/schema.md` |
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
| `CI-026` | The release lane verifies the published schema bundle, the archive of the published bundle, and the versioned raw URLs. | ADR-0022; `//scripts/tests:release_flow_tests`. |
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
| `BUILD-012` | The Linux CI run starts Bazel with the current `.bazelrc`. | The first Linux CI run passed on 2026-11-24. |
| `COMPAT-016` | The Linux CI run starts Bazel with the current `.bazelrc`. | The first Linux CI run passed on 2026-11-24. |
| `BUILD-015` | `//specs/schemas:schema_tests` validates the bundle that `//specs/schemas:schema_bundle` produces, against the rules in `specifications/schema.md`. | `//specs/schemas:schema_tests`; 6 bundle files checked, 0 violations. |
| `BUILD-017` | The documentation checks run with the hermetic Python toolchain and need no SDK installation and no network access. | `//scripts:docs_checks`; `scripts/validate_docs.py` uses the standard library only. |
| `BUILD-018` | The clean checkout build proves that the build does not depend on a warm cache or on an untracked file. | The `Clean build` job of the workflows; the first run passed. |
| `BUILD-019` | The Bazel cache is separated by operating system and keyed by the Bazel version, the lockfile, and the build files. | The cache configuration of the workflows. |
| `BUILD-016` | `//specs/schemas/templates/api/types:schema_templates` and `//specs/catalogs/enums:enum_catalogs` were removed; `schema_bundle` remains the bundle entry point. | `bazel query "rdeps(//..., //specs/schemas:schema_bundle)"` and `bazel build //...`. |
| `BUILD-021` | `//specs/schemas:archive` writes a deterministic gzip tarball: the member order, the member metadata, and the gzip header are fixed, and the bytes do not depend on the modification time of the files. | `//specs/schemas:archive`; `//tools/publish/tests:publish_tests` compares two archives byte for byte. |
| `SCH-011` | `read_csv_column` rejects an empty value in the selected column. | `test_empty_value_in_selected_column_reports_an_error` in `//tools/codegen/tests:unit_tests`. |
| `SCH-012` | `read_csv_column` skips fully blank rows. | `test_fully_blank_rows_are_skipped` in `//tools/codegen/tests:unit_tests`. |
| `SCH-001` | Every schema of the bundle declares the draft 2020-12 dialect. | `//specs/schemas:schema_tests`; the dialect rule. |
| `SCH-002` | Every schema of the bundle declares an absolute, unique `$id` that matches its versioned raw URL, and the release tag of that URL matches the whole tag. | `//specs/schemas:schema_tests`; the identity and uniqueness rules; `//specs/schemas:release_tag_tests`. |
| `SCH-003` | Every object schema of the bundle is closed. | `//specs/schemas:schema_tests`; the closed-object rule. |
| `SCH-006` | Every union of the bundle uses a `type` discriminator with unique `const` values. | `//specs/schemas:schema_tests`; the discriminator rule. |
| `SCH-008` | Every relative `$ref` of the bundle resolves inside the bundle. | `//specs/schemas:schema_tests`; the reference rule. |
| `SCH-009` | The schema contract is validated against the built bundle, not against the source tree. | `//specs/schemas:schema_tests`; 6 bundle files checked, 0 violations. |
| `SCH-020` | The ten prototype defects `SCH-D01` to `SCH-D10` are closed. | `specifications/schema.md`; the bundle test reports no violation. |
| `DOC-015` | The root `README.md` uses standard code fences and LF line endings. | Documentation validation script run on 2026-11-24. |
| `DOC-016` | `.gitattributes` pins LF for text files and `.editorconfig` pins UTF-8, LF, final newline, and indentation. | Files present at the repository root. |
| `DOC-021` | `scripts/validate_docs.py` validates the documents, the requirement index, the ADR index, and the schema references with the standard library only. | `//scripts:docs_checks`; 57 files, 461 requirements, and 3 workflows checked with 0 errors. |
| `DOC-012` | The documentation gate runs on pull requests. | The `Documentation gate` job of `.github/workflows/pr.yml`. |
| `DOC-013` | The documentation gate runs on `main`. | The `Documentation gate` job of `.github/workflows/main.yml`. |
| `DOC-022` | The repository gate validates the workflow files: pinned actions, declared permissions, no write access or secret in a pull request workflow, and no `pull_request_target`. | `//scripts:docs_checks`; 3 workflows checked. |
| `DOC-023` | The repository gate validates the CODEOWNERS file: it exists, every rule names an owner, and one rule covers every path. | `//scripts:docs_checks`; the CODEOWNERS file is checked. |
| `DOC-006` | Every code fence of the documents declares a language. | `//scripts:docs_checks`; the code fence rule. |
| `BUILD-008` | Every CSV used by a template is declared in the `catalogs` attribute of the rule, and the generator rejects a placeholder whose catalog is not declared. | `//tools/codegen:typcast_codegen`; `//tools/codegen/tests:unit_tests`. |
| `REPO-006` | Every template CSV is declared in the Bazel rule, so the sandbox provides the file and the cache invalidates when it changes. | `//tools/codegen:typcast_codegen`; `//tools/codegen/tests:unit_tests`. |
| `REPO-002` | No module of `specs/` imports the SDK package, so the contract depends on no SDK code. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `REPO-003` | Each SDK depends on no code outside its own package, so the two SDKs cannot depend on each other. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `REPO-007` | The generated published schemas are committed only when every manifest, every schema source, and the changelog agree on the release version. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `REPO-008` | The Python project is named `typcast`, and the package directory `packages/python/src/typcast` holds the `__init__.py` of the import path. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `REPO-010` | No module of `scripts/` imports the SDK package, so the repository checks need no SDK installation. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `REPO-011` | Every package directory that holds Python modules holds an `__init__.py`. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `REPO-012` | The root manifest holds the exact version of the TypeScript compiler, the SDK manifest holds none, and `MODULE.bazel` reads the version from the root manifest. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `REPO-001` | Every source file belongs to a Bazel package, and no source file sits in the root package, so the build sees every file of the repository. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`; `bazel build //...`. |
| `REPO-009` | The npm manifest of the TypeScript SDK is named `typcast`, so the publication uses the reserved name. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-003` | The lock file of the Bazel module is present, is not empty, and is tracked by git. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-004` | The Python toolchain is pinned to one version in `python.defaults()` and `python.toolchain()`, and the module file names no system Python. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-005` | Every package directory that holds Python modules holds an `__init__.py`. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-009` | The generated published schemas are committed only when every manifest, every schema source, and the changelog agree on the release version. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-011` | Every test module is a complete program with an `if __name__ == "__main__":` guard, so the build needs no `--test_filter`. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-013` | The root manifest holds the exact version of the TypeScript compiler, the SDK manifest holds none, and `MODULE.bazel` reads the version from the root manifest. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-001` | Every source file belongs to a Bazel package, and no source file sits in the root package, so Bazel remains the build system of every file. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`; `bazel build //...`. |
| `BUILD-002` | `.bazelversion` holds a Bazel version, and no workflow overrides it, so every lane uses the same Bazel. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `BUILD-006` | The branch protection of `main` requires the `Build` checks of the pull request lane, and every job of that lane runs `bazel build //...`. | The branch protection settings of the repository; the checks passed on 2026-11-24. |
| `BUILD-007` | The branch protection of `main` requires the `Test` checks of the pull request lane, and every job of that lane runs `bazel test //...`. | The branch protection settings of the repository; the checks passed on 2026-11-24. |
| `DOC-014` | No module of `scripts/` imports the SDK package, so the documentation tooling adds no SDK runtime dependency. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `DOC-017` | Every ADR holds the title, the fields, and the sections of the template of `docs/decisions/README.md`, in the documented order. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `DOC-026` | The rules of the repository structure checks are covered by unit tests, and the checks run in the pull request lane, in the main lane, and in the release lane. | `//scripts/tests:repository_tests`; 30 cases; the `Repository checks` job of `pr.yml` and `main.yml`; the `verify` job of `release.yml`. |
| `DOC-027` | The repository publishes the scope document, and the root README links it. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `DOC-001` | Every document is UTF-8 without a byte order mark. | `//scripts:docs_checks`; the encoding rule. |
| `DOC-002` | Every document uses LF line endings and ends with a final newline. | `//scripts:docs_checks`; the encoding rule. |
| `DOC-003` | No document contains an emoji or a dingbat. | `//scripts:docs_checks`; the text hygiene rule. |
| `DOC-004` | No document contains a replacement character. | `//scripts:docs_checks`; the text hygiene rule. |
| `DOC-005` | No document contains a mojibake sequence. | `//scripts:docs_checks`; the text hygiene rule. |
| `DOC-007` | Every document has exactly one level-1 heading, and it is the first line of the document. | `//scripts:docs_checks`; the heading rules. |
| `DOC-008` | Every internal link of the documents resolves. | `//scripts:docs_checks`; the link rule. |
| `DOC-009` | The Mermaid diagrams parse: the flowchart has a direction and readable statements, the sequence diagram declares every participant, and every block is closed. | `//scripts:docs_checks`; the diagram rule. |
| `DOC-010` | The external links are checked with a timeout, and an unreachable link is a warning that does not block the merge. | `//scripts:check_links`; `//scripts/tests:link_tests`. |
| `DOC-024` | The external link check runs in the pull request lane and in the main lane. | The `Link check` job of `.github/workflows/pr.yml` and `main.yml`. |
| `DOC-025` | The rules of the repository gate and of the external link check are covered by unit tests, including the encoding and the text hygiene rules. | `//scripts/tests:docs_tests`; `//scripts/tests:link_tests`. |
| `TEST-016` | `//specs/schemas:schema_tests` validates every bundle file and resolves every relative `$ref`, and `//specs/schemas:release_tag_tests` covers the release tag pattern of the identity rule. | `//specs/schemas:schema_tests`; 6 bundle files checked, 0 violations; `//specs/schemas:release_tag_tests`; 4 cases. |
| `TEST-025` | The test lane runs on Windows and Linux. | The `Test` jobs of the workflows; the first run passed on `windows-latest` and `ubuntu-latest`. |
| `TEST-026` | `//tools/publish/tests:publish_tests` covers the publisher with unit tests and with an integration test against the built bundle. | `//tools/publish/tests:publish_tests`; 45 cases. |
| `TEST-027` | `//scripts/tests:version_tests` covers the release version check. | `//scripts/tests:version_tests`; 15 cases. |
| `TEST-028` | The publisher tests serve the published files from a local server, so the test suite needs no network access. | `//tools/publish/tests:publish_tests`; the `PublishedUrlTests` cases. |
| `TEST-029` | The publisher tests cover the content, the member metadata, and the byte-for-byte determinism of the schema archive. | `//tools/publish/tests:publish_tests`; the `ArchiveTests` cases. |
| `TEST-030` | The unit tests cover the rules of the repository gate and of the external link check, including the encoding and the text hygiene rules. | `//scripts/tests:docs_tests`; `//scripts/tests:link_tests`. |
| `TEST-031` | The unit tests cover the version bump, the publication, the verification, and the cleanup of the release preparation. | `//scripts/tests:release_tests`; 20 cases. |
| `TEST-032` | The rehearsal covers the release preparation end to end with the manifests, the schema sources, and the bundle of the build, so that the path of the release lane runs in the test lane. | `//scripts/tests:release_flow_tests`; 6 cases. |
| `REL-012` | `//scripts:check_version` compares the version of every manifest, the contract version of every schema source, and the changelog with the tag, and the release lane runs the check on the tagged commit. | `//scripts:check_version`; `//scripts/tests:version_tests`; 15 cases. |
| `REL-032` | `//tools/publish:publish_schemas` publishes exactly the files of the bundle manifest, sets the `$id` of every file to the versioned raw URL of the release tag, and rejects a version that is not a release tag. | `//tools/publish:publish_schemas`; `publish` and `check` verified against the built bundle with an illustrative `v1.0.0` tag. |
| `REL-033` | `//scripts:check_version` compares the version of every manifest, the contract version of every schema source, and the changelog with the tag, and reports every mismatch. | `//scripts:check_version`; `//scripts/tests:version_tests`; 15 cases. |
| `REL-034` | `publish_schemas verify` fetches every published schema from its versioned raw URL and compares the served bytes with the file of the tagged commit. | `//tools/publish:publish_tests`; the `PublishedUrlTests` cases. |
| `REL-036` | `//scripts:prepare_release` sets the release version in every manifest and in every schema source, publishes the built bundle under `specs/schemas/`, verifies the version consistency, the published bundle, and the archive, and removes the generated published files from the development branch. The rehearsal runs the path with the files of the repository and the bundle of the build. | `//scripts:prepare_release`; `//scripts/tests:release_tests`; 20 cases; `//scripts/tests:release_flow_tests`; 6 cases. |
| `CI-001` | The repository has the pull request validation, the main integration, and the release workflows. | `.github/workflows/pr.yml`, `.github/workflows/main.yml`, and `.github/workflows/release.yml`. |
| `CI-002` | The pull request workflows have read-only permissions. | `permissions: contents: read` in `pr.yml` and `main.yml`; the repository gate rejects write access in a pull request workflow. |
| `CI-003` | No pull request workflow reads a secret. | No workflow reads a secret; the repository gate rejects a secret in a pull request workflow. |
| `CI-004` | The main integration workflow runs on every push to `main`. | `.github/workflows/main.yml`. |
| `CI-010` | The Bazel cache is separated by operating system. | The cache key of the workflows holds the operating system and the architecture. |
| `CI-011` | The cache key holds the Bazel version, the lockfile, and the build files. | The cache configuration of the workflows hashes `.bazelversion`, `MODULE.bazel.lock`, and the build files. |
| `CI-012` | The build and the test lane run on Windows and Linux. | The workflows; the first run passed on `windows-latest` and `ubuntu-latest`. |
| `CI-014` | The documentation gate runs on pull requests and on `main`. | The `Documentation gate` job of `pr.yml` and `main.yml`. |
| `CI-017` | The release workflow uses one concurrency group per tag and does not cancel a run. | `.github/workflows/release.yml`. |
| `CI-019` | Every action is pinned to a commit SHA. | The three workflow files; the repository gate rejects a tag or a branch. |
| `CI-020` | No workflow publishes. | The three workflow files; the pull request workflow has read-only permissions. |
| `CI-021` | The test lane prints the output of every failing test. | `test --test_output=errors` in `.bazelrc`. |
| `CI-025` | The workflow files are in their own commits. | The commits `ci: add the pull request validation workflow`, `ci: add the main integration workflow`, and `ci: add the release verification workflow`. |
| `CI-027` | The pull request and main lanes run the build, the test lane, the clean checkout build, the documentation gate, the repository structure checks, and the external link check, and the release lane verifies the version, the tagged build, the published bundle, the archive of the published bundle, and the raw URLs. | The three workflow files; the first pull request run passed on 2026-11-24. |
| `CI-015` | The pull request lane reviews the dependencies of the pull request, and the secret scanning and the push protection are enabled in the settings of the repository. | The `Dependency review` job of `pr.yml`; `security_and_analysis` of the repository API. |
| `CI-029` | The pull request lane reviews the dependencies of the pull request with an action that is pinned to a commit SHA. | The `Dependency review` job of `pr.yml`; `actions/dependency-review-action` is pinned to a commit SHA. |
| `CI-026` | The release lane verifies the published schema bundle, the archive of the published bundle, and the versioned raw URLs. | `//scripts/tests:release_flow_tests`; the rehearsal of the release path. |
| `CI-028` | The repository gate rejects an unpinned action, a workflow without permissions, write access or a secret in a pull request workflow, and `pull_request_target`. | `scripts/validate_docs.py`; `//scripts:docs_checks`; 3 workflows checked. |
| `SEC-002` | The Apache-2.0 license text is present at the repository root. | `LICENSE`, compared byte for byte with the canonical Apache-2.0 text. |
| `SEC-003` | The vulnerability reporting policy is present at the repository root and names a private channel, and it sends no reporter to a public issue. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `SEC-004` | The settings of the repository report secret scanning and push protection as enabled. | The settings of the repository; `security_and_analysis` of the repository API. |
| `SEC-005` | The ignore file holds the `.env` and `.env.*` patterns, so an environment file is never committed. | `//scripts:repository_checks`; `//scripts/tests:repository_tests`. |
| `SEC-007` | The settings of the repository enable the security updates of Dependabot, and `.github/dependabot.yml` covers the module file of Bazel, the root npm manifest, the npm manifest of the TypeScript SDK, and the Python manifest of the Python SDK. | The settings of the repository; `.github/dependabot.yml`; `//scripts:repository_checks`. |
| `GOV-019` | Contributions are accepted under Apache-2.0. | `LICENSE`. |
| `GOV-006` | The repository has exactly one pull request template at `.github/PULL_REQUEST_TEMPLATE.md`, with the summary, classification, scope, requirement traceability, architecture and API impact, testing and verification, documentation, compatibility and release impact, security, final checklist, and reviewer notes sections. | `.github/PULL_REQUEST_TEMPLATE.md`. |
| `GOV-021` | The template records the commands that were run and their results, and states that an inapplicable section or checkbox is removed or marked "Not applicable". | `.github/PULL_REQUEST_TEMPLATE.md`. |
| `GOV-018` | `CODE_OF_CONDUCT.md` carries the Contributor Covenant 2.1 text and names the maintainer contact for reports. | `CODE_OF_CONDUCT.md` at the repository root. |
| `GOV-003` | The branch protection of `main` requires one approving review. | The branch protection settings of the repository. |
| `GOV-004` | The branch protection of `main` requires the eight checks of the pull request lane. | The branch protection settings of the repository; the checks passed on 2026-11-24. |
| `GOV-013` | Direct pushes to `main` are blocked; an administrator may merge a pull request without a second reviewer while the project has one maintainer. | The branch protection settings of the repository. |

| `IR-001` | The reader of both SDKs rejects a document that misses `schemaVersion`, `metadata`, `page`, or `contents`. | `//packages/python/tests:model_tests`; the missing-required-field case. |
| `IR-002` | The reader of both SDKs rejects an unknown field of the `page` object. | `//packages/python/tests:model_tests`; the unknown-node-field case. |
| `IR-003` | The constructor of both SDKs rejects empty contents, and the reader rejects a block without a supported discriminator. | `//packages/python/tests:model_tests`; the empty-contents case and the unknown-discriminator case. |
| `IR-004` | The reader of both SDKs rejects an unknown discriminator with `TYPCAST-VAL-0003`. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the negative fixture `unknown-discriminator.json`. |
| `IR-005` | The constructor of both SDKs rejects a heading level outside 1 to 6 with `TYPCAST-VAL-0005`. | `//packages/python/tests:model_tests`; the heading-level case. |
| `IR-007` | The constructor of both SDKs rejects another table alignment with `TYPCAST-VAL-0003`. | `//packages/python/tests:model_tests`; the alignment case. |
| `IR-008` | The constructor of both SDKs rejects another length unit with `TYPCAST-VAL-0004`. | `//packages/python/tests:model_tests`; the unit case. |
| `IR-011` | The constructor of both SDKs rejects an empty raw value with `TYPCAST-VAL-0006`. | `//packages/python/tests:model_tests`; the empty-raw-value case. |
| `IR-012` | The reader of both SDKs rejects a malformed version with `TYPCAST-IR-0002` and accepts a supported patch version. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the negative fixtures `malformed-version.json` and `unsupported-version.json`, and the fixture `patch-version.json`. |
| `IR-013` | Both SDKs write every shared fixture back byte for byte in the canonical form. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the valid fixtures of the manifest. |
| `IR-014` | Both SDKs reject every negative fixture with the diagnostic code that the manifest names. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the negative fixtures of the manifest. |
| `IR-015` | The reader and the writer of both SDKs preserve the document. | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the round-trip cases. |
| `IR-017` | The SDKs depend on no Typst compiler, and the model and the contract tests run without a Typst installation. | `//packages/python/tests:model_tests`; `//tests/contract:contract_py`; `//tests/contract:contract_ts_test`. |
| `IR-018` | The shared fixtures are language-neutral JSON, and both SDKs read them. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the fixtures under `tests/fixtures/documents/`. |
| `API-004` | The constructors of both SDKs check the type, the enum literal, the range, and the emptiness of their arguments. | `//packages/python/tests:model_tests`; `//packages/typescript:model_test_run`; the constructor cases. |
| `API-009` | Both SDKs write the canonical JSON form: two-space indentation, the field order of the contract, and a trailing newline. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; every shared fixture is written back byte for byte. |
| `API-010` | Both SDKs reject an unknown field, a missing required field, and an unsupported version. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the negative fixtures of the manifest. |
| `API-011` | The round trip of both SDKs preserves the document. | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the round-trip cases. |
| `API-015` | Every error of both SDKs inherits from `TypcastError` and exposes a diagnostic. | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the error cases. |
| `API-016` | Both SDKs expose the same diagnostic fields, and the contract runners compare the code of every negative fixture. | `typcast.diagnostics`; `packages/typescript/src/diagnostics.ts`; `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`. |
| `API-018` | Both package roots export the public API. | `//packages/python/tests:model_tests` imports every public type from `typcast`; `//packages/typescript:model_test_run` imports every public type from the package root. |
| `DIAG-001` | Both SDKs expose the documented diagnostic shape. | `typcast.diagnostics`; `packages/typescript/src/diagnostics.ts`; the diagnostic cases of the model tests. |
| `DIAG-004` | Both SDKs expose the same diagnostic fields, and the contract runners compare the code of every negative fixture. | `typcast.diagnostics`; `packages/typescript/src/diagnostics.ts`; `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`. |
| `DIAG-005` | `ValidationError` and `SerializationError` of both SDKs inherit from `TypcastError`. | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the error cases. |
| `DIAG-006` | The diagnostic of a rejected document carries the JSON Pointer of the failing node. | `//packages/python/tests:model_tests`; the diagnostic-path case. |
| `DIAG-009` | Every diagnostic message of both SDKs is English. | `typcast.diagnostics`; `packages/typescript/src/diagnostics.ts`. |
| `DIAG-010` | An application handles an error by its code, and the manifest names the expected code of every negative fixture. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the manifest of the shared fixtures. |
| `NODE-001` | The model of both SDKs holds the seven block types of the catalog and no other. | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the node-type case. |
| `NODE-002` | The model of both SDKs holds the seven inline span types of the catalog and no other. | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the node-type case. |
| `NODE-003` | The constructor of both SDKs rejects a heading level outside 1 to 6. | `//packages/python/tests:model_tests`; the heading-level case. |
| `NODE-004` | The constructor of both SDKs rejects empty heading and paragraph content. | `//packages/python/tests:model_tests`; the empty-content case. |
| `NODE-010` | The constructor of both SDKs requires a non-empty alternative text of an image. | `//packages/python/tests:model_tests`; the image cases. |
| `NODE-011` | The model of both SDKs holds an optional caption, and the canonical JSON omits the field when it is absent. | `//packages/python/tests:model_tests`; the optional-field case. |
| `REPO-004` | Both contract runners check the schema version of the fixtures against the version of their own SDK. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the contract-version case. |
| `REPO-005` | The fixtures under `tests/fixtures/documents/` are language-neutral JSON, and both contract runners read them. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`. |
| `TEST-002` | The fixtures under `tests/fixtures/documents/` are language-neutral JSON. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`. |
| `TEST-017` | Both contract runners read every valid fixture, write it back byte for byte, and read it again. | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the round-trip cases. |
| `TEST-018` | The shared fixtures cover the seven block types and the seven inline span types, and the model tests serialize every type. | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the node-type case. |

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
