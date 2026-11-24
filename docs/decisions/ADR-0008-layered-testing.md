# ADR-0008: Layered testing and shared fixtures

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The repository currently has seven unit tests for the schema generator. There are
no tests for the schema contract, model serialization, emitter output,
cross-language parity, compiler integration, or package installation.

The MVP needs confidence in both correctness and distribution. Running every test
on every pull request would be slow and flaky, especially compiler tests.

## Decision

Use layered testing with shared fixtures:

- Unit, schema, contract, golden, parity, negative, compiler integration,
  install, and compatibility layers.
- Shared JSON fixtures and expected `.typ` files for both SDKs.
- PR fast lane for unit, schema, contract, golden, parity, and pure negative
  tests.
- Main and release full lane for compiler integration, install, and
  compatibility.
- Compiler tests may be skipped locally when Typst is unavailable but are
  required in CI.
- Golden files are reviewed source artifacts, not regenerated silently.

## Consequences

- The contract is tested across languages.
- Compiler and packaging paths are verified before release.
- Fixture ownership and update rules are required.
- CI cost and runtime increase on main and release.
- Flaky tests must be fixed or quarantined, not silently retried.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Unit and golden only | Compiler and installation paths remain unverified. |
| Minimal unit tests | Does not prove parity or distribution. |
| Full end-to-end on every PR | Too slow and expensive for the MVP. |
| Generated-only tests | Do not catch semantic or cross-language drift. |

## References

- `docs/development/testing.md`
- `docs/development/ci-cd.md`
- `TEST-001` to `TEST-025`
- `CI-001` to `CI-025`
