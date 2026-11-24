# Release

Status: PROPOSED
Scope: Normative
Last updated: 2026-11-24

## Purpose

This document defines how Typcast packages, versions, verifies, and publishes
the MVP. It is a specification only. No release workflow or publishing job is
active in the repository today.

## Release model

Typcast uses lockstep SemVer:

- Python package, npm package, and schema share one version.
- Git tags use `vX.Y.Z`.
- Pre-releases use `vX.Y.Z-alpha.N` or `vX.Y.Z-beta.N`.
- The first stable release is `1.0.0`.
- A pre-release may be published before `1.0.0`, but it does not satisfy the
  stable release gate.
- The schema is published from the tagged commit under `specs/schemas/` and is
  referenced through versioned raw URLs at that tag.

## Artifacts

| Artifact | Format | Target | Channel |
|---|---|---|---|
| Python wheel | `.whl` | `//packages/python:wheel` | PyPI |
| Python sdist | `.tar.gz` | `//packages/python:sdist` | PyPI |
| npm package | `.tgz` | `//packages/typescript:npm_package` | npm |
| Schema archive | `.tar.gz` | `//specs/schemas:archive` | GitHub Release |
| Published schema bundle | JSON files under `specs/schemas/` | `//specs/schemas:schema_bundle` | Tagged commit |
| Checksums | `SHA256SUMS` | Release assembly | GitHub Release |
| SBOM | CycloneDX 1.6 JSON | Release assembly | GitHub Release |
| License | `LICENSE` | Repository | GitHub Release and packages |
| Changelog | `CHANGELOG.md` | Repository | GitHub Release |

The target names and artifact set are `CONFIRMED`. The schema archive is a
gzip-compressed tarball so that it is identical on Windows and Linux. The
published schema bundle is the same file set, committed to the tagged commit so
that the versioned raw URLs resolve.

## Package metadata

### Python

`packages/python/pyproject.toml` must include:

- `name = "typcast"`.
- `version` matching the release tag.
- `description`.
- `readme`.
- `requires-python = ">=3.11"`.
- `license = "Apache-2.0"`.
- Authors or maintainers.
- Project URLs.
- Classifiers.
- Runtime dependencies, if any.
- `license-files`.

The wheel and sdist must include `LICENSE`.

### npm

`packages/typescript/package.json` must include:

- `name = "typcast"`.
- `version` matching the release tag.
- `description`.
- `license = "Apache-2.0"`.
- `type = "module"`.
- `engines.node = ">=22"`.
- `exports` with ESM and types.
- `main`, `module`, and `types` where applicable.
- `files` with the published files.
- `repository`, `homepage`, and `bugs`.
- `sideEffects = false`.
- `private` removed.

The npm tarball must include `LICENSE`.

The current manifest name is `@zuudevs/typcast` and `private` is `true`. Both
must change before publication.

## Version consistency

Before publishing, the release job checks:

- `MODULE.bazel` module version.
- Root `package.json` workspace version.
- `packages/python/pyproject.toml` version.
- `packages/typescript/package.json` version.
- The git tag without the `v` prefix.
- The changelog entry.
- The schema version in the release notes.
- The tagged commit contains the complete published schema bundle under
  `specs/schemas/`.

Any mismatch fails the release.

## Schema distribution

The canonical URL of a published schema file is:

```text
https://raw.githubusercontent.com/zuudevs/typcast/<VERSION>/specs/schemas/<SCHEMA_FILE>
```

- `<VERSION>` is the release tag, for example `v1.0.0`.
- `<SCHEMA_FILE>` is the path of the schema file relative to `specs/schemas/`.
- A `main` URL is a development reference only and is never a stable
  reference.
- A published tag is immutable. The tag MUST NOT be moved, reused, or deleted.
- The MVP does not register, host, or operate a dedicated schema domain.

The release prepares a release commit before it creates the tag. That commit
publishes the built bundle under `specs/schemas/` and sets the schema `$id`
values to the versioned raw URLs of the release. The tag points at that commit,
so every schema file and every `$ref` target resolves at the same tag.

The published paths and their sources are listed in
`specifications/schema.md`.

### Publishing the bundle

`//tools/publish:publish_schemas` writes the published bundle. It reads the
file list from the bundle manifest, so it publishes exactly the files of
`//specs/schemas:schema_bundle` and nothing else.

```shell
bazel build //specs/schemas:schema_bundle //specs/schemas:schema_manifest
bazel-bin/tools/publish/publish_schemas.exe publish \
  --version v1.0.0 \
  --input bazel-bin/specs/schemas \
  --manifest bazel-bin/specs/schemas/schema_manifest.txt \
  --output specs/schemas
```

