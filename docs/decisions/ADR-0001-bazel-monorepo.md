# ADR-0001: Bazel monorepo and module boundaries

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

Typcast contains a Python code generator, a Python SDK, a TypeScript SDK, JSON
Schema sources, shared fixtures, and documentation. The Python and TypeScript
implementations must use the same contract and produce the same output. The
repository already uses Bazel, and `bazel build //...` and `bazel test //...`
are the verified commands.

The project needs one build graph, explicit inputs, and reproducible schema
generation without coupling the SDKs to each other.

## Decision

Keep Typcast as a Bazel monorepo with these boundaries:

- `specs/` owns the contract and does not depend on SDK code.
- `tools/codegen/` is a standalone Python package.
- `packages/python/` and `packages/typescript/` are independent SDK packages.
- `tests/` owns shared conformance and integration fixtures.
- `bazel/` owns reusable Starlark rules.
- `docs/` is independent of the build graph.

Python and TypeScript must not depend on each other. Both depend on the same
versioned contract artifacts.

## Consequences

- One command builds all targets.
- Schema generation has explicit inputs and cache invalidation.
- The SDKs can be released together with a shared version.
- Bazel adds a learning curve for contributors.
- Windows symlink support and cross-platform startup flags require care.
- The build graph must be kept clean; unused filegroups and implicit inputs are
  defects.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Separate repositories per SDK | Contract drift and release coordination become harder. |
| npm and pip workspaces only | No single build graph for schema generation and cross-language tests. |
| Code generation at install time | Consumers would need Bazel or a generator; reproducibility suffers. |
| One shared runtime package | Python and TypeScript cannot share a runtime implementation directly. |

## References

- `docs/architecture/repository.md`
- `docs/development/build.md`
- `REPO-001` to `REPO-012`
