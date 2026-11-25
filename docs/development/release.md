# Release

Status: PROPOSED
Scope: Normative
Last updated: 2026-11-24

## Purpose

This document defines how Typcast packages, versions, verifies, and publishes
the MVP. The verification lane is active in the repository, and the release
preparation is a repository command. No publishing job is active yet, because
the packaging targets do not exist.

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
- The contract version in the `$id` of every schema source.
- The tagged commit contains the complete published schema bundle under
  `specs/schemas/`.

Any mismatch fails the release.

`//scripts:check_version` performs the version part of the check. It compares
the four manifests, the contract version of every schema source, and the
changelog with the tag, and it reports every mismatch at once.

```shell
bazel run //scripts:check_version -- --version v1.0.0
```

The check runs with the hermetic Python toolchain and needs no network access.
The release lane runs it before it builds the tagged commit.

## Preparing the release commit

The release commit is the commit that the release tag points at. It carries
the published schema bundle under `specs/schemas/`, so that every versioned
raw URL resolves at the tag.

`//scripts:prepare_release` prepares that commit. It sets the release version
in every manifest and in every schema source, publishes the built bundle
under `specs/schemas/`, and verifies the result. The command creates neither
a commit nor a tag.

The procedure has six steps.

1. Write the changelog entry of the release. The command refuses to run
   without it, because a release without an entry has no notes.

2. Set the version and build the bundle. The build carries the identity of
   the sources, so it must run after the version is set.

   ```shell
   bazel run //scripts:prepare_release -- --version v1.0.0 --root "$PWD"
   bazel build //specs/schemas:schema_bundle //specs/schemas:schema_manifest
   ```

3. Publish the bundle and verify the result. The command reports a mismatch
   between the published bundle and the build, and a mismatch between the
   archive of the published bundle and the archive of the build.

   ```shell
   bazel run //scripts:prepare_release -- --version v1.0.0 --root "$PWD" \
     --bundle "$PWD/bazel-bin/specs/schemas" \
     --manifest "$PWD/bazel-bin/specs/schemas/schema_manifest.txt"
   ```

4. Commit the result and tag it.

   ```shell
   git add -A
   git commit -m "release: v1.0.0"
   git tag v1.0.0
   git push origin v1.0.0
   ```

5. Remove the generated published files and commit the removal. The published
   bundle is a release artifact, and the development branch must not carry the
   files that the build generates (`BUILD-009`, `REPO-007`). The cleanup
   changes no version and no source, so it is safe to run on the development
   branch.

   ```shell
   bazel run //scripts:prepare_release -- --version v1.0.0 --root "$PWD" \
     --manifest "$PWD/bazel-bin/specs/schemas/schema_manifest.txt" --clean
   git add -A
   git commit -m "chore(release): remove the generated published bundle"
   git push origin main
   ```

6. Watch the release lane. It checks out the tag and verifies the release.

The tag points at the release commit, so the published bundle stays reachable
at the versioned raw URLs, whatever happens to the development branch
afterwards.

The command is idempotent: a second run reports no change. The `--dry-run`
flag reports the changes without writing them.

### The rehearsal of the release commit

`//scripts/tests:release_flow_tests` rehearses the procedure. It copies the
real manifests, the real schema sources, and the bundle of the build into a
temporary tree, prepares the release there, and checks the published bundle,
the identities, the archive, and the cleanup. The test never writes into the
checkout, and it publishes nothing.

The rehearsal runs in `bazel test //...`, so the path of the release lane runs
on Windows and Linux in every test lane, before the first tag exists.

### What the release commit carries

| File | Change |
|---|---|
| `MODULE.bazel`, `package.json`, `packages/python/pyproject.toml`, `packages/typescript/package.json` | The release version. |
| `specs/schemas/validator.schema.json`, `specs/schemas/definitions/bound.schema.json`, `specs/schemas/definitions/node.schema.json` | The identity of the release tag. The published file has the same content, so the file does not change when the version is already set. |
| `specs/schemas/templates/api/types/alignment.schema.json.tmpl`, `length.schema.json.tmpl`, `paper.schema.json.tmpl` | The identity of the release tag, which is the contract version. The versions are lockstep (`REL-001`). |
| `specs/schemas/api/types/alignment.schema.json`, `length.schema.json`, `paper.schema.json` | The published files of the generated schemas. They are new files in the release commit. |

The three generated files are the only files that the published bundle adds
to the repository. The cleanup of step five removes them again, so the
development branch carries the sources and the templates only.

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

### Verifying the published URLs

The release lane also fetches every published schema from its versioned raw
URL and compares the served bytes with the file that the tagged commit
carries.

```shell
bazel-bin/tools/publish/publish_schemas.exe verify \
  --version v1.0.0 \
  --manifest bazel-bin/specs/schemas/schema_manifest.txt \
  --published specs/schemas
```

A file that does not resolve, or that resolves to a different content, fails
the check. The command uses the network, so it belongs to the release lane and
not to the repository checks.

### The schema archive

`//specs/schemas:archive` packages the bundle as a gzip-compressed tarball for
the GitHub Release asset.

```shell
bazel build //specs/schemas:archive
```

The archive is deterministic: the member order, the member metadata, and the
gzip header are fixed, so the bytes and the checksum of the asset are the same
on Windows and on Linux. The rules are listed in `development/build.md`.

The release lane archives the published bundle of the tagged commit, so that
the asset carries exactly the files that the versioned raw URLs serve.

