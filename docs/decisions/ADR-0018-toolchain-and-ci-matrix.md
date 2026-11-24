# ADR-0018: Toolchain and CI matrix

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The MVP must publish Python and npm packages that work on a defined set of
runtimes and operating systems. The earlier baseline left the CI matrix open
and flagged two build-graph risks: the unconditional Windows symlink startup
flag, and the absence of a clean-checkout build.

The repository currently has 12 Bazel rules, no CI workflows, and no evidence
of a Linux build.

## Decision

Fix the support and verification matrix:

| Dimension | Pull request lane | Main and release lane |
|---|---|---|
| OS | Windows, Linux | Windows, Linux |
| Python | 3.11, 3.14 | 3.11, 3.12, 3.13, 3.14 |
| Node.js | 22 | 22, 24 |
| Typst | Optional | 0.15.1 |

Additional decisions:

- The supported Typst range is `>=0.15.0 <0.16.0`, tested with 0.15.1.
- `.bazelrc` keeps `startup --windows_enable_symlinks`, because the
  `typcast_schema_copy` symlink action requires it on Windows. The first Linux
  CI run must prove that Bazel starts with this flag. If the flag is rejected
  on Linux, it moves to a Windows-only rc file and Linux uses the default.
- CI runs a clean-checkout build with no Bazel cache to prove the build does
  not depend on a warm cache or on untracked files.
- CI caches Bazel outputs per operating system, keyed by the Bazel version,
  `MODULE.bazel.lock`, and the build files.
- Remote cache and remote execution are `DEFERRED`.

## Consequences

- The supported surface is explicit and testable.
- The pull request lane stays fast by testing only the minimum and newest
  Python versions.
- The Linux build is proven before the first release instead of assumed.
- The symlink flag question is resolved by evidence rather than by guesswork.
- A larger matrix increases CI cost, which is reviewed after the first full
  run.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Test every Python version on every pull request | Too slow for the MVP's fast lane. |
| Windows-only CI | The release would ship without Linux evidence. |
| Move the symlink flag immediately | It is required on Windows, and the failure mode on Linux is unknown until it is tested. |
| Remote cache from the start | Adds isolation and cost complexity that the MVP does not need. |

## References

- `docs/specifications/compatibility.md`
- `docs/development/build.md`
- `docs/development/ci-cd.md`
- `COMPAT-008`, `COMPAT-016`, `BUILD-012`, `BUILD-018`, `BUILD-019`, `CI-024`
- `ADR-0009`
