# Documentation

Status: CONFIRMED / PROPOSED
Scope: Normative
Last updated: 2026-11-24

## Purpose

This document defines documentation standards, review rules, and the
documentation gate. The gate must catch encoding, formatting, link, and Mermaid
problems before they reach `main`.

## Standards

| Rule | Requirement |
|---|---|
| Encoding | UTF-8 without a byte order mark. |
| Line endings | LF. |
| Emoji | No emoji, emoticons, or decorative dingbats. |
| Replacement characters | No `U+FFFD`. |
| Mojibake | No text that was UTF-8 but decoded as Latin-1 or Windows-1252. The gate checks for the common byte sequences by code point. |
| Markdown | Valid CommonMark or GitHub-flavored Markdown. |
| Headings | One level-1 heading per document. |
| Code fences | Every fence declares a language. |
| Links | Internal links resolve; external links are reachable. |
| Mermaid | Diagrams parse as Mermaid. |
| Trailing whitespace | None. |
| Tabs | Not used for indentation. |
| Line length | Not enforced in the MVP; readability is reviewed. |
| Filenames | Lowercase ASCII, hyphen-separated, `.md`. |
| Requirement IDs | Stable and unique within the project. |

## Normative language

The key words `MUST`, `MUST NOT`, `SHOULD`, `SHOULD NOT`, and `MAY` are used as
described in RFC 2119 and RFC 8174.

A requirement is normative when it has:

- A requirement ID.
- A status of `CONFIRMED` or `IMPLEMENTED`.
- A verification method.

## Status vocabulary

| Status | Meaning |
|---|---|
| `CONFIRMED` | Approved as part of the MVP baseline. |
| `PROPOSED` | Recommended but not yet approved. |
| `OPEN` | Missing decision or evidence. |
| `DEFERRED` | Excluded from the MVP. |
| `IMPLEMENTED` | Present and verified. |

## Document structure

A specification document should contain:

1. Title.
2. Status and scope.
3. Purpose.
4. Normative content.
5. Requirements table.
6. Open questions.
7. Related documents.

Explanatory documents may omit the requirements table, but they must not contain
normative statements without an ID.

## Diagrams

- Use Mermaid for flows, components, and sequences.
- Keep labels short and ASCII where possible.
- Quote labels that contain punctuation.
- Do not use Mermaid for decorative images.
- Validate Mermaid syntax in the docs gate.
- A diagram must have a text explanation nearby.

## Links

- Internal links use relative paths.
- Links do not include absolute local paths.
- External links use HTTPS where available.
- Link text describes the target.
- A link to an external resource does not imply endorsement.
- The docs gate checks internal links and attempts external links with a timeout.
- A broken internal link is blocking. An unreachable external link is a
  warning, because an external outage must not block an unrelated change.

## Code examples

- Code fences declare a language.
- Python examples use the public `typcast` import.
- TypeScript examples use the public `typcast` package.
- Examples are illustrative unless marked normative.
- Examples must not contain secrets or real personal data.
- Examples must be updated when the public API changes.

## Requirement traceability

- Every requirement has an ID.
- The ID appears in the source document.
- The traceability index links the ID family to its source and verification.
- A requirement marked `IMPLEMENTED` links to a test or artifact.
- A removed requirement is marked as removed; its ID is not reused.

## ADR process

Architecture decisions are recorded in `docs/decisions/` using the template in
`decisions/README.md`.

An ADR:

- Has a unique number.
- States context, decision, consequences, and alternatives.
- Has a status: proposed, accepted, superseded, or rejected.
- Is linked from the affected documents.
- Is not edited to change a decision after acceptance; a new ADR supersedes it.

## Documentation gate

The gate runs on changed documents in pull requests and all documents on
`main`.

| Check | Tool class | Failure |
|---|---|---|
| Markdown lint | `markdownlint` or equivalent. | Blocking. |
| Internal links | Link checker. | Blocking. |
| External links | Link checker with timeout. | Warning. |
| Mermaid syntax | Mermaid CLI or parser. | Blocking. |
| UTF-8 validity | Repository script. | Blocking. |
| BOM detection | Repository script. | Blocking. |
| LF line endings | Repository script. | Blocking. |
| Emoji and dingbats | Repository script. | Blocking. |
| Replacement characters | Repository script. | Blocking. |
| Mojibake patterns | Repository script. | Blocking. |
| Heading structure | Markdown lint. | Blocking. |
| Code fence language | Markdown lint. | Blocking. |

Tooling must not add runtime dependencies to the SDK. Documentation tools are
CI-only or development-only.

## Repository checks

`scripts/validate_docs.py` runs the checks that the repository can perform
today. It uses the Python standard library only, so it needs no SDK
installation and no network access.

