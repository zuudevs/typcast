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
  document set, with the requirement index and 27 architecture decision
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
- The semantic validation engine of both SDKs. `Document.validate()` returns
  the diagnostics of the rules that span more than one node and raises no error
  for a semantic problem, so that a caller can show all of the problems at
  once. The engine checks the shape of a table with `TYPCAST-VAL-0007`, the
  uniqueness of a module alias with `TYPCAST-VAL-0008`, and the size of a raw
  node with `TYPCAST-VAL-0010`. The diagnostics come in the order of the
  document.
- The configuration of the validation engine: `TypcastConfig` in Python and
  `TypcastOptions` in TypeScript hold the raw size limit, which is passed per
  call and is never stored in the document. A limit that is not an integer that
  is finite and not negative raises `ConfigError` with `TYPCAST-CONFIG-0004`,
  the phase `config`, and the path `/max_raw_bytes`.
- The measurement of the size of a raw value in the bytes of the UTF-8
  encoding of the value, implemented the same way in both SDKs, so that the
  two SDKs count the same number of bytes for the same text.
- Shared validation fixtures under `tests/fixtures/validation/`, with a
  manifest that names the diagnostics of every negative fixture in the order
  the engine reports them, and that may name the raw size limit of a fixture.
- Cross-language validation contract runners,
  `//tests/contract:validation_py` and `//tests/contract:validation_ts_test`,
  which read the same validation fixtures and the same manifest, so a drift in
  the diagnostics of either SDK fails one of the two targets.
- Unit tests for the validation engine,
  `//packages/python/tests:validation_tests` and
  `//packages/typescript:validation_test_run`, which cover the semantic rules,
  the configuration, the order of the diagnostics, and the measurement of the
  size of a text.
- The fluent builder of the Python SDK and of the TypeScript SDK:
  `DocumentBuilder` with `title()`, `author()`, `date()`, `page()`, `heading()`,
  `paragraph()`, `bullet_list()`, `numbered_list()`, `table()`, `image()`,
  `page_break()`, `raw()`, `module()`, and `build()`, with the span helpers
  `text()`, `bold()`, `italic()`, `monospace()`, `link()`, `line_break()`, and
  `raw_inline()`, and with the table helpers `column()` and `cell()`. The
  builder is mutable and is not thread-safe, and `build()` returns an
  immutable snapshot that a later call of the builder does not change.
- The normalization of the content of the builder. A string that is passed as
  content becomes a `Text` span, a span is kept as it is, and two strings are
  never merged, because a merge would change the structure of the content.
- The defaults of the builder, which the node catalog names: the paper `a4`,
  the orientation `portrait`, a margin of 2.5 cm on every side, an unordered
  bullet list, no module, and no caption and no width for an image.
- `Length.cm(value)` in both SDKs, which returns a length in centimeters, as
  the examples of the SDK API use it.
- `ApiUsageError` with the codes `TYPCAST-API-0001` and `TYPCAST-API-0002` in
  both SDKs. The builder raises `ApiUsageError` when an argument has a type
  that the method cannot use, and the rules of a node stay with the
  constructors of the model.
- Unit tests for the builder, `//packages/python/tests:builder_tests` and
  `//packages/typescript:builder_test_run`, which cover the surface of the
  builder, the chaining of its methods, the normalization of the content, the
  defaults, the errors of the diagnostic taxonomy, and the immutability of the
  snapshot that `build()` returns.
- Shared builder fixtures under `tests/fixtures/builder/`, with a manifest that
  names the scenarios of the builder and the operations of every scenario, and
  with the canonical JSON that every scenario must produce.
- Cross-language builder contract runners, `//tests/contract:builder_py` and
  `//tests/contract:builder_ts_test`, which read the same builder fixtures and
  the same manifest, so a drift in the builder of either SDK fails one of the
  two targets.
- The configuration of the validation run of a build. `build()` takes the
  configuration of the validation engine in both SDKs, so the raw size limit of
  a build is the limit of the call and a call that names no configuration uses
  the default limit of one MiB. The configuration is passed per call and is
  never stored in the document.
- The shared builder fixtures cover the limit of a build: a scenario may name a
  raw size limit, and a scenario that expects a diagnostic names the code, the
  path, the message, and the details that both SDKs must report.
