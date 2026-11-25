# ADR-0022: Release artifacts, schema distribution, and response policy

Status: Accepted
Date: 2026-11-24
Supersedes: ADR-0020
Superseded by: none

## Context

The first stable release must be reproducible, verifiable, and supported by a
defensible security response process. ADR-0020 fixed the artifact target names,
the SBOM format, and the vulnerability response expectations. It also required
a dedicated schema publishing domain, `schemas.typcast.dev`, to be registered
and to serve the published schema archive.

The dedicated domain has two problems. It requires registration, DNS, TLS,
hosting, and renewal before the project has published anything, and it adds an
operational dependency that no release process currently owns. The repository
already lives on GitHub, and GitHub serves repository content at stable,
versioned URLs. A release tag is an immutable, addressable version of the
repository content.

The schema bundle is not fully present in the source tree. Three schema files
are generated from templates by Bazel and exist only in the build output. A raw
URL can serve only files that exist in the tagged commit, so the release must
publish the built bundle into the tagged commit.

## Decision

Release artifacts:

| Artifact | Target |
|---|---|
| Python wheel | `//packages/python:wheel` |
| Python source distribution | `//packages/python:sdist` |
| npm tarball | `//packages/typescript:npm_package` |
| Schema archive | `//specs/schemas:archive` |
| Published schema bundle | `//specs/schemas:schema_bundle` in the tagged commit |

- The schema archive is a gzip-compressed tarball so that it is identical on
  Windows and Linux.
- The SBOM is generated in CycloneDX 1.6 JSON and attached to the release.
- SHA-256 checksums are published as `SHA256SUMS`.
- Artifact signing and SLSA provenance remain Post-MVP.

Schema distribution:

- The canonical published URL of a schema file is
  `https://raw.githubusercontent.com/zuudevs/typcast/<VERSION>/specs/schemas/<SCHEMA_FILE>`.
- `<VERSION>` is the Git release tag that publishes the schema, for example
  `v1.0.0`.
- `<SCHEMA_FILE>` is the path of the schema file relative to `specs/schemas/`,
  for example `validator.schema.json` or `api/types/paper.schema.json`.
- The tagged commit contains the complete published bundle under
  `specs/schemas/`, so every schema file and every `$ref` target resolves at
  the same tag.
- A `main` URL is a development reference only. It is not a stable reference
  and MUST NOT be published as one.
- A published release tag is immutable. The tag MUST NOT be moved, reused, or
  deleted, and a correction ships in a new tag.
- Consumers pin an exact release tag. A breaking schema change requires a
  major version, so the pinned tag identifies the contract unambiguously.
- The MVP does not register, host, or operate a dedicated schema domain. No
  DNS, TLS, hosting, or renewal is required to publish a schema.

Vulnerability response:

- Reports are received through GitHub private vulnerability reporting. Public
  issues are not used for vulnerabilities.
- Acknowledgement within 3 business days, triage within 7 business days, a
  fix or mitigation plan for critical and high severity issues within 14
  calendar days, and a fix release within 30 calendar days.
- The coordinated disclosure window after a fix ships is 90 days.
- Severity is assessed with CVSS 3.1 as a starting point.

## Consequences

- The release job has a fixed artifact list with fixed target names.
- Consumers can verify artifacts with checksums and inspect dependencies
  through the SBOM.
- The schema contract has a stable, absolute identity from the first release
  without any hosting setup.
- The release gains a pre-tag step. The bundle is published into the release
  commit before the tag is created.
- The published bundle in the tagged commit is a second copy of the generated
  schema files and MUST be verified against the Bazel build.
- A URL that resolves for one release keeps resolving for that release, so a
  consumer that pins a tag is not affected by later schema work.
- A schema file added in a later release is reachable only after that release
  is tagged.
- The security policy states measurable expectations rather than an intention.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| SPDX JSON instead of CycloneDX | Both are acceptable; CycloneDX tooling has broader adoption for dependency graphs. |
| Zip archive for the schemas | Tarball output is byte-identical across platforms, which matters for checksums. |
| A dedicated schema domain such as `schemas.typcast.dev` | It requires registration, DNS, TLS, hosting, and renewal before the first release, and adds an operational dependency with no MVP benefit. |
| A `typcast.local` placeholder domain | Not a registrable domain, so the `$id` values would not be resolvable in practice. |
| Public issue tracker for vulnerabilities | Disclosure would be immediate and unpatched. |

## References

- `docs/development/release.md`
- `docs/specifications/schema.md`
- `docs/development/security.md`
- `SECURITY.md`
- `BUILD-014`, `BUILD-016`, `REL-007`, `REL-027`, `REL-028`, `REL-029`,
  `REL-030`, `REL-031`
- `SEC-024`, `SEC-025`
