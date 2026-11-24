# ADR-0007: Lockstep SemVer and schema version

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The project distributes a Python package, an npm package, and a JSON Schema
contract. Independent versions would make compatibility matrices complex. A
single version makes releases and support easier but couples schema evolution to
SDK releases.

## Decision

Use lockstep SemVer:

- Python, TypeScript, and schema share one version.
- Git tags use `vX.Y.Z`.
- Pre-releases use `vX.Y.Z-alpha.N` or `vX.Y.Z-beta.N`.
- Document IR carries `schemaVersion`.
- Breaking schema changes require a major version.
- Additive schema changes require a minor version.
- Clarifications and fixes use a patch version.
- The first stable release is `1.0.0`.

## Consequences

- One changelog and one release number.
- Version consistency is easy to check.
- The schema cannot evolve independently without a product release.
- A schema-only patch still requires a package release.
- Readers must reject unsupported major versions and newer minors with unknown
  fields.
- The mapping between `schemaVersion` and product version is `PROPOSED` as exact
  equality and `CONFIRMED` for the major version.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Independent schema version | More flexible but a larger compatibility matrix for a small MVP. |
| Permanent `0.x` | Inconsistent with a stable release goal. |
| Calendar versioning | Not compatible with SemVer expectations and registry tooling. |
| Git commit as version | Not user-friendly and not registry-compatible. |

## References

- `docs/specifications/compatibility.md`
- `docs/development/release.md`
- `REL-001` to `REL-004`
- `COMPAT-011` to `COMPAT-014`
