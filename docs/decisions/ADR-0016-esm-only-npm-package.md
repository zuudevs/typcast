# ADR-0016: ESM-only npm package

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The npm package must be consumable from JavaScript and TypeScript projects. The
earlier baseline left CommonJS support undecided.

The current `packages/typescript/package.json` already declares `"type":
"module"`, and the package is built from TypeScript with `aspect_rules_ts`.
Node.js 22 is the minimum supported runtime, where ESM is the default module
system.

## Decision

Publish an ESM-only package for `1.0.0`:

- The package exposes ESM entry points and type declarations.
- `package.json` keeps `"type": "module"` and declares `exports` with the ESM
  and types conditions.
- Named exports are used; there is no default export.
- CommonJS support is `DEFERRED` to a later minor version.
- If CommonJS is added later, it requires a separate consumer test and is
  released as a minor version.

## Consequences

- The package has one module format to test and document.
- CommonJS consumers need a dynamic `import()` or a transpilation step until a
  later release.
- A dual package is not published in the MVP, so there is no dual-package
  hazard where the same file is loaded through two module systems.
- The `exports` map is the only supported entry point definition.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Dual ESM and CommonJS build | Two module systems double the test matrix and create the dual-package hazard. |
| CommonJS only | Contradicts the existing `"type": "module"` manifest and modern Node.js defaults. |
| TypeScript source only, no build | Consumers would need a TypeScript toolchain at install time. |

## References

- `docs/specifications/sdk-api.md`
- `docs/specifications/compatibility.md`
- `docs/development/release.md`
- `API-019`, `API-025`, `COMPAT-017`