- ADR-0026, which supersedes ADR-0024 and restates the rules of the engine
  unchanged, and adds the configuration of the validation run of a build.
- The validation of an instance against the JSON Schema contract in both SDKs.
  `validate_schema(value)` in Python and `validateSchema(value)` in TypeScript,
  and the method `Document.validate_schema()` and `Document.validateSchema()`,
  report every rule that the value breaks and raise no error. The check is
  opt-in and stays separate from the reader of the document IR and from the
  semantic validation engine.
- The diagnostics of the schema validation use the new family `TYPCAST-SCH-*`
  with the phase `validation`. `TYPCAST-SCH-0001` names an instance that
  breaks a rule of the schema, and the details name the keyword of the broken
  rule. `TYPCAST-SCH-0002` names a keyword of the schema that the validator
  does not implement, so a contract that gains a keyword fails the check
  instead of passing every instance.
- A schema embedding generator, `//tools/schemagen`, and the rule
  `typcast_schema_source` of `bazel/schemagen.bzl`, which embed the built
  bundle into a source file of an SDK. The contract travels with the package,
  the SDK reads no file and parses no JSON at run time, and the SDKs depend on
  no third-party JSON Schema library.
- Shared schema fixtures under `tests/fixtures/schema/`, with a manifest that
  names the diagnostics of every negative fixture in the order the validator
  reports them, and cross-language schema contract runners,
  `//tests/contract:schema_py` and `//tests/contract:schema_ts_test`, which
  read the same fixtures and the same manifest, so a drift in the diagnostics
  of either validator fails one of the two targets.
- The stage `//tests/schema:schema_py`, which walks the whole embedded
  contract and reports a keyword that the validator does not implement, and
  which checks every valid document fixture and every canonical document of
  the builder against the contract.
- ADR-0027, which records the validation of an instance against the JSON
  Schema contract and the decision to keep the SDKs free of a third-party
  JSON Schema dependency.
- A Typst emitter in both SDKs, with the public API `Document.to_typst(config=None)`
  and `Document.toTypst(options?)`. The method returns the Typst source of a
  document as a string, validates the document again before the emission, and
  reads no asset and invokes no compiler.
- The output contract of the emitter: the fixed header, the module imports, the
  page setup, the document metadata, and the blocks in the order of the
  document, with one blank line between the sections, UTF-8 without a byte
  order mark, LF line endings, and exactly one trailing newline.
- The escaping rules of the emitter, which follow the table of the node
  catalog and escape a list marker at the start of a line when the marker could
  open a list. A monospace span is emitted as the raw text of Typst, and a value
  that the raw text cannot hold is rejected with `TYPCAST-EMIT-0003`.
- The diagnostics of the emitter, which use the family `TYPCAST-EMIT-*` with the
  phase `emit`. `TYPCAST-EMIT-0001` names an invariant of the model that does
  not hold, `TYPCAST-EMIT-0002` names a node of an unknown type, and
  `TYPCAST-EMIT-0003` names a value that cannot be escaped safely.
- Golden Typst files under `tests/fixtures/expected/`, one for every valid
  document fixture, and cross-language emitter contract runners,
  `//tests/contract:typst_py` and `//tests/contract:typst_ts_test`, which
  compare the output of both SDKs with the same golden file, so a drift in the
  output of either SDK fails one of the two targets.
- ADR-0028, which records the Typst emitter, the context-sensitive escaping of
  the list markers, and the raw text of a monospace span.

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
- The requirements `IR-006`, `IR-010`, `IR-019`, `API-007`, `API-027`,
  `DIAG-018`, `NODE-008`, and `TEST-033` that the semantic validation engine
  proves are marked `IMPLEMENTED`.
- The requirements `API-001`, `API-002`, `API-003`, `API-005`, `API-006`,
  `API-024`, and `NODE-023` that the fluent builder proves are marked
  `IMPLEMENTED`.
- The requirements `SCH-024`, `API-029`, `DIAG-019`, and `TEST-034` that the
  validation against the schema contract proves are marked `IMPLEMENTED`.
