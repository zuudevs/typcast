# Pull request

<!--
This is the only pull request template in the repository.

Keep every section that applies. If a section does not apply, replace its
content with "Not applicable" and say why, or delete the section and record the
reason in "Reviewer notes".

Do not tick a box that was not verified. Do not claim a command was run when it
was not. The reviewer relies on the commands and results in this template.

See docs/governance/contributing.md for the contribution rules.
-->

## Summary

<!--
What changed, and why. One paragraph. Link the issue, the requirement, or the
ADR that authorizes the change. If the pull request fixes a defect, describe
the defect and its impact.
-->

## Classification

<!-- Tick every box that applies. -->

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation or specification change
- [ ] Refactor or maintenance
- [ ] Build, tooling, or CI change
- [ ] Security change
- [ ] Breaking change

| Field | Value |
|---|---|
| Scope | e.g. `specs`, `tools/codegen`, `docs`, `packages/python` |
| Version impact | none, patch, minor, or major |
| Requirement impact | none, new, changed, or retired |

## Scope

<!--
The areas that are changed, and the areas that are deliberately left out.
Name the files or packages that a reviewer should look at first.
-->

### Changed

-

### Not changed

-

## Requirement traceability

<!--
List every requirement ID that this pull request adds, changes, or retires.
A changed CONFIRMED requirement MUST link the approving ADR or the documented
scope change. Use "Not applicable" when no requirement is affected.
-->

| Requirement ID | Change | Evidence, ADR, or scope change |
|---|---|---|
|  |  |  |

## Architecture and API impact

<!--
Describe the effect on the public API, the data contract, the build graph, and
the architecture decisions. Link the ADR when a decision changes, and state
when the decision is unchanged. Use "Not applicable" with a reason when the
change has no architectural effect.
-->

## Testing and verification

<!--
Record the commands that were run in the workspace of this pull request and
their real results. "Tested locally" and "CI will check" are not results. Give
the command and the observed outcome. Use "Not applicable" only when the change
has no executable effect, and explain why.
-->

| Command | Result |
|---|---|
|  |  |

## Documentation

<!--
List the documentation that was updated for this change, and the documents
that were checked and needed no change. Use "Not applicable" with a reason
when the change is internal.
-->

## Compatibility and release impact

<!--
State the effect on the Python package, the npm package, the schema version,
the supported platforms, and the release artifact set. State explicitly when
there is none. A breaking schema change requires a major version.
-->

## Security

<!--
State the effect on trust boundaries, input handling, dependencies, secrets,
and the vulnerability policy. Confirm that the change contains no secret,
credential, private data, or unreviewed third-party content. Use "Not
applicable" with a reason when the change has no security effect.
-->

## Final checklist

<!--
Every box must be accurate. Delete a box that does not apply and explain the
deletion in "Reviewer notes". Do not tick a box that was not verified.
-->

- [ ] The change is described above and stays within the stated scope.
- [ ] Requirement IDs are updated in the source document and in `docs/requirements/traceability.md`.
- [ ] Tests cover the changed behavior, or the change has no executable effect.
- [ ] The commands and results above were run in the workspace of this pull request.
- [ ] Documentation is updated for user-visible behavior.
- [ ] `CHANGELOG.md` is updated for user-visible changes, or the change is not user-visible.
- [ ] The version impact is stated above and matches the change.
- [ ] No secret, credential, generated output, or local absolute path is included.
- [ ] A breaking change is marked in the commit and in the changelog.
- [ ] A new or changed architecture decision has an ADR and an updated ADR index.

## Reviewer notes

<!--
Point the reviewer at the parts that need attention, list the decisions that
are still open, and explain every section that was removed or marked not
applicable.
-->
