# ADR-0012: Explicit asset root and opaque raw Typst

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

Reports need images and local Typst modules. The SDK could resolve paths relative
to the current working directory, embed assets in the IR, fetch remote URLs, or
require an explicit asset root. Each choice affects portability, security, and
compiler workspace design.

The MVP also needs an escape hatch for Typst features outside the core node set.
Parsing and validating raw Typst would add a compiler dependency to the SDK.

## Decision

Use:

- An explicit `assetRoot` for validation and compilation.
- Relative, normalized POSIX paths in the IR.
- Rejection of absolute paths, UNC paths, URIs, data URIs, and traversal.
- Symlink checks after real-path resolution.
- No remote assets in the MVP.
- A temporary compiler workspace that mirrors relative paths.
- Opaque raw Typst blocks and spans with `markup`, `code`, and `math` formats.
- Raw content validation limited to non-empty, UTF-8, and size limits.
- Raw content emitted verbatim and treated as trusted input.

## Consequences

- Asset resolution is portable and testable.
- Users must configure an asset root.
- Path traversal and symlink escapes are rejected before reads.
- Raw Typst can express features outside the typed API.
- Raw Typst is not sandboxed by Typcast; untrusted input needs an external
  sandbox.
- Remote assets, embedding, and parser-validated raw are Post-MVP.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| CWD-relative paths | Fragile and dependent on process launch. |
| Embedded base64 assets | Bloats JSON and complicates the schema and performance. |
| Remote URLs | Network, cache, security, and reproducibility complexity. |
| Parser-validated raw | Adds compiler coupling and slows validation. |
| No raw escape hatch | Does not meet the extensibility requirement. |

## References

- `docs/specifications/assets.md`
- `docs/specifications/nodes.md`
- `docs/specifications/compiler.md`
- `ASSET-001` to `ASSET-020`
- `NODE-014` to `NODE-016`