The publisher sets the `$id` of every file to its versioned raw URL and keeps
the relative path of the file. It rejects a version that is not a release tag,
so a `main` URL can never be published.

The release lane verifies the result against the build before the tag is
created.

```shell
bazel-bin/tools/publish/publish_schemas.exe check \
  --version v1.0.0 \
  --input bazel-bin/specs/schemas \
  --manifest bazel-bin/specs/schemas/schema_manifest.txt \
  --published specs/schemas
```

The check reports a missing file, a file that differs from the build, and a
file that the bundle does not contain. It fails the release when any of them
is found.

## Release gates

| Gate | Requirement |
|---|---|
| Build | `bazel build //...` passes on Windows and Linux. |
| Unit and contract tests | All pass. |
| Schema tests | Bundle and all `$ref` values validate. |
| Schema distribution | The tagged commit contains the complete published bundle under `specs/schemas/`. |
| Golden and parity tests | Python and TypeScript output match. |
| Compiler integration | Supported Typst version compiles all fixtures. |
| Install tests | Wheel and npm tarball work in clean environments. |
| Documentation | Docs gate passes. |
| Security | Secret scanning and dependency review pass. |
| License | `LICENSE` present in repository and packages. |
| Changelog | Entry exists and is reviewed. |
| Version | All manifests and tag agree. |
| Approval | Release environment approved by a maintainer. |

## Release process

1. Confirm the release scope and changelog.
2. Run the full test lane on Windows and Linux.
3. Build wheel, sdist, npm tarball, schema archive, SBOM, and checksums.
4. Run install tests against the built artifacts.
5. Verify the supported Typst version.
6. Prepare the release commit: publish the built bundle under `specs/schemas/`
   and set the schema `$id` values to the versioned raw URLs.
7. Create a signed or annotated tag `vX.Y.Z` on that commit.
8. Push the tag.
9. Approve the protected release environment.
10. Publish Python to PyPI.
11. Publish the npm package.
12. Create the GitHub Release.
13. Attach artifacts, checksums, SBOM, and license.
14. Verify the published artifacts by installing them again, and fetch every
    published schema from its versioned raw URL and compare it with the release
    bundle.
15. Announce the release and record known issues.

## Publishing security

- Prefer PyPI trusted publishing with OIDC.
- Prefer npm trusted publishing or provenance where available.
- Use environment secrets only when OIDC is unavailable.
- Never store registry tokens in the repository.
- Release jobs use least privilege.
- Release jobs use a concurrency lock.
- Release jobs do not run on pull requests.
- Build artifacts from the tagged commit only.
- Do not publish from a dirty working tree.
- Do not publish if any gate fails.

## Checksums and SBOM

- Generate SHA-256 checksums for every release artifact.
- Publish `SHA256SUMS` as a release asset.
- Generate an SBOM in CycloneDX 1.6 JSON.
- Include direct and transitive dependencies where tooling allows.
- Record the Typst version used for verification.
- Record the Bazel version and lockfile hash.
- Artifact signing and SLSA provenance are Post-MVP.

## Pre-release and stable release

Pre-release:

- Version `1.0.0-alpha.N` or `1.0.0-beta.N`.
- Published to PyPI and npm with a pre-release tag.
- Not marked as latest.
- Used to validate installation and compiler behavior.
- Does not satisfy the `1.0.0` gate.

Stable `1.0.0`:

- All gates pass.
- Documentation is complete for the MVP scope.
- No open blocker defects.
- Supported Typst range is verified.
- Package names are final.
- License and security policy are present.

## Rollback and yank

- PyPI releases can be yanked, not deleted, when a critical defect is found.
- npm versions can be deprecated; unpublishing is avoided.
- GitHub Releases can be edited or marked as pre-release.
- A rollback release uses a new patch version.
- A security advisory is published when appropriate.
- Users are notified through release notes and the security policy.

## Current state