- The requirements `EMIT-001` to `EMIT-024`, `API-017`, `API-030`, `DIAG-020`,
  `NODE-005`, `NODE-007`, `NODE-013` to `NODE-023`, and `TEST-035` that the
  Typst emitter proves are marked `IMPLEMENTED`.
- The emitter document states that the emitter is implemented in both SDKs, and
  it names the rules of the monospace span and of the list markers.
- The node catalog states that a plus at the start of a line is escaped like a
  hyphen, and that the content of a monospace span is not escaped.
- The SDK API document names the behavior of `to_typst()` and `toTypst()`.
- The diagnostics document names the details of the codes of the emitter.
- The schema document states that the instance validation against the contract
  is implemented in the two SDKs. The validation of a schema document against
  the JSON Schema meta-schema is still missing.
- The SDK API document names the behavior of the builder: the chaining of its
  methods, the normalization of the content, the defaults of the node catalog,
  the split between the errors of the public API and the errors of the model,
  and the validation that `build()` runs. The builder is documented as
  mutable, single-document, and not thread-safe.
- The diagnostics document names the code `TYPCAST-API-0002` and states that
  no path of the builder raises it.
- The SDK API document names the behavior of `validate()`, the configuration of
  the validation engine, and the details of the diagnostics of the engine. The
  configuration holds the raw size limit only, because the asset root, the
  compiler path, and the timeout belong to the asset layer and the compiler
  adapter, which arrive later.
- The diagnostics document names the details of the codes of the semantic
  engine and the order in which the engine reports its diagnostics.

### Fixed

- The validator of the JSON Schema contract of the Python SDK converted a
  number to the binary64 domain of ECMAScript when it checked the type of an
  integer. A Python integer that is larger than that domain, such as the
  heading level `10**400` of a JSON document, raised an `OverflowError`
  instead of reporting the diagnostics of the document. The validator now
  checks the type of an integer without a conversion, and the comparison of
  two numbers of the contract handles the same case.
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
- The TypeScript SDK read a date with the `Date.UTC` function, which maps a
  year below 100 to the year 1900 and above. The SDK therefore rejected a
  date such as `0001-01-01` that the Python SDK accepts. Both SDKs now check
  the calendar with the same arithmetic.
- The TypeScript SDK looked a discriminator up with the `in` operator, which
  accepts an inherited key such as `constructor` or `toString`. Such a value
  raised a raw `TypeError` instead of the documented diagnostic. The lookup
  now checks the own keys of the table.
- The Python SDK wrote a lone surrogate into the canonical JSON text, because
  Python holds such a character in a string. The result was a text that no
  UTF-8 encoder can encode. The Python SDK now rejects the value with the
  same diagnostic as the TypeScript SDK.
- The Python SDK read a date with a pattern that matches every Unicode
  decimal digit and that accepts a final newline. A date such as
  `2026-01-01\n` was therefore accepted by the Python SDK and rejected by the
  TypeScript SDK. Both SDKs now read the same dates.
- Both SDKs accepted a title or an author of more than 512 Unicode code
  points, which the schema of the contract rejects. Both SDKs now check the
  limit and report it with the new code `TYPCAST-VAL-0013`. The catalog of
  the diagnostics allows a new code in a minor release.
- The Python SDK read the schema version with a pattern that matches every
  Unicode decimal digit and that accepts a final newline. A version such as
  `١.0.0` or `1.0.0\n` was therefore accepted by the Python SDK and rejected
  by the TypeScript SDK. Both SDKs now read the same versions.
- The Python SDK checked a module alias and a module item with a pattern that
  accepts a final newline. An identifier that ends with a newline was
  therefore accepted by the Python SDK and rejected by the TypeScript SDK.
  Both SDKs now accept the same identifiers.
- The Python SDK held a length value as an arbitrary precision integer, so a
  value that the binary64 number domain cannot hold exactly was rounded when
  the canonical text was written. The document in the model and the document
  in the text were therefore different, and the round trip did not preserve
  the document. Both SDKs now hold the numbers of a document in the binary64
  domain of ECMAScript, so a value that the domain cannot hold is narrowed
  the same way in both SDKs, and a value that overflows the domain is
  rejected in both SDKs.
- The Python SDK rejected a JSON number with a zero fractional part, such as
  the level `1.0` of a heading, while the TypeScript SDK accepted it. A JSON
  integer is a number without a fractional part, so both SDKs now accept the
  same values.
