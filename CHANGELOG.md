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
  with unit tests. The generator rejects a placeholder whose catalog is not
  declared as an input of the rule, so a missing declaration fails the build
  instead of leaving a stale output. The generator accepts only standard JSON,
  so the constants `NaN`, `Infinity`, and `-Infinity` are errors.
- The schema bundle and its validation target, `//specs/schemas:schema_tests`,
  which checks the built bundle against the contract, and
  `//specs/schemas:release_tag_tests`, which covers the release tag pattern of
  the contract.
- A schema publisher, `//tools/publish:publish_schemas`, which writes the
  published bundle with the identity of a release tag, verifies it against the
  build, and checks that every published schema resolves at its versioned raw
  URL.
- A release version check, `//scripts:check_version`, which compares the
  version of every manifest, the contract version of every schema source, and
  the changelog with the tag.
- A release preparation command, `//scripts:prepare_release`, which sets the
  release version in every manifest and in every schema source, publishes the
  built bundle under `specs/schemas/`, verifies the version consistency, the
  published bundle, and the archive, and removes the generated published files
  from the development branch again.
- A rehearsal of the release commit, `//scripts/tests:release_flow_tests`,
  which prepares the release in a temporary tree with the manifests, the schema
  sources, and the bundle of the build, so that the path of the release lane
  runs in every test lane.
- Repository checks, `//scripts:docs_checks`, for the documents, the
  requirement index, the decision index, the schema references, and the
  workflow files.
- Repository structure checks, `//scripts:repository_checks`, which read the
  source tree and enforce the dependency direction between `specs/`, the two
  SDKs, and the repository checks, the `__init__.py` of every Python package
  directory, the hermetic Python toolchain, the committed lock file, the
  TypeScript compiler version of the root manifest, the template of every
  architecture decision record, the rule that the generated published schemas
  are committed only in a release commit, the rule that every source file
  belongs to a Bazel package, the pinned Bazel version, the `.env` patterns of
  the ignore file, the private channel of the vulnerability policy, the
  dependency configuration of Dependabot, the npm package name, and the scope
  document. The rules are covered by unit tests, and the checks run in the
  pull request lane, in the main lane, and in the release lane.
- The npm manifest of the TypeScript SDK is named `typcast`, so the
  publication uses the reserved name.
- A Dependabot configuration, `.github/dependabot.yml`, that covers the
  module file of Bazel, the root npm manifest, the npm manifest of the
  TypeScript SDK, and the Python manifest of the Python SDK. The security
  updates of Dependabot are enabled in the settings of the repository.
- Three GitHub Actions workflows: pull request validation, main integration,
  and release verification. The pull request lane builds, tests, and checks
  the repository on Windows and Linux, reviews the dependencies of the pull
  request, and the eight checks are required before a merge into `main`.
- A pull request template at `.github/PULL_REQUEST_TEMPLATE.md`, this
  changelog, a contributing guide, and a code of conduct.
- The security policy and the Apache-2.0 license.
- The node schema, `specs/schemas/definitions/node.schema.json`, which defines
  the block and the inline span unions of the document IR.
- A schema archive target, `//specs/schemas:archive`, which packages the
  bundle as a deterministic gzip tarball. The member order, the member
  metadata, and the gzip header are fixed, so the bytes and the checksum of
  the release asset are the same on every platform.
- An archive comparison in the release lane: the archive of the published
  bundle must be the archive of the build, so that the release asset carries
  the files of the build and the identity of the release tag.
- A CODEOWNERS file at `.github/CODEOWNERS`, which routes every path to the
  maintainer and is checked by the repository gate.
- A Markdown lint in the repository gate: the document starts with its title,
  the heading levels do not skip a level, the headings and the code fences
  have a blank line around them, and the rows of a table have the same number
  of columns.
- A Mermaid parser in the repository gate. It reads the flowchart and the
  sequence diagram, the diagram types that the repository uses.
- Unit tests for the rules of the repository gate, including the encoding and
  the text hygiene rules: UTF-8 without a byte order mark, LF line endings, a
  final newline, no emoji, no replacement character, and no mojibake.
- An external link check, `//scripts:check_links`, that checks the external
  links with a timeout. It reports warnings only, because an outage of an
  external site must not block an unrelated change. It runs in its own job of
  the pull request lane and of the main lane.
- Unit tests for the rules of the repository gate and of the external link
  check.
- The immutable document model of the Python SDK and of the TypeScript SDK:
  `Document`, `Metadata`, `Page`, `Margin`, `Length`, `Module`, the seven block
  types, and the seven inline span types. The Python model uses frozen
  dataclasses and tuples, and the TypeScript model uses readonly properties,
  frozen arrays, and runtime checks, so a model instance cannot change after
  its construction.
- The JSON reader and the writer of the document IR in both SDKs. The canonical
  form follows the field order of the contract, uses two-space indentation and
  a trailing newline, preserves Unicode, and formats the numbers the same way
  in both languages. The reader rejects an unknown field, a missing required
  field, an unknown discriminator, and an unsupported schema version.
- The error hierarchy of the SDKs: `TypcastError` with a diagnostic collection,
  `ValidationError`, and `SerializationError`, with the diagnostic codes of
  `docs/specifications/diagnostics.md`.
- Shared document fixtures under `tests/fixtures/documents/`, with a manifest
  that names every valid fixture and every negative fixture with the
  diagnostic code that both SDKs must report.
- Cross-language contract runners, `//tests/contract:contract_py` and
  `//tests/contract:contract_ts_test`, which read the same fixtures, write
  every valid fixture back byte for byte, and compare the diagnostic code of
  every negative fixture.
- Unit tests for the document model, `//packages/python/tests:model_tests` and
  `//packages/typescript:model_test_run`, which cover the immutability, the
  constructor checks, the canonical JSON form, the reader, and the round trip.

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
- The requirements of the document IR, the SDK API, the node catalog, the
  diagnostics, the repository layout, and the testing layers that the new
  model, the new fixtures, and the new contract runners prove are marked
  `IMPLEMENTED`.

### Fixed

- The generator rejects the constants `NaN`, `Infinity`, and `-Infinity`, which
  Python accepts by default and which the JSON specification does not define.
  The generator reported success and wrote a file that every standard JSON
  parser rejects.
- The schema contract and the documentation gate check the whole release tag
  of an identity and of a raw URL reference, so a suffix such as
  `v1.0.0-invalid` is no longer accepted as a release tag. The patterns are
  identical to the pattern of the publisher.
- The repository structure checks walked into the Bazel output trees, so a
  build directory could own a Python module and the SDK isolation check could
  report a false error. The walk now skips the output trees, and a unit test
  covers the case.
- The TypeScript unit test project of the SDK did not carry the manifest of
  the package as an input. The sandbox of Linux therefore classified the test
  file as a CommonJS file, and the compilation failed with TS1295 while the
  build on Windows passed. The manifest is now an input of the project, as it
  already was for the project of the SDK.
- The test runners of Node did not carry the compiled SDK in their runfiles.
  The sandbox of Linux therefore could not resolve the import of the SDK and
  the run failed with ERR_MODULE_NOT_FOUND while the test on Windows passed.
  Both runners now declare the compiled SDK and the manifest of the package
  in their data.

### Known issues

- The project does not validate a document against the schema yet. That needs
  a JSON Schema implementation that the repository does not depend on.
- The builder, the validation engine, the Typst emitter, the Typst compiler
  adapter, the packaging targets for the wheel, the source distribution, and
  the npm tarball, and the publishing jobs of the release workflow are not
  implemented.
