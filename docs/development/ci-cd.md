# CI/CD

Status: PROPOSED
Scope: Normative
Last updated: 2026-11-24

## Purpose

This document defines the CI/CD workflows for pull requests, main integration,
and release. The MVP uses three separate workflows so that publishing
credentials are never available to pull request code.

The repository currently has no active workflow. `.github/workflows/` contains
only `.gitkeep`. This document specifies the target; it does not create or enable
publishing.

## Workflow overview

| Workflow | Trigger | Purpose | Permissions |
|---|---|---|---|
| PR validation | `pull_request` | Build, fast tests, docs, security checks. | `contents: read` |
| Main integration | `push` to `main` | Full tests, compiler integration, install tests, matrix. | `contents: read` |
| Release | Tag `v*` | Verify, package, publish, attach release assets. | `contents: write`, `id-token: write` |

```mermaid
flowchart TD
  PR["Pull request"] --> PV["PR validation"]
  PV --> B["Build"]
  PV --> F["Fast tests"]
  PV --> D["Docs gate"]
  PV --> S["Security checks"]
  M["Push to main"] --> MI["Main integration"]
  MI --> FT["Full tests"]
  MI --> CI["Compiler integration"]
  MI --> IT["Install tests"]
  MI --> MX["Compatibility matrix"]
  T["Tag v*"] --> R["Release"]
  R --> V["Version and gate verification"]
  V --> P["Build packages"]
  P --> PUB["Publish PyPI and npm"]
  PUB --> GH["GitHub Release assets"]
```

## PR validation

Triggers:

- `pull_request` to `main`.
- No secrets.
- No publishing.

Jobs:

1. Checkout with full history only if needed for version checks.
2. Set up Bazelisk and cache.
3. `bazel build //...`.
4. `bazel test //...` for the fast lane.
5. Schema validation: `bazel test //specs/schemas:schema_tests`.
6. Contract and golden tests.
7. Cross-language parity tests.
8. Repository checks: `bazel test //scripts:docs_checks`.
9. Dependency and secret scanning where available.

Permissions:

```yaml
permissions:
  contents: read
```

The workflow must not use `pull_request_target` for code execution.

## Main integration

Triggers:

- `push` to `main`.
- Manual dispatch for diagnostics.

Jobs:

1. Full test lane on Windows and Linux.
2. Compiler integration with the supported Typst version.
3. Install and consumer tests from wheel and npm tarball.
4. Compatibility matrix for Python and Node.
5. Benchmark job on the main lane.
6. Documentation gate for all documents.
7. Cache warm for the next run.

Permissions:

```yaml
permissions:
  contents: read
```

Main integration does not publish.

## Release

Triggers:

- Tag `v*`.
- Manual approval through a protected environment.

Preconditions:

- Tag matches the package versions.
- Tag matches the schema version.
- Changelog contains the release.
- All tests pass.
- Documentation gate passes.
- Security checks pass.
- Artifacts are built from the tagged commit.
- The tagged commit contains the complete published schema bundle under
  `specs/schemas/`.

Jobs:

1. Verify version consistency across `MODULE.bazel`, the root `package.json`,
   `pyproject.toml`, `packages/typescript/package.json`, and the tag.
2. Build wheel, sdist, npm tarball, schema archive, checksums, and SBOM.
3. Compare the published schema bundle in the tagged commit with the built
   bundle.
4. Run install tests against the built artifacts.
5. Publish Python to PyPI.
6. Publish npm package.
7. Create or update the GitHub Release.
8. Attach artifacts and checksums.
9. Fetch every published schema from its versioned raw URL and compare it with
   the release bundle.
10. Record the Typst version used for verification.

Permissions:

```yaml
permissions:
  contents: write
  id-token: write
```

Publishing credentials:

- Prefer PyPI trusted publishing with OIDC.
- Prefer npm trusted publishing where available.
- If a token is required, store it in an environment secret, never in the
  repository.
- The release environment requires manual approval.
- The release job uses a concurrency lock to prevent duplicate publishes.

## Caching

Bazel cache:

- Separate cache per operating system.
- Key includes the Bazel version, `MODULE.bazel.lock`, and build files.
- Restore keys are scoped to the OS and Bazel version.
- Cache is not shared between pull requests from forks and trusted branches.
- Cache contents are never treated as trusted build outputs.

Other caches:

- Python package cache for install tests.
- npm cache for consumer tests.
- No cache for compiler output.

## Matrix

| Dimension | PR fast lane | Main full lane | Release |
|---|---|---|---|
| OS | Windows, Linux | Windows, Linux | Windows, Linux |
| Python | 3.11, 3.14 | 3.11, 3.12, 3.13, 3.14 | 3.11 to 3.14 |
| Node | 22 | 22, 24 | 22, 24 |
| Typst | Optional | 0.15.1 | 0.15.1 |
| Compiler tests | If available | Required | Required |
| Install tests | No | Required | Required |
| Clean-checkout build | No | Required | Required |

The matrix is `CONFIRMED`. The pull request lane keeps the minimum and newest
Python versions to control runtime. The full lane covers every supported
Python and Node version. The release lane repeats the full lane against the
built artifacts.

