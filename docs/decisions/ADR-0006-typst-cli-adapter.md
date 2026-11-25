# ADR-0006: Typst CLI adapter and tested range

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The MVP promises PDF output. Typst is the chosen compiler candidate. The SDK
could bundle a compiler, require an explicit path, auto-detect a local compiler,
or define only a pluggable backend.

Bundling would add supply-chain, licensing, platform, and offline complexity.
Compiler-only validation would leave the document contract unenforced.

## Decision

Use an external Typst CLI through an adapter:

- Resolve an explicit path first, then `typst` on `PATH`.
- Check `typst --version` before compilation.
- Support one tested minor range: `>=0.15.0 <0.16.0`, initially tested with
  0.15.1.
- Reject unsupported versions unless an explicit override is set.
- Run without a shell, with an argument array.
- Set `--root` to an isolated temporary workspace.
- Use `--format pdf` and `--diagnostic-format short`.
- Apply a 60-second default timeout.
- Do not retry automatically.
- Do not fetch Typst packages.
- Map compiler output to structured diagnostics.

## Consequences

- Users must install Typst themselves.
- The SDK remains small and platform-independent.
- Compiler compatibility is explicit and testable.
- The adapter must handle missing, unsupported, and broken compilers.
- Raw Typst is trusted input and is not sandboxed by Typcast.
- Bundling and auto-install remain Post-MVP.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Bundled compiler | Supply-chain, license, platform, and size costs are too high for the MVP. |
| Explicit path only | Poor user experience and diagnostics. |
| No version check | Unpredictable output and hard-to-diagnose failures. |
| Pluggable backend only | PDF would not work out of the box. |

## References

- `docs/specifications/compiler.md`
- `docs/specifications/diagnostics.md`
- `docs/specifications/compatibility.md`
- `COMP-001` to `COMP-022`
- `COMPAT-008` to `COMPAT-010`
