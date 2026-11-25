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
- The docs gate checks the internal links.
- A broken internal link is blocking. An unreachable external link is a
  warning in the full gate, because an external outage must not block an
  unrelated change.

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
| Markdown lint | Repository script. | Blocking. |
| Internal links | Repository script. | Blocking. |
| External links | Repository script with a timeout. | Warning. |
| Mermaid syntax | Repository script. | Blocking. |
| UTF-8 validity | Repository script. | Blocking. |
| BOM detection | Repository script. | Blocking. |
| LF line endings | Repository script. | Blocking. |
| Emoji and dingbats | Repository script. | Blocking. |
| Replacement characters | Repository script. | Blocking. |
| Mojibake patterns | Repository script. | Blocking. |
| Heading structure | Repository script. | Blocking. |
| Code fence language | Repository script. | Blocking. |

Tooling must not add runtime dependencies to the SDK. Documentation tools are
CI-only or development-only.

The repository script runs the blocking checks. The external link check needs
the network, so it runs in its own job of the continuous integration lanes and
reports warnings only.

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
| Markdown lint | The document starts with its title, the heading levels do not skip a level, the headings and the code fences have a blank line around them, one blank line separates the blocks, and the rows of a table have the same number of columns. |
| Diagrams | Every Mermaid block starts with a diagram type, the flowchart has a direction, the flowchart statements connect two nodes with a readable edge, the sequence diagram declares every participant, and every block is closed. |
| Requirements | Unique IDs, an allowed status, family ranges that match the traceability index, and evidence for every implemented requirement. |
| Decisions | An ADR index that lists every ADR, links that resolve, and supersede relations that point at a known ADR. |
| Schema references | Every published raw URL uses a repository path, and no current document keeps the retired publishing domain. |
| Schemas | Valid JSON, and every relative `$ref` resolves except the references that are tracked as open defects. |
| Workflows | Every action is pinned to a commit SHA, every workflow declares its permissions, no pull request workflow grants write access or reads a secret, and no workflow uses `pull_request_target`. |
| Governance | The CODEOWNERS file exists, every rule names an owner, and one rule covers every path. |

The rules of the script are covered by unit tests.

```shell
bazel test //scripts/tests:docs_tests
```