| Item | Current |
|---|---|
| Python version | `0.1.0`. |
| npm version | `0.1.0`. |
| npm name | `@zuudevs/typcast`. |
| npm private | `true`. |
| Packaging targets | None. |
| Release workflow | None. |
| Changelog | `CHANGELOG.md` present at the repository root. It has no released entry yet. |
| License | `LICENSE` present at the repository root. |
| Security policy | `SECURITY.md` present at the repository root. |
| Tag | None. |
| Schema archive | None. |
| Published schema bundle | None. The publisher exists, but the release commit step is not implemented. |
| Schema domain | None. The MVP does not require a dedicated schema domain. |
| SBOM | None. |

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| REL-001 | Python, npm, and schema versions MUST be lockstep. | CONFIRMED | Version check. |
| REL-002 | Release tags MUST use `vX.Y.Z`. | CONFIRMED | Tag check. |
| REL-003 | The first stable release MUST be `1.0.0`. | CONFIRMED | Release review. |
| REL-004 | Pre-releases MUST use `-alpha.N` or `-beta.N`. | CONFIRMED | Tag check. |
| REL-005 | The release MUST produce a wheel and sdist. | CONFIRMED | Artifact check. |
| REL-006 | The release MUST produce an npm tarball. | CONFIRMED | Artifact check. |
| REL-007 | The release MUST produce a schema archive. | CONFIRMED | Artifact check. |
| REL-008 | The release MUST publish SHA-256 checksums. | CONFIRMED | Artifact check. |
| REL-009 | The release MUST publish an SBOM. | CONFIRMED | Artifact check. |
| REL-010 | The release MUST include `LICENSE`. | CONFIRMED | Package check. |
| REL-011 | The release MUST include a changelog entry. | CONFIRMED | Release check. |
| REL-012 | The release MUST verify all package versions and the tag. | CONFIRMED | Release check. |
| REL-013 | The release MUST run install tests before publishing. | CONFIRMED | Release check. |
| REL-014 | The release MUST use OIDC or environment secrets. | CONFIRMED | Workflow review. |
| REL-015 | The release MUST use a protected environment. | CONFIRMED | Environment settings. |
| REL-016 | The release MUST NOT publish from a pull request. | CONFIRMED | Workflow review. |
| REL-017 | The release MUST build from the tagged commit. | CONFIRMED | Release check. |
| REL-018 | The release MUST NOT publish when a gate fails. | CONFIRMED | Release check. |
| REL-019 | The npm package name MUST be `typcast`. | CONFIRMED | Manifest check. |
| REL-020 | The npm package MUST not be private. | CONFIRMED | Manifest check. |
| REL-021 | The Python package name MUST be `typcast`. | CONFIRMED | Manifest check. |
| REL-022 | The Python package MUST declare Apache-2.0. | CONFIRMED | Manifest check. |
| REL-023 | The npm package MUST declare Apache-2.0. | CONFIRMED | Manifest check. |
| REL-024 | The release MUST record the Typst version used for verification. | CONFIRMED | Release notes. |
| REL-025 | Rollback MUST use a new patch release, not deletion. | CONFIRMED | Process review. |
| REL-026 | Artifact signing and SLSA provenance MUST be Post-MVP. | DEFERRED | Scope review. |
| REL-027 | The artifact target names MUST be `//packages/python:wheel`, `//packages/python:sdist`, `//packages/typescript:npm_package`, and `//specs/schemas:archive`. | CONFIRMED | Build review. |
| REL-028 | The SBOM MUST be generated in CycloneDX 1.6 JSON and attached to the release. | CONFIRMED | Release check. |
| REL-029 | The canonical schema reference MUST be the versioned raw URL `https://raw.githubusercontent.com/zuudevs/typcast/<VERSION>/specs/schemas/<SCHEMA_FILE>`, where `<VERSION>` is the release tag; the MVP MUST NOT require a dedicated schema domain or hosting infrastructure. | CONFIRMED | Release check. |
| REL-030 | The tagged release commit MUST contain the complete published schema bundle under `specs/schemas/`, so that every schema file is retrievable at its versioned raw URL. | CONFIRMED | Release check. |
| REL-031 | A published release tag MUST NOT be moved, reused, or deleted; a schema correction MUST ship in a new release tag. | CONFIRMED | Release check. |
| REL-032 | The publisher MUST set the `$id` of every published schema to the versioned raw URL of the release tag, MUST publish exactly the files of the bundle, and MUST reject a version that is not a release tag. | IMPLEMENTED | `//tools/publish:publish_schemas`; `//tools/publish/tests:publish_tests`. |

## Open questions

- Is the first public release an alpha, a beta, or `1.0.0` directly?
- Which tool generates the CycloneDX SBOM?
- Is npm trusted publishing available for the account?
- What is the exact support window for old minor versions?

## Related documents

- [Compatibility](../specifications/compatibility.md)
- [Schema contract](../specifications/schema.md)
- [CI/CD](ci-cd.md)
- [Security](security.md)
- [Build](build.md)
- [ADR-0007](../decisions/ADR-0007-lockstep-semver.md)
- [ADR-0010](../decisions/ADR-0010-distribution-and-package-identity.md)
- [ADR-0022](../decisions/ADR-0022-release-artifacts-schema-distribution-and-response-policy.md)
- [ADR-0023](../decisions/ADR-0023-schema-bundle-validation.md)
