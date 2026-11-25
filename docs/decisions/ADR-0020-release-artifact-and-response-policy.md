# ADR-0020: Release artifact and response policy

Status: Superseded
Date: 2026-11-24
Supersedes: none
Superseded by: ADR-0022

> Superseded by
> [ADR-0022](ADR-0022-release-artifacts-schema-distribution-and-response-policy.md).
> The schema publishing domain decision is replaced by versioned GitHub Raw
> URLs. The artifact targets, the SBOM format, and the vulnerability response
> policy are restated unchanged in ADR-0022.

## Context

The first stable release must be reproducible, verifiable, and supported by a
defensible security response process. The earlier baseline left the artifact
target names, the SBOM format, the schema publishing domain, and the
vulnerability response expectations open.

The repository now contains `LICENSE` and `SECURITY.md`, but it has no
packaging targets, no release workflow, and no registered publishing domain.

## Decision

Release artifacts:

| Artifact | Target |
|---|---|
| Python wheel | `//packages/python:wheel` |
| Python source distribution | `//packages/python:sdist` |
| npm tarball | `//packages/typescript:npm_package` |
| Schema archive | `//specs/schemas:archive` |

- The schema archive is a gzip-compressed tarball so that it is identical on
  Windows and Linux.
- The SBOM is generated in CycloneDX 1.6 JSON and attached to the release.
- SHA-256 checksums are published as `SHA256SUMS`.
- The canonical schema `$id` base URI is `https://schemas.typcast.dev/`. The
  domain must be registered and must serve the published schema archive before
  the first stable release.
- Artifact signing and SLSA provenance remain Post-MVP.

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
- The schema contract has a stable, absolute identity from the first release.
- The security policy states measurable expectations rather than an intention.
- The domain registration is a release prerequisite and must be tracked by the
  maintainer.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| SPDX JSON instead of CycloneDX | Both are acceptable; CycloneDX tooling has broader adoption for dependency graphs. |
| Zip archive for the schemas | Tarball output is byte-identical across platforms, which matters for checksums. |
| A `typcast.local` placeholder domain | Not a registrable domain, so the `$id` values would not be resolvable in practice. |
| Public issue tracker for vulnerabilities | Disclosure would be immediate and unpatched. |

## References

- `docs/development/release.md`
- `docs/development/security.md`
- `docs/specifications/schema.md`
- `SECURITY.md`
- `BUILD-014`, `BUILD-015`, `BUILD-016`, `REL-027`, `REL-028`, `REL-029`
- `SEC-024`, `SEC-025`