A new document must be added to the `docs_sources` group in the root
`BUILD.bazel`, so that it becomes part of the gate. The group holds the root
policy files `README.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`,
`CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `.gitattributes`, and
`.editorconfig`, the pull request template, the CODEOWNERS file, and every
document under `docs/`. A new workflow file is picked up by the
`workflow_sources` group.

## External link check

`scripts/check_links.py` checks the external links of the documents. It uses
the network, so it belongs to the continuous integration lane and not to the
repository gate.

```shell
bazel run //scripts:check_links
```

| Property | Rule |
|---|---|
| Method | A `HEAD` request, and a `GET` request when the server refuses the first one. |
| Timeout | Ten seconds per request. |
| Result | A warning for every unreachable link. |
| Exit code | Always zero. The check never blocks a merge. |
| Skipped URLs | The versioned raw URLs of the schemas. They resolve only after the first release tag exists, and the release lane verifies them against the tagged commit. |

The rules of the script are covered by unit tests.

```shell
bazel test //scripts/tests:link_tests
```

## Repository structure checks

`scripts/check_repository.py` reads the source tree of the repository and
checks the rules that the architecture and the build documents state: the
dependency direction between `specs/`, the two SDKs, and the repository
checks, the `__init__.py` of every Python package directory, the hermetic
Python toolchain, the committed lock file, the TypeScript compiler version of
the root manifest, the template of every architecture decision record, and the
rule that the generated published schemas are committed only in a release
commit.

The check reads the working tree, so it runs against the checkout and not
against the runfiles tree.

```shell
bazel run //scripts:repository_checks
```

The rules are covered by unit tests that build a synthetic repository for
every case.

```shell
bazel test //scripts/tests:repository_tests
```

The check runs in the pull request lane, in the main lane, and in the release
lane.

## Current state

| Item | Current |
|---|---|
| `docs/` content | This document set. |
| README code fences | Fixed; README uses standard fences and LF line endings. |
| `.gitattributes` | Present. It pins LF for text files and marks binary assets as binary. |
| `.editorconfig` | Present. It pins UTF-8, LF, final newline, and indentation rules. |
| Root policy files | `README.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `LICENSE` are present and covered by the gate. |
| Repository checks | Implemented in `//scripts:docs_checks`. |
| Markdown lint | Implemented in `//scripts:docs_checks`. The script checks the title, the heading levels, the blank lines around the blocks, and the shape of the tables. |
| Link checker | Internal links are checked by the repository script. External links are checked by `//scripts:check_links` in the continuous integration lanes. |
| Mermaid validation | Implemented in `//scripts:docs_checks`. The script parses the flowchart and the sequence diagram, the diagram types that the repository uses. |
| Encoding checks | Implemented in `//scripts:docs_checks`. |
| Workflow checks | Implemented in `//scripts:docs_checks`; three workflow files are checked. |
| Governance checks | Implemented in `//scripts:docs_checks`; the CODEOWNERS file is checked. |
| Repository structure checks | Implemented in `//scripts:repository_checks`; the rules are covered by `//scripts/tests:repository_tests`. |
| Docs CI | The `Documentation gate` job and the `Link check` job of the pull request lane and of the main lane. |
| Repository CI | The `Repository checks` job of the pull request lane and of the main lane, and the `verify` job of the release lane. |

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| DOC-001 | Documents MUST be UTF-8 without BOM. | IMPLEMENTED | `//scripts:docs_checks`; the encoding rule. |
| DOC-002 | Documents MUST use LF. | IMPLEMENTED | `//scripts:docs_checks`; the encoding rule. |
| DOC-003 | Documents MUST NOT contain emoji or dingbats. | IMPLEMENTED | `//scripts:docs_checks`; the text hygiene rule. |
| DOC-004 | Documents MUST NOT contain replacement characters. | IMPLEMENTED | `//scripts:docs_checks`; the text hygiene rule. |
| DOC-005 | Documents MUST NOT contain mojibake patterns. | IMPLEMENTED | `//scripts:docs_checks`; the text hygiene rule. |
| DOC-006 | Every code fence MUST declare a language. | IMPLEMENTED | `//scripts:docs_checks`; the code fence rule. |
| DOC-007 | Every document MUST have one level-1 heading. | IMPLEMENTED | `//scripts:docs_checks`; the heading rule. |
| DOC-008 | Internal links MUST resolve. | IMPLEMENTED | `//scripts:docs_checks`; the link rule. |
| DOC-009 | Mermaid diagrams MUST parse. | IMPLEMENTED | `//scripts:docs_checks`; the diagram rule parses the flowchart and the sequence diagram. |
| DOC-010 | External links MUST be checked with a timeout and MUST produce a warning, not a blocking failure, when unreachable. | IMPLEMENTED | `//scripts:check_links`; `//scripts/tests:link_tests`. |
| DOC-011 | Requirement IDs MUST be unique and stable. | CONFIRMED | Review and script. |
| DOC-012 | The docs gate MUST run on changed documents in PRs. | IMPLEMENTED | The `Documentation gate` job of the pull request lane. |
| DOC-013 | The docs gate MUST run on all documents on main. | IMPLEMENTED | The `Documentation gate` job of the main lane. |
| DOC-014 | Documentation tooling MUST NOT add SDK runtime dependencies. | IMPLEMENTED | `//scripts:repository_checks` rejects a module of `scripts/` that imports the SDK package. |
| DOC-015 | README code fences MUST be fixed before the gate is enabled. | IMPLEMENTED | Review; README uses standard fences and LF. |
| DOC-016 | `.gitattributes` and `.editorconfig` MUST enforce LF and UTF-8. | IMPLEMENTED | Repository review. |
| DOC-017 | ADRs MUST use the documented template. | IMPLEMENTED | `//scripts:repository_checks` checks the title, the fields, and the sections of every ADR against the template of `docs/decisions/README.md`. |
| DOC-018 | Accepted ADRs MUST NOT be edited to change decisions. | CONFIRMED | Review. |
| DOC-019 | Examples MUST be updated when the public API changes. | CONFIRMED | Review. |
| DOC-020 | The traceability index MUST be updated with requirement changes. | CONFIRMED | Review. |
| DOC-021 | A repository script MUST validate the documents, the requirement index, the ADR index, and the schema references without SDK installation or network access. | IMPLEMENTED | `//scripts:docs_checks`. |
| DOC-022 | The repository gate MUST validate the workflow files: pinned actions, declared permissions, no write access or secret in a pull request workflow, and no `pull_request_target`. | IMPLEMENTED | `//scripts:docs_checks`; three workflow files are checked. |
| DOC-023 | The repository gate MUST validate the CODEOWNERS file: it exists, every rule names an owner, and one rule covers every path. | IMPLEMENTED | `//scripts:docs_checks`; the CODEOWNERS file is checked. |
| DOC-024 | The external link check MUST run in the pull request lane and in the main lane, MUST use a timeout, and MUST NOT block the merge. | IMPLEMENTED | The `Link check` job of `pr.yml` and `main.yml`; `//scripts:check_links`. |
| DOC-025 | The rules of the repository gate and of the external link check MUST be covered by unit tests. | IMPLEMENTED | `//scripts/tests:docs_tests`; `//scripts/tests:link_tests`. The encoding rules are covered too. |
| DOC-026 | The rules of the repository structure checks MUST be covered by unit tests, and the checks MUST run in the pull request lane, in the main lane, and in the release lane. | IMPLEMENTED | `//scripts/tests:repository_tests`; the `Repository checks` job of `pr.yml` and `main.yml`; the `verify` job of `release.yml`. |

## Open questions

- Should the Mermaid parser cover the diagram types that the repository does
  not use yet?
- Should the line length be enforced later?
- Should the external link check also visit the anchors of the external
  documents?

## Related documents

- [Documentation index](../README.md)
- [Traceability](../requirements/traceability.md)
- [CI/CD](ci-cd.md)
- [Contributing](../governance/contributing.md)
- [ADR-0013](../decisions/ADR-0013-documentation-gate-and-traceability.md)
