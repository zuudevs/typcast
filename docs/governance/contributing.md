# Contributing and governance

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-24

## Purpose

This document defines the lightweight governance model for the MVP. It covers
branching, review, commits, issues, changelog, release approval, and architecture
decisions. It is intentionally small enough for a maintainer-led project.

## Principles

1. `main` is always releasable.
2. Changes enter through pull requests.
3. Required checks are not bypassed.
4. Decisions are recorded in ADRs.
5. Security reports are handled privately.
6. Release publishing requires human approval.
7. Documentation is part of the change, not an afterthought.

## Roles

| Role | Responsibility |
|---|---|
| Contributor | Opens issues and pull requests, responds to review. |
| Maintainer | Reviews, merges, triages, and approves releases. |
| Release approver | Approves the protected release environment. |
| Security responder | Handles private vulnerability reports. |

A small project may combine maintainer and release approver roles. Separation of
duties is recommended as the maintainer count grows.

## Branching

- Trunk-based development.
- Short-lived branches.
- Pull requests target `main`.
- Branch names use a short prefix such as `feat/`, `fix/`, `docs/`, or `chore/`.
- Long-running feature branches are avoided.
- Force-pushing a shared branch is discouraged.
- A maintainer may squash merge.

## Pull requests

Every pull request must:

- Describe the problem and the change.
- Link the relevant issue or ADR.
- Include tests for behavior changes.
- Update documentation for public behavior.
- Update the changelog for user-visible changes.
- State the version impact: none, patch, minor, or major.
- Confirm that no secrets or generated artifacts are included.

The PR template must include a checklist for tests, documentation, changelog, and
version impact.

### Pull request template

The repository has exactly one pull request template at
`.github/PULL_REQUEST_TEMPLATE.md`. It has these sections:

| Section | Content |
|---|---|
| Summary | What changed and why. |
| Classification | Change-type checkboxes, scope, version impact, requirement impact. |
| Scope | The areas that changed and the areas deliberately left out. |
| Requirement traceability | Requirement IDs that are added, changed, or retired. |
| Architecture and API impact | Effect on the public API, the data contract, and the decisions. |
| Testing and verification | The commands that were run and their real results. |
| Documentation | The documentation that changed and the documentation that was checked. |
| Compatibility and release impact | Effect on versions, platforms, and release artifacts. |
| Security | Effect on trust boundaries, dependencies, and secrets. |
| Final checklist | The merge-readiness checks. |
| Reviewer notes | Where the reviewer should look and what is still open. |

- A section that does not apply is marked "Not applicable" with a reason, or is
  removed and the reason is recorded in the reviewer notes.
- Not every checkbox applies to every pull request. A box that does not apply
  is removed and the removal is explained.
- A checkbox is ticked only when it was verified.
- The testing section records commands and results, not intentions. "Tested
  locally" is not a result.

The template is the only pull request template. The repository does not use
multiple templates, and it does not use an issue template.

## Review

- At least one maintainer approval is required.
- Required CI checks must pass.
- A reviewer checks behavior, tests, documentation, and security impact.
- A reviewer may request an ADR for a significant decision.
- A maintainer does not approve their own change without a second reviewer when
  another maintainer is available.
- Review comments are resolved before merge.
- A pull request that changes a confirmed requirement links the approving ADR or
  scope change.

## Commits

Conventional Commits are required:

```text
<type>(<scope>): <summary>
```

Allowed types include:

- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `build`
- `ci`
- `chore`
- `perf`

Examples:

```text
feat(python): add document builder
fix(schema): remove page double nesting
docs(specs): define document IR
ci: add pull request validation
```

The summary is imperative and lowercase. The body explains why, not only what.
Breaking changes use `!` and a `BREAKING CHANGE:` footer.

## Issues

Issue templates are `DEFERRED` for the MVP. The repository has one pull request
template and no issue template, so an issue is a free-form report.

- Security report is not a public issue; it uses the private channel in
  `SECURITY.md`.

A bug report includes:

- Version.
- Platform.
- Minimal reproduction.
- Expected and actual behavior.
- Diagnostics or logs with secrets removed.

## Changelog

- `CHANGELOG.md` follows a Keep a Changelog style.
- Entries are grouped by Added, Changed, Deprecated, Removed, Fixed, and Security.
- Unreleased changes are collected under `Unreleased`.
- A release moves the relevant entries under the version and date.
- The changelog is reviewed with the release.
- The changelog is not generated blindly from commit messages.

## Release approval

- The release environment is protected.
- A maintainer approves the release after all gates pass.
- The approval is recorded in the release workflow.
- A release is not published from a pull request.
- A release is not published from a dirty tree.
- A failed gate blocks publication.

## Architecture decisions

- Significant decisions use an ADR in `docs/decisions/`.
- An ADR is proposed before implementation when practical.
- An accepted ADR is not edited to change its decision; a new ADR supersedes it.
- The ADR index is updated with each new decision.
- Requirements and documents link to the relevant ADR.

## Security

- Do not open a public issue for a vulnerability.
- Follow `SECURITY.md` for private disclosure.
- Do not include secrets in issues, pull requests, logs, or test fixtures.
- A security fix is released as a patch unless the impact requires otherwise.
- A security advisory is published when appropriate.

## CODEOWNERS