```shell
bazel-bin/tools/publish/publish_schemas.exe archive \
  --input specs/schemas \
  --manifest bazel-bin/specs/schemas/schema_manifest.txt \
  --output typcast-schemas-v1.0.0.tar.gz
```

The command keeps the content of every file as it is, including the identity
of the release tag that the publisher wrote. The release attaches the archive
and its SHA-256 checksum to the GitHub Release.

The release lane compares the archive of the published bundle with the archive
of the build. The two archives must be identical, so that the asset carries
exactly the files that the build produced and that the identity of every file
names the release tag.

```shell
bazel-bin/tools/publish/publish_schemas.exe compare-archives \
  --input bazel-bin/specs/schemas \
  --manifest bazel-bin/specs/schemas/schema_manifest.txt \
  --published specs/schemas
```

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
| Version | All manifests, all schema sources, and the tag agree. |
| Preparation | `//scripts:prepare_release` publishes the bundle and verifies the result. |
| Approval | Release environment approved by a maintainer. |

## Release process

1. Confirm the release scope and changelog.
2. Run the full test lane on Windows and Linux.
3. Build wheel, sdist, npm tarball, schema archive, SBOM, and checksums.
4. Run install tests against the built artifacts.
5. Verify the supported Typst version.
6. Prepare the release commit: run `//scripts:prepare_release`, which sets the
   release version and publishes the built bundle under `specs/schemas/` with
   the versioned raw URLs as the schema `$id` values.
7. Create a signed or annotated tag `vX.Y.Z` on that commit.
8. Push the tag.
9. Remove the generated published files from the development branch with
   `//scripts:prepare_release --clean`.
10. Approve the protected release environment.
11. Publish Python to PyPI.
12. Publish the npm package.
13. Create the GitHub Release.
14. Attach artifacts, checksums, SBOM, and license.
15. Verify the published artifacts by installing them again, and fetch every
    published schema from its versioned raw URL and compare it with the release
    bundle.
16. Announce the release and record known issues.

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
| Schema contract version | `1.0.0`. The publisher replaces it with the release tag. |
| Packaging targets | None. |
| Release workflow | `.github/workflows/release.yml` verifies the release. It does not publish yet. |
| Version check | `//scripts:check_version` compares the manifests, the contract version of every schema source, and the changelog with the tag. |
| Release preparation | `//scripts:prepare_release` sets the release version, publishes the bundle, and verifies the result. The command is ready; no release has run. |
| Changelog | `CHANGELOG.md` present at the repository root. It has no released entry yet. |
| License | `LICENSE` present at the repository root. |
| Security policy | `SECURITY.md` present at the repository root. |
| Tag | None. |
| Schema archive | `//specs/schemas:archive` builds a deterministic gzip tarball of the bundle. The release asset is produced by the same code from the published bundle. |
| Published schema bundle | None. The publisher and the preparation command exist, but no release commit exists yet. |
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
| REL-007 | The release MUST produce a schema archive as a gzip-compressed tarball whose bytes are identical on every platform. | CONFIRMED | Artifact check. |
| REL-008 | The release MUST publish SHA-256 checksums. | CONFIRMED | Artifact check. |
| REL-009 | The release MUST publish an SBOM. | CONFIRMED | Artifact check. |
| REL-010 | The release MUST include `LICENSE`. | CONFIRMED | Package check. |
| REL-011 | The release MUST include a changelog entry. | CONFIRMED | Release check. |
| REL-012 | The release MUST verify all package versions and the tag. | IMPLEMENTED | `//scripts:check_version`; the release lane checks out the tag and runs the check. |
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
| REL-030 | The tagged release commit MUST contain the complete published schema bundle under `specs/schemas/`, so that every schema file is retrievable at its versioned raw URL. | CONFIRMED | The preparation command publishes the bundle; the release lane checks the tagged commit. |
| REL-031 | A published release tag MUST NOT be moved, reused, or deleted; a schema correction MUST ship in a new release tag. | CONFIRMED | Release check. |
| REL-032 | The publisher MUST set the `$id` of every published schema to the versioned raw URL of the release tag, MUST publish exactly the files of the bundle, and MUST reject a version that is not a release tag. | IMPLEMENTED | `//tools/publish:publish_schemas`; `//tools/publish/tests:publish_tests`. |
| REL-033 | The release MUST compare the version of every manifest, the contract version of every schema source, and the changelog with the tag, and MUST fail when one of them differs. | IMPLEMENTED | `//scripts:check_version`; `//scripts/tests:version_tests`; 15 cases. |
| REL-034 | The release MUST verify that every published schema resolves at its versioned raw URL and serves the content of the tagged commit. | IMPLEMENTED | `publish_schemas verify`; `//tools/publish/tests:publish_tests`. |
| REL-035 | The release MUST attach the schema archive of the published bundle as a GitHub Release asset, and the archive MUST be byte-identical on every platform. | CONFIRMED | The archive is deterministic and the release lane compares the archives; the asset is attached with the publishing jobs. |
| REL-036 | The release preparation MUST be a repository command that sets the release version in every manifest and in every schema source, publishes the built bundle under `specs/schemas/`, verifies the version consistency, the published bundle, and the archive, and removes the generated published files from the development branch. | IMPLEMENTED | `//scripts:prepare_release`; `//scripts/tests:release_tests`; 20 cases. The rehearsal `//scripts/tests:release_flow_tests` runs the path with the files of the repository and the bundle of the build. |

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
