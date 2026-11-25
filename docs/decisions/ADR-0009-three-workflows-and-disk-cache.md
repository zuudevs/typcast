# ADR-0009: Three workflows and disk cache

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The repository has no CI workflows. A release will publish to PyPI and npm, so
publishing credentials must never be available to pull request code. The build
uses Bazel and can be expensive without caching.

## Decision

Use three separate GitHub Actions workflows:

- PR validation with read-only permissions.
- Main integration with read-only permissions and the full test lane.
- Tag-triggered release with a protected environment and least-privilege write
  permissions.

Use a Bazel disk cache per operating system, keyed by Bazel version, lockfile,
and build files. Do not use a remote cache or remote execution in the MVP.

## Consequences

- Publishing is isolated from pull requests.
- Workflow configuration has some duplication.
- Main branch is verified continuously.
- Cold builds are slower, but the cache is simple and auditable.
- Remote cache and remote execution remain Post-MVP.
- Branch protection and required checks become part of governance.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Single conditional workflow | Complex conditions and higher risk of accidental publish. |
| PR and release only | Main branch would not be continuously verified. |
| Manual release only | Not reproducible and prone to human error. |
| Remote cache in the MVP | Adds cost, security, and isolation complexity. |

## References

- `docs/development/ci-cd.md`
- `docs/development/build.md`
- `CI-001` to `CI-025`
- `BUILD-019`