The repository has a CODEOWNERS file at `.github/CODEOWNERS`. It routes every
path to the maintainer, so a pull request always has a reviewer. The repository
check verifies that the file exists, that every rule names an owner, and that
one rule covers every path.

Area-specific ownership is added when:

- More than one maintainer owns distinct areas.
- Review routing becomes ambiguous.
- A release requires area-specific approval.

Until then, the file stays a single rule for the whole repository.

## Code of conduct

The project adopts the Contributor Covenant 2.1. `CODE_OF_CONDUCT.md` is
present at the repository root. The file is copied verbatim from the
Contributor Covenant 2.1 text and names the maintainer contact for reports.

## Contributing guide

`CONTRIBUTING.md` is present at the repository root. It is the entry point for
a new contributor: it links to this document, lists the checks to run, and
explains how a requirement, a decision, and the changelog are updated.

## Current gaps

| Gap | Status |
|---|---|
| `CONTRIBUTING.md` at repository root | CLOSED. Present at the repository root. |
| `CODEOWNERS` | CLOSED. Present at `.github/CODEOWNERS`. It routes every path to the maintainer until a second maintainer joins. |
| PR template | CLOSED. Present at `.github/PULL_REQUEST_TEMPLATE.md`. |
| Issue templates | DEFERRED |
| `CHANGELOG.md` | CLOSED. Present at the repository root. |
| `SECURITY.md` | CLOSED. Present at the repository root. |
| `LICENSE` | CLOSED. Present at the repository root. |
| Branch protection | CLOSED. `main` is protected: the required checks must pass, one approval is required, force pushes and deletions are disabled, and a conversation must be resolved. |
| Required checks | CLOSED. The eight checks of the pull request lane are required: `Build`, `Test`, and `Clean build` on Windows and Linux, the `Documentation gate`, the `Repository checks`, and the `Dependency review`. The `Link check` runs as well, but it reports warnings only and is not required. |
| `CODE_OF_CONDUCT.md` | CLOSED. Present at the repository root. |

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| GOV-001 | Development MUST be trunk-based with short-lived branches. | CONFIRMED | Process review. |
| GOV-002 | Pull requests MUST target `main`. | CONFIRMED | Repository settings. |
| GOV-003 | At least one maintainer approval MUST be required. | IMPLEMENTED | Branch protection of `main` requires one approving review. |
| GOV-004 | Required CI checks MUST pass before merge. | IMPLEMENTED | Branch protection of `main` requires the eight checks of the pull request lane. |
| GOV-005 | Commits MUST follow Conventional Commits. | CONFIRMED | Review. |
| GOV-006 | The repository MUST have exactly one pull request template at `.github/PULL_REQUEST_TEMPLATE.md`, and it MUST cover tests, documentation, changelog, and version impact. | IMPLEMENTED | `.github/PULL_REQUEST_TEMPLATE.md`. |
| GOV-007 | Issue templates are DEFERRED for the MVP; an issue is a free-form report. | DEFERRED | Scope review. |
| GOV-008 | A changelog MUST be maintained and reviewed at release. | CONFIRMED | `CHANGELOG.md` present; the release review is pending. |
| GOV-009 | Release MUST require manual environment approval. | CONFIRMED | Environment settings. |
| GOV-010 | Area-specific CODEOWNERS MUST be added when the maintainer count requires it. | DEFERRED | Future review. The file is present and routes every path to the maintainer. |
| GOV-011 | Significant decisions MUST use an ADR. | CONFIRMED | ADR review. |
| GOV-012 | Security reports MUST use a private channel. | CONFIRMED | `SECURITY.md`. |
| GOV-013 | Direct pushes to `main` MUST be disabled. | IMPLEMENTED | Branch protection of `main`; an administrator may merge a pull request without a second reviewer while the project has one maintainer. |
| GOV-014 | Breaking changes MUST be marked in the commit and changelog. | CONFIRMED | Review. |
| GOV-015 | A change to a confirmed requirement MUST link an approving ADR or scope change. | CONFIRMED | Review. |
| GOV-016 | A maintainer MUST NOT approve their own change without a second reviewer when available. | CONFIRMED | Review. |
| GOV-017 | The repository MUST publish a roadmap or scope document. | CONFIRMED | Documentation review. |
| GOV-018 | The project MUST adopt the Contributor Covenant 2.1 and MUST add `CODE_OF_CONDUCT.md` before accepting public contributions. | IMPLEMENTED | `CODE_OF_CONDUCT.md` at the repository root. |
| GOV-019 | Contributions MUST be accepted under Apache-2.0. | IMPLEMENTED | `LICENSE` present at the repository root. |
| GOV-020 | Release notes MUST describe user-visible changes and known issues. | CONFIRMED | Release review. |
| GOV-021 | The pull request template MUST record the commands that were run and their results, and MUST allow a section or a checkbox that does not apply to be removed or marked "Not applicable". | IMPLEMENTED | `.github/PULL_REQUEST_TEMPLATE.md`. |

## Open questions

- When should the CODEOWNERS rules become area specific?
- Is a maintainer-only release approval sufficient for `1.0.0`?
- Should the project use a contributor license agreement?
- What is the issue triage cadence?

## Related documents

- [Documentation](../development/documentation.md)
- [Release](../development/release.md)
- [Security](../development/security.md)
- [ADR index](../decisions/README.md)
