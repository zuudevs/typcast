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
  version of every manifest and the changelog with the tag.
- Repository checks, `//scripts:docs_checks`, for the documents, the
  requirement index, the decision index, the schema references, and the
  workflow files.
- Three GitHub Actions workflows: pull request validation, main integration,
  and release verification. The pull request lane builds, tests, and checks
  the repository on Windows and Linux.
- A pull request template at `.github/PULL_REQUEST_TEMPLATE.md`, this
  changelog, a contributing guide, and a code of conduct.
- The security policy and the Apache-2.0 license.

### Changed

- Schema distribution uses versioned GitHub Raw URLs at the release tag
  instead of a planned dedicated schema domain.
- The schema validation runs against the built bundle, which is the
  authoritative artifact set.

### Known issues

- The schema prototype does not satisfy the contract yet. The open defects are
  listed in [the schema specification](docs/specifications/schema.md).
- The Typcast SDK core, the packaging targets, and the publishing jobs of the
  release workflow are not implemented.
