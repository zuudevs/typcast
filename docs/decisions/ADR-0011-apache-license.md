# ADR-0011: Apache-2.0 license

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

Typcast will publish packages to PyPI and npm. The repository currently has no
`LICENSE` file. The license determines usage, redistribution, patent rights, and
contribution terms. Typst itself uses Apache-2.0.

## Decision

Use Apache License 2.0 for the repository and published artifacts.

## Consequences

- Add `LICENSE` at the repository root.
- Declare `Apache-2.0` in `pyproject.toml` and `package.json`.
- Include the license in wheel, sdist, npm tarball, and release assets.
- Add `NOTICE` only if third-party content requires it.
- Maintain a dependency license inventory compatible with Apache-2.0.
- A license change requires an explicit decision and a major version.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| MIT | Simpler, but no explicit patent grant. |
| Dual MIT OR Apache-2.0 | More compatibility, but more metadata and documentation complexity. |
| Proprietary | Contradicts public distribution and open adoption. |
| No license | Cannot be safely used or redistributed. |

## References

- `docs/development/security.md`
- `docs/development/release.md`
- `SEC-001` to `SEC-003`
- `REL-010`, `REL-022`, `REL-023`
