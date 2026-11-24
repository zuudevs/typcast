# Changelog

All notable changes to Typcast are recorded in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
The package versions, the schema version, and the release tag are lockstep
(`REL-001`).

No release has been published yet. Every change so far is listed under
`Unreleased`.

## [Unreleased]

### Added

- The product, architecture, specification, engineering, and governance
  document set, with the requirement index and 23 architecture decision
  records.
- A JSON Schema generator that expands CSV catalog placeholders in templates,
  with unit tests.
- The schema bundle and its validation target, `//specs/schemas:schema_tests`,
  which checks the built bundle against the contract.
- A schema publisher, `//tools/publish:publish_schemas`, which writes the
  published bundle with the identity of a release tag, verifies it against the
  build, and checks that every published schema resolves at its versioned raw
  URL.
- A release version check, `//scripts:check_version`, which compares the
  version of every manifest, the contract version of every schema source, and
  the changelog with the tag.
- Repository checks, `//scripts:docs_checks`, for the documents, the
  requirement index, the decision index, the schema references, and the
  workflow files.
- Three GitHub Actions workflows: pull request validation, main integration,
  and release verification. The pull request lane builds, tests, and checks
  the repository on Windows and Linux, and the six checks are required before
  a merge into `main`.
- A pull request template at `.github/PULL_REQUEST_TEMPLATE.md`, this
  changelog, a contributing guide, and a code of conduct.
- The security policy and the Apache-2.0 license.
- The node schema, `specs/schemas/definitions/node.schema.json`, which defines
  the block and the inline span unions of the document IR.
- A schema archive target, `//specs/schemas:archive`, which packages the
  bundle as a deterministic gzip tarball. The member order, the member
  metadata, and the gzip header are fixed, so the bytes and the checksum of
  the release asset are the same on every platform.
- A CODEOWNERS file at `.github/CODEOWNERS`, which routes every path to the
  maintainer and is checked by the repository gate.
- A Markdown lint in the repository gate: the document starts with its title,
  the heading levels do not skip a level, the headings and the code fences
  have a blank line around them, and the rows of a table have the same number
  of columns.
- A Mermaid parser in the repository gate. It reads the flowchart and the
  sequence diagram, the diagram types that the repository uses.
- An external link check, `//scripts:check_links`, that checks the external
  links with a timeout. It reports warnings only, because an outage of an
  external site must not block an unrelated change. It runs in its own job of
  the pull request lane and of the main lane.
- Unit tests for the rules of the repository gate and of the external link
  check.

### Changed

- Schema distribution uses versioned GitHub Raw URLs at the release tag
  instead of a planned dedicated schema domain.
- The schema validation runs against the built bundle, which is the
  authoritative artifact set.
- The root schema implements the document IR: `schemaVersion`, `metadata`,
  `page`, `contents`, and `modules`. The `page.paper.paper` nesting of the
  prototype is gone.
- Every schema declares the draft 2020-12 dialect, an absolute identifier
  under the versioned raw base, a closed object shape, and an explicit list of
  required fields.
- The alignment catalog holds the three alignment values of the MVP. The
  remaining Typst alignment values are not part of the contract.

### Known issues

- The project does not validate a document against the schema yet. That needs
  a JSON Schema implementation that the repository does not depend on.
- The Typcast SDK core, the packaging targets for the wheel, the source
  distribution, and the npm tarball, and the publishing jobs of the release
  workflow are not implemented.