- The TypeScript SDK parsed the lengths of a margin and the optional fields of
  an image inside the factory of the construction helper, so the path of a
  failing child was prefixed a second time. An error of the length of the top
  margin was reported at `/page/margin/page/margin/top/value` instead of
  `/page/margin/top/value`, and the path differed from the path of the Python
  SDK. Both SDKs now report the path of the failing field.
- Both SDKs formed the path of an unknown field without escaping the name, so
  a property named `bad/name` produced the pointer `/bad/name` instead of
  `/bad~1name`. Both SDKs now escape the name as RFC 6901 defines it.
- The Python SDK stored a runtime value of an unknown type in the details of a
  diagnostic, so the details of that diagnostic could not be serialized to
  JSON. Both SDKs now keep only a JSON-serializable representation of such a
  value, and the representation of the two SDKs agrees.
- The Python SDK built the path of an unknown field without checking the type
  of the key, so a mapping with a key that is not a string raised a raw
  `AttributeError` instead of a diagnostic. The reader now rejects such a
  mapping with the documented diagnostic.
- The Python SDK kept a number that is not finite in the details of a
  diagnostic, and such a number has no token in JSON. Both SDKs now spell a
  number that is not finite in the form of ECMAScript, so the details of both
  SDKs stay JSON-serializable.
- The Python SDK read a JSON integer token of more than 4300 digits with the
  integer parser of the interpreter, which reports such a token as malformed
  JSON. The token is valid JSON, and the TypeScript reader reads it as an
  infinity. The Python SDK now reads every integer token in the number domain
  of the IR, so both SDKs report the same overflow.
- The Python SDK checked the type of an item of a module before it checked the
  item itself, so an item of another type reported the diagnostic of a wrong
  element type, while the TypeScript SDK reports the diagnostic of the module
  item. Both SDKs now report the diagnostic of the module item.
- Both SDKs accepted an image whose width is zero, while the IR requires a
  positive width. Both SDKs now reject a width of zero with the documented
  diagnostic, and the requirement `IR-022` and the negative fixture
  `invalid-image-width.json` record the rule.
- The Python SDK converted a component of the schema version with the integer
  parser of the interpreter, which reports a component of more than 4300
  digits as a raw error. The component is a number of the IR, so it lives in
  the binary64 domain of ECMAScript, in which such a number is an infinity.
  Both SDKs now read the same components and accept and reject the same
  versions.
- The TypeScript SDK read the discriminator of a block or a span from the
  value itself, so a property that the prototype of the value supplies was
  accepted as a discriminator. The Python SDK reads only the own keys of a
  mapping, so both SDKs now require an own discriminator.
- Neither SDK exported the version of its package, although the API of
  `docs/specifications/sdk-api.md` names `typcast.__version__` and the
  TypeScript `VERSION` export. Both package roots now export the version of
  the package, the requirement `API-026` records the rule, and the repository
  gate compares every export with the manifest of its package.
- Both SDKs accepted a schema version whose component held a leading zero,
  such as `01.0.0`, while a semantic version holds none. Both SDKs now reject
  such a version, and the negative fixture `version-leading-zero.json` records
  the rule.
- The Python SDK rendered the rejected value of a module alias or of a length
  unit in the message of a diagnostic, so an integer of more than 4300 digits
  raised a raw error of the interpreter instead of a diagnostic. Both SDKs now
  render the value in a bounded form, so the message stays readable and the
  details of the diagnostic stay JSON-serializable.
- The two SDKs reported an invalid input in different words. The Python SDK
  named the rejected value of an invalid enum, while the TypeScript SDK named
  it in no message at all, and the Python SDK called a collection a sequence
  while the TypeScript SDK called it an array. Both SDKs now use the same
  wording, and the requirement `DIAG-015` records the rule. The manifest of
  the shared fixtures names the message of every negative fixture, so a drift
  in the wording fails the contract tests.
- The message of a malformed JSON text quoted the reason of the parser of the
  runtime, and the two parsers word their reason differently. Both SDKs now
  write the same message, and the reason belongs to the details of the
  diagnostic.