The clean-checkout build job checks out the repository without any Bazel cache
and runs `bazel build //...` to prove the build does not depend on a warm
cache or on untracked files.

## Artifacts

| Artifact | Retention | Purpose |
|---|---|---|
| Test reports | 14 days | Debugging failed runs. |
| Benchmark JSON | 90 days | Trend comparison. |
| Wheel and sdist | 14 days in CI, permanent in release | Install tests and release. |
| npm tarball | 14 days in CI, permanent in release | Install tests and release. |
| Schema archive | 14 days in CI, permanent in release | Contract distribution. |
| SBOM | Permanent in release | Supply-chain record. |
| Checksums | Permanent in release | Verification. |

## Concurrency

- PR workflows cancel superseded runs for the same pull request.
- Main workflows do not cancel an in-progress release.
- Release workflows use a single concurrency group per tag.
- Release workflows do not run in parallel for the same version.

## Security

- PR workflows have read-only permissions.
- Release workflows use least privilege.
- Secrets are not printed.
- Logs do not include document content or asset contents.
- Fork pull requests do not receive secrets.
- Third-party actions are pinned to commit SHAs.
- Dependency review runs on pull requests where available.
- Secret scanning and push protection are enabled on the repository.

## Current state

| Item | Current |
|---|---|
| Workflows | None; only `.gitkeep`. |
| Cache | None. |
| Matrix | None. |
| Release environment | None. |
| Trusted publishing | None. |
| Required checks | None. |
| Published schema bundle | None; the release commit step is not implemented. |

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| CI-001 | The repository MUST have PR validation, main integration, and release workflows. | CONFIRMED | Workflow review. |
| CI-002 | PR workflows MUST have read-only permissions. | CONFIRMED | Workflow review. |
| CI-003 | PR workflows MUST NOT access publishing secrets. | CONFIRMED | Workflow review. |
| CI-004 | Main integration MUST run on every push to `main`. | CONFIRMED | Workflow review. |
| CI-005 | Release MUST run only on `v*` tags with manual approval. | CONFIRMED | Workflow review. |
| CI-006 | Release MUST verify version consistency before publishing. | CONFIRMED | Release check. |
| CI-007 | Release MUST build artifacts from the tagged commit. | CONFIRMED | Release check. |
| CI-008 | Release MUST run install tests before publishing. | CONFIRMED | Release check. |
| CI-009 | Release MUST use OIDC or environment secrets, never repository secrets. | CONFIRMED | Workflow review. |
| CI-010 | Bazel cache MUST be separated by OS. | CONFIRMED | Workflow review. |
| CI-011 | Cache keys MUST include Bazel version and lockfile. | CONFIRMED | Workflow review. |
| CI-012 | CI MUST run on Windows and Linux. | CONFIRMED | Matrix review. |
| CI-013 | Compiler integration MUST run on main and release. | CONFIRMED | Matrix review. |
| CI-014 | Documentation gate MUST run on PRs and main. | CONFIRMED | Workflow review. |
| CI-015 | Security checks MUST run on PRs where available. | CONFIRMED | Workflow review. |
| CI-016 | Release MUST attach checksums and SBOM. | CONFIRMED | Release check. |
| CI-017 | Release MUST use a concurrency lock. | CONFIRMED | Workflow review. |
| CI-018 | CI artifacts MUST have documented retention. | CONFIRMED | This document. |
| CI-019 | Third-party actions MUST be pinned. | CONFIRMED | Workflow review. |
| CI-020 | CI MUST NOT publish from pull requests. | CONFIRMED | Workflow review. |
| CI-021 | CI MUST report test results and logs for failures. | CONFIRMED | Workflow review. |
| CI-022 | CI MUST NOT print secrets or document content. | CONFIRMED | Review. |
| CI-023 | The release environment MUST require manual approval. | CONFIRMED | Environment settings. |
| CI-024 | The CI matrix MUST cover Windows and Linux, Python 3.11 to 3.14, Node.js 22 and 24, and Typst 0.15.1, with the pull request lane limited to the minimum and newest Python versions. | CONFIRMED | Matrix review. |
| CI-025 | The workflow files MUST be added in a separate implementation change. | CONFIRMED | Scope control. |
| CI-026 | The release lane MUST verify that the tagged commit contains the complete published schema bundle and that every published schema resolves at its versioned raw URL. | CONFIRMED | Release check. |

## Open questions

- Which GitHub-hosted runner images are used for Windows and Linux?
- Is a self-hosted runner needed for stable benchmarks?
- Which action versions and commit SHAs are approved?
- Is npm trusted publishing available for the chosen account?

## Related documents

- [Testing](testing.md)
- [Benchmarking](benchmarking.md)
- [Release](release.md)
- [Security](security.md)
- [Documentation](documentation.md)
- [ADR-0009](../decisions/ADR-0009-three-workflows-and-disk-cache.md)
- [ADR-0018](../decisions/ADR-0018-toolchain-and-ci-matrix.md)
- [ADR-0022](../decisions/ADR-0022-release-artifacts-schema-distribution-and-response-policy.md)
