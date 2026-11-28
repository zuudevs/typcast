# ADR-0027: Instance validation against the JSON Schema contract

Status: Accepted
Date: 2026-11-28
Supersedes: none
Superseded by: none

## Context

The JSON Schema contract of the project is the normative data contract of the
document IR. The repository builds it, validates its shape, and publishes it at
a versioned raw URL, but no SDK could check a document against it. The reader
of both SDKs checks the rules that one node carries, and the semantic engine
checks three rules that span more than one node. A caller that wanted to know
whether a document satisfies the published contract had to run an external JSON
Schema implementation against the schema bundle and the document, which meant
installing a tool that the repository does not depend on and keeping it in step
with the contract version of the package.

The schema specification stated that the bundle test does not validate a schema
document against the JSON Schema meta-schema and does not validate an instance
against the contract, because both need a JSON Schema implementation that the
repository does not depend on yet. The instance validation is the part that a
caller needs, and the change closes it.

The two SDKs are dependency-free by contract. `REPO-003` requires that each SDK
depends on no code outside its own package, and the published packages are
self-contained. A third-party JSON Schema library would break both rules, and it
would bring a dependency tree into two packages that carry none today.

The contract also uses only a part of JSON Schema 2020-12. It uses `$ref`,
`additionalProperties`, `const`, `enum`, `exclusiveMinimum`, `items`,
`maxLength`, `maximum`, `minItems`, `minLength`, `minimum`, `not`, `oneOf`,
`pattern`, `properties`, `required`, `type`, and `unevaluatedProperties`, plus
the annotations `$comment`, `$defs`, `$id`, `$schema`, `default`, `deprecated`,
`description`, `examples`, `readOnly`, `title`, and `writeOnly`. A validator of
the whole specification would be a large dependency for a small contract, and a
validator of the part that the contract uses is small enough to write by hand.

ADR-0002 keeps the schema the data contract and the builders hand-written, and
ADR-0005 keeps the validation in two layers: the rules of the schema and the
rules of the semantics. The schema layer was missing.

## Decision

Give both SDKs a validator of the instance against the JSON Schema contract,
and keep the reader and the semantic engine unchanged.

- Each SDK carries the schema contract as a generated source file. The build
  embeds the bundle that `//specs/schemas:schema_bundle` produces into a source
  file of the SDK, so a published package holds the contract and needs no file
  of the repository at run time. The generated file is a literal, so the SDK
  reads no file and parses no JSON at run time.
- Each SDK holds a hand-written validator for the subset of JSON Schema
  2020-12 that the contract uses. The validator implements the keywords listed
  above and ignores the annotations.
- A keyword that the validator does not implement is never ignored silently.
  The validator reports it with `TYPCAST-SCH-0002`, so a contract that gains a
  keyword fails the check instead of passing every instance.
- The new public API is `validate_schema(value)` in Python and
  `validateSchema(value)` in TypeScript, and the method
  `Document.validate_schema()` and `Document.validateSchema()`. The function
  checks any JSON value, and the method checks the JSON value of the document.
  Both report every rule that the value breaks and raise no error.
- The reader of both SDKs keeps its own error contract and stays unchanged. The
  schema validation is opt-in and separate from the semantic engine of
  ADR-0026, and the builder does not call it.
- The diagnostics of the schema validation use a new family `TYPCAST-SCH-*` with
  the phase `validation`. `TYPCAST-SCH-0001` names an instance that breaks a
  rule of the schema, and `TYPCAST-SCH-0002` names a keyword of the schema that
  the validator does not implement. The phase vocabulary is unchanged, because
  the check is a validation.
- A message of an enumeration lists the allowed values when there are at most
  eight of them, and names the number of the values otherwise. The details hold
  the whole list under `allowed` in both cases. The paper catalog holds 107
  variants, and a message that lists all of them is unreadable.
- The pattern of a schema is a pattern of ECMAScript. The Python SDK translates
  the anchor `$` into the end anchor of Python and compiles the pattern with
  the ASCII flag, so that both SDKs accept and reject the same text.

## Consequences

- A caller can check a document against the published contract with the package
  it already installs, and the check needs no external tool.
- The two SDKs report the same diagnostics for the same instance, because the
  shared fixtures of `tests/fixtures/schema/` name the diagnostics that both
  validators must report.
- A keyword that the contract gains and the validator does not know is caught
  by the stage `//tests/schema:schema_py` and by the unit test of the
  TypeScript SDK, which walk the whole embedded contract.
- The validator is a second implementation of the contract, and it is a copy
  that can drift from the reader. The drift is caught by the shared fixtures,
  because the reader and the validator agree on every fixture of the repository.
- The validator implements only the subset that the contract uses. A contract
  that needs another keyword needs a rule in both SDKs, and the keyword check
  names the keyword that is missing.
- The generated source file grows with the contract, and the size of the
  packages grows with it. The contract is the size of the document IR, so the
  growth is bounded and is paid for by the callers that use the check.
- The reader and the semantic engine stay unchanged, so a document that the
  reader rejects is still rejected by the reader and not by the validator.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| A third-party JSON Schema library | It breaks the dependency-free rule of the SDKs and adds a dependency tree to two packages that carry none today. |
| Reading the schema bundle at run time | A published package would need the files of the repository beside it, and the paths of the bundle would leak into the public surface of the package. |
| Validating in the reader | The reader has its own error contract, and ADR-0002 keeps the reader and the schema layer apart. A change of the reader would change the error that a caller sees. |
| Validating in the builder | The builder would then run two validation layers, and a caller that only wants the semantic rules would pay for the schema check. |
| Validating against the meta-schema only | The meta-schema describes a schema document, not a document of the IR. It cannot answer whether an instance satisfies the contract. |
| One validator in a shared module | The SDKs depend on no code outside their own package, and a shared module would make the two SDKs depend on each other. |
| Listing every allowed value in a message | The paper catalog holds 107 variants, and the message would be unreadable. The details hold the whole list. |
| A new code for every keyword | The number of keywords grows with the contract, and a caller that handles a violation of a rule would have to handle a code per keyword. The keyword belongs in the details. |

## References

- `docs/specifications/schema.md`
- `docs/specifications/sdk-api.md`
- `docs/specifications/diagnostics.md`
- `API-029`, `DIAG-019`, `SCH-024`, `TEST-034`
- [ADR-0002](ADR-0002-hybrid-schema-and-builders.md)
- [ADR-0005](ADR-0005-two-phase-validation-and-diagnostics.md)
- [ADR-0026](ADR-0026-semantic-validation-engine-configuration-and-build.md)
