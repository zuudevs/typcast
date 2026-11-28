# Architecture decision records

Status: living index
Last updated: 2026-11-27

This directory records the significant decisions behind the Typcast MVP. An ADR
explains why a decision was made; it does not replace the detailed specification.

## Index

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](ADR-0001-bazel-monorepo.md) | Bazel monorepo and module boundaries | Accepted |
| [ADR-0002](ADR-0002-hybrid-schema-and-builders.md) | Hybrid schema and idiomatic builders | Accepted |
| [ADR-0003](ADR-0003-typed-block-ir.md) | Typed block sequence and inline spans | Accepted |
| [ADR-0004](ADR-0004-immutable-model-and-builder.md) | Immutable model and fluent builder | Accepted |
| [ADR-0005](ADR-0005-two-phase-validation-and-diagnostics.md) | Two-phase validation and structured diagnostics | Accepted |
| [ADR-0006](ADR-0006-typst-cli-adapter.md) | Typst CLI adapter and tested range | Accepted |
| [ADR-0007](ADR-0007-lockstep-semver.md) | Lockstep SemVer and schema version | Accepted |
| [ADR-0008](ADR-0008-layered-testing.md) | Layered testing and shared fixtures | Accepted |
| [ADR-0009](ADR-0009-three-workflows-and-disk-cache.md) | Three workflows and disk cache | Accepted |
| [ADR-0010](ADR-0010-distribution-and-package-identity.md) | Distribution and package identity | Accepted |
| [ADR-0011](ADR-0011-apache-license.md) | Apache-2.0 license | Accepted |
| [ADR-0012](ADR-0012-explicit-asset-root-and-raw.md) | Explicit asset root and opaque raw Typst | Accepted |
| [ADR-0013](ADR-0013-documentation-gate-and-traceability.md) | Documentation gate and traceability | Accepted |
| [ADR-0014](ADR-0014-diagnostic-warning-policy.md) | Diagnostic warning policy | Accepted |
| [ADR-0015](ADR-0015-mutable-builder-contract.md) | Mutable builder contract | Accepted |
| [ADR-0016](ADR-0016-esm-only-npm-package.md) | ESM-only npm package | Accepted |
| [ADR-0017](ADR-0017-resource-limits.md) | Resource limits | Accepted |
| [ADR-0018](ADR-0018-toolchain-and-ci-matrix.md) | Toolchain and CI matrix | Accepted |
| [ADR-0019](ADR-0019-test-and-benchmark-policy.md) | Test and benchmark policy | Accepted |
| [ADR-0020](ADR-0020-release-artifact-and-response-policy.md) | Release artifact and response policy | Superseded by ADR-0022 |
| [ADR-0021](ADR-0021-schema-bundle-validation.md) | Schema bundle validation | Superseded by ADR-0023 |
| [ADR-0022](ADR-0022-release-artifacts-schema-distribution-and-response-policy.md) | Release artifacts, schema distribution, and response policy | Accepted |
| [ADR-0023](ADR-0023-schema-bundle-validation.md) | Schema bundle validation and published identity | Accepted |
| [ADR-0024](ADR-0024-semantic-validation-engine-and-configuration.md) | Semantic validation engine and its configuration | Superseded by ADR-0026 |
| [ADR-0026](ADR-0026-semantic-validation-engine-configuration-and-build.md) | Semantic validation engine, its configuration, and the build | Accepted |

## Template

```markdown
# ADR-0000: Title

Status: Proposed | Accepted | Superseded | Rejected
Date: YYYY-MM-DD
Supersedes: none
Superseded by: none

## Context

What problem or constraint requires a decision?

## Decision

What is decided? Use normative language where appropriate.

## Consequences

What becomes easier, harder, or impossible? What must be tested or documented?

## Alternatives considered

Which options were rejected, and why?

## References

Links to related documents, issues, or requirements.
```

## Rules

- An ADR has a unique number and is never renumbered.
- An accepted ADR is not edited to change its decision. A new ADR supersedes it.
- A superseded ADR remains in the repository and links to its replacement.
- Every accepted ADR is linked from at least one specification or architecture
  document.
- The index is updated in the same change as the ADR.
- ADRs record architecture and contract decisions. Process-only policies, such
  as the external link policy in `DOC-010` and the code of conduct in
  `GOV-018`, are recorded in the document that owns them and do not need an
  ADR.
