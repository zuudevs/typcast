# ADR-0010: Distribution and package identity

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The SDK must be installable by Python and JavaScript/TypeScript users. The
repository currently has a Python `py_library` and a TypeScript `ts_project`, but
no wheel, sdist, npm tarball, schema archive, or release workflow. The TypeScript
manifest is private and uses the name `@zuudevs/typcast`.

## Decision

Distribute:

- Python wheel and sdist to PyPI.
- TypeScript/JavaScript package to npm.
- Schema archive, checksums, SBOM, and license to GitHub Releases.

Use the package name `typcast` on both PyPI and npm. Use `typcast` as the Python
import path and the npm package name. Register `@typcast` only for future
additional packages.

## Consequences

- Installation is `pip install typcast` and `npm install typcast`.
- The TypeScript manifest must change from `@zuudevs/typcast` and become public.
- Package metadata, entry points, and license files must be completed.
- Trusted publishing or protected environment secrets are required.
- Registry name availability must be rechecked before the first publish.
- GitHub Actions Artifacts are not a distribution channel.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| GitHub Packages for both | Consumers need registry configuration; Python index support is limited. |
| GitHub Releases only | No standard `pip install` or `npm install` by name. |
| Private registry | Contradicts the public distribution goal. |
| Scoped npm package `@typcast/core` | Adds npm organization setup and a longer install name for the MVP. |

## References

- `docs/development/release.md`
- `docs/specifications/compatibility.md`
- `REL-005` to `REL-023`
- `CI-016`