- The Python SDK added the text of the exception of the runtime to the details
  of the diagnostic of an impossible date, while the TypeScript SDK named the
  rejected value only. Both SDKs now write the same details, and the
  requirement `DIAG-016` records the rule. The manifest of the shared fixtures
  names the details of every negative fixture, so a drift in the details fails
  the contract tests.
- The two SDKs showed a rejected value in no canonical form, so a value that
  holds a quote, a backslash, or a control character broke the text of the
  message, and a value that holds a supplementary character was cut in the
  middle of the character. Both SDKs now show the value in the same escaped
  form, and the text holds at most 64 Unicode code points. The requirement
  `DIAG-017` records the rule.
- The pattern of `schemaVersion` in `validator.schema.json` accepted a version
  with a leading zero, a Unicode digit, and a trailing newline or carriage
  return, while the readers of the SDKs rejected them. The pattern now matches
  the whole text of a semantic version, and the requirement `SCH-022` records
  the rule.
- The Python SDK wrote a number in the canonical text with the format of the
  interpreter, so a number such as `1e-7` and a number such as `1e+21` were
  written in another form than the TypeScript SDK wrote them. The Python SDK
  now writes every number in the format of ECMAScript, so the canonical text
  of a document is the same in both SDKs.
- The Python SDK checked the encodability of a document only when it wrote the
  canonical text, so the JSON value of a document could hold a character that
  UTF-8 cannot encode. The check now runs on every public path of both SDKs.
- The details of the diagnostic of a mapping with a key that is not a string
  named the type of the key in the language of the SDK, and the TypeScript SDK
  accepted an object with a symbol key. Both SDKs now report the same
  details, `{"keyType": "non-string"}`, and the TypeScript SDK rejects such an
  object with the same diagnostic as the Python SDK.
- The schema accepted an image whose width is zero, because the width of an
  image referenced the shared length schema, whose lower bound of zero is the
  bound of a margin, while the readers of the SDKs and the IR require a
  positive width of an image. The width of an image now carries an exclusive
  lower bound of zero, the length of a margin stays non-negative, and the
  requirement `SCH-023` records the rule.
- The Python SDK lost the sign of an integer that overflows the binary64
  number domain of ECMAScript, because the conversion of such an integer to a
  float raises an error of the interpreter, and the fallback returned a
  positive infinity for every sign. A length whose value was a negative
  integer of more than 400 digits therefore reported `{"value": "Infinity"}`
  in its details, while the TypeScript SDK reported `{"value": "-Infinity"}`.
  The conversion now keeps the sign, exactly as the conversion of a number of
  ECMAScript does, and the canonical format of a number follows the same rule.
- The shared fixtures held no case for a quoted value, a control character, a
  supplementary character, a long value, a version that ends with a newline, a
  number at the boundary of the binary64 domain, a lone surrogate, a key that
  is not a string, and an integer token that the interpreter cannot convert.
  The fixtures and the manifest of their expectations now cover these cases,
  and both contract runners compare the code, the path, the message, and the
  details of every one of them.
- The SDK API document grouped `to_json()` with the operations that raise a
  typed error. ADR-0005 decided that the serialization of a built model does
  not validate again, so the prose is corrected, and the decision itself is
  unchanged.
- The builder of the TypeScript SDK read the fields of its options objects
  before it checked the objects themselves. A caller in JavaScript, or a
  caller in TypeScript with a cast, therefore got a native `TypeError` for an
  options object that was `null`, and the defaults of the node catalog for an
  options object that was a string or another primitive. The builder now
  checks the options of `page`, `table`, `image`, `raw`, and `module` before
  it reads a field of them, so a wrong options object raises the documented
  `ApiUsageError` with `TYPCAST-API-0001` and the phase `api`. A failed check
  changes no state of the builder, so the builder stays usable. The rules of a
  node stay with the model, so an invalid enum inside a well-typed options
  object still raises a `ValidationError` of the `TYPCAST-VAL-*` family.

### Known issues

- The project does not validate a schema document against the JSON Schema
  meta-schema yet. That needs a JSON Schema implementation that the repository
  does not depend on.
- The Typst compiler adapter, the packaging targets for the wheel, the source
  distribution, and the npm tarball, and the publishing jobs of the release
  workflow are not implemented.