```shell
bazel test //scripts:docs_checks
```

| Area | Check |
|---|---|
| Encoding | UTF-8 without a byte order mark, LF endings, a final newline. |
| Text hygiene | No trailing whitespace, tabs, emoji, replacement characters, or mojibake. |
| Markdown | One level-1 heading, code fences with a language, balanced fences, internal links that resolve. |
| Diagrams | Every Mermaid block starts with a diagram type and has balanced brackets. |
| Requirements | Unique IDs, an allowed status, family ranges that match the traceability index, and evidence for every implemented requirement. |
| Decisions | An ADR index that lists every ADR, links that resolve, and supersede relations that point at a known ADR. |
| Schema references | Every published raw URL uses a repository path, and no current document keeps the retired publishing domain. |
| Schemas | Valid JSON, and every relative `$ref` resolves except the references that are tracked as open defects. |

A new document must be added to the `docs_sources` group in the root
`BUILD.bazel`, so that it becomes part of the gate.

The script does not replace the full gate. Markdown lint, external link
checks, and a Mermaid parser are still not configured, and the checks do not
run in CI yet.

## Current state

| Item | Current |
|---|---|
| `docs/` content | This document set. |
| README code fences | Fixed; README uses standard fences and LF line endings. |
| `.gitattributes` | Present. It pins LF for text files and marks binary assets as binary. |
| `.editorconfig` | Present. It pins UTF-8, LF, final newline, and indentation rules. |
| Repository checks | Implemented in `//scripts:docs_checks`. |
| Markdown lint | Not configured. The repository script checks the structure. |
| Link checker | Internal links are checked by the repository script. External links are not checked. |
| Mermaid validation | Structural check only. A Mermaid parser is not configured. |
| Encoding checks | Implemented in `//scripts:docs_checks`. |
| Docs CI | None. |

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| DOC-001 | Documents MUST be UTF-8 without BOM. | CONFIRMED | Encoding script. |
| DOC-002 | Documents MUST use LF. | CONFIRMED | Line-ending script. |
| DOC-003 | Documents MUST NOT contain emoji or dingbats. | CONFIRMED | Script. |
| DOC-004 | Documents MUST NOT contain replacement characters. | CONFIRMED | Script. |
| DOC-005 | Documents MUST NOT contain mojibake patterns. | CONFIRMED | Script. |
| DOC-006 | Every code fence MUST declare a language. | CONFIRMED | Markdown lint. |
| DOC-007 | Every document MUST have one level-1 heading. | CONFIRMED | Markdown lint. |
| DOC-008 | Internal links MUST resolve. | CONFIRMED | Link checker. |
| DOC-009 | Mermaid diagrams MUST parse. | CONFIRMED | Mermaid validation. |
| DOC-010 | External links MUST be checked with a timeout and MUST produce a warning, not a blocking failure, when unreachable. | CONFIRMED | Link checker. |
| DOC-011 | Requirement IDs MUST be unique and stable. | CONFIRMED | Review and script. |
| DOC-012 | The docs gate MUST run on changed documents in PRs. | CONFIRMED | CI review. |
| DOC-013 | The docs gate MUST run on all documents on main. | CONFIRMED | CI review. |
| DOC-014 | Documentation tooling MUST NOT add SDK runtime dependencies. | CONFIRMED | Dependency review. |
| DOC-015 | README code fences MUST be fixed before the gate is enabled. | IMPLEMENTED | Review; README uses standard fences and LF. |
| DOC-016 | `.gitattributes` and `.editorconfig` MUST enforce LF and UTF-8. | IMPLEMENTED | Repository review. |
| DOC-017 | ADRs MUST use the documented template. | CONFIRMED | Review. |
| DOC-018 | Accepted ADRs MUST NOT be edited to change decisions. | CONFIRMED | Review. |
| DOC-019 | Examples MUST be updated when the public API changes. | CONFIRMED | Review. |
| DOC-020 | The traceability index MUST be updated with requirement changes. | CONFIRMED | Review. |
| DOC-021 | A repository script MUST validate the documents, the requirement index, the ADR index, and the schema references without SDK installation or network access. | IMPLEMENTED | `//scripts:docs_checks`. |

## Open questions

- Which Markdown linter and link checker are used?
- Is a custom Python script preferred for encoding checks?
- Should Mermaid validation run on every PR or only changed files?
- Should line length be enforced later?

## Related documents

- [Documentation index](../README.md)
- [Traceability](../requirements/traceability.md)
- [CI/CD](ci-cd.md)
- [Contributing](../governance/contributing.md)
- [ADR-0013](../decisions/ADR-0013-documentation-gate-and-traceability.md)
