# ADR-0013: Documentation gate and traceability

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The repository has no documentation content, no Markdown lint, no link checker,
and no encoding checks. The README contained escaped backticks that broke code
fences; the documentation set fixes them. The working tree used CRLF in places
while documentation requires LF. The MVP also needs requirement traceability
across product, architecture, contract, and release documents.

## Decision

Use a full documentation gate and a requirement traceability index:

- UTF-8 without BOM.
- LF line endings.
- No emoji, dingbats, replacement characters, or mojibake.
- Markdown lint.
- Internal link checking.
- Mermaid syntax validation.
- External link checking with a timeout.
- Requirement IDs and a traceability index.
- ADRs for significant decisions.
- Docs gate on changed documents in PRs and all documents on main.

## Consequences

- Documentation defects are caught before merge.
- `.gitattributes` and `.editorconfig` are required.
- The README code fences are fixed; the gate itself remains to be implemented.
- Tooling is CI-only and does not add SDK runtime dependencies.
- Semantic consistency and automated API reference generation remain Post-MVP.
- Every requirement change must update the traceability index.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Core encoding and link gate only | Mermaid and emoji/mojibake issues would slip through. |
| Manual review only | Not reliable and does not scale. |
| Full gate plus semantic checks | Too complex for the MVP. |
| No traceability | Requirements and tests would drift. |

## References

- `docs/development/documentation.md`
- `docs/requirements/traceability.md`
- `DOC-001` to `DOC-020`
- `TRACE-001` to `TRACE-005`
