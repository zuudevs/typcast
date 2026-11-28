# ADR-0024: Semantic validation engine and its configuration

Status: Superseded
Date: 2026-11-27
Supersedes: none
Superseded by: ADR-0026

> Superseded by
> [ADR-0026](ADR-0026-semantic-validation-engine-configuration-and-build.md).
> The rules of the engine are restated unchanged, and the builder passes the
> configuration of the engine to the validation run of the build.

## Context

The model constructors and the reader of the document IR check the rules that
one node carries: a required field, a closed object, a discriminator, a
length, a number domain, and a text length. Three rules of the IR span more
than one node, and no constructor can check them: the shape of a table, the
uniqueness of a module alias, and the size of a raw node.

ADR-0005 names the engine the second layer of the validation and keeps the
serialization of a built model free of a second validation. ADR-0017 places the
raw size limit in the engine and makes it the only configurable limit. The
contract of the SDK API named one configuration that holds the asset root, the
compiler path, the timeout, and the raw limit together, but the first three
belong to the asset layer and the compiler adapter, which do not exist yet.

The engine also needed a contract of its own: which problems it reports, in
which order, and whether it raises.

## Decision

Implement a semantic validation engine as a separate layer of both SDKs.

- `Document.validate(config=None)` and `Document.validate(options?)` return the
  diagnostics of the semantic rules. The method reports every problem it finds
  and raises no error for a semantic problem, so that a caller can show all of
  them at once.
- The engine checks exactly three rules in this release: the shape of a table
  (`TYPCAST-VAL-0007`), the uniqueness of a module alias (`TYPCAST-VAL-0008`),
  and the size of a raw node (`TYPCAST-VAL-0010`).
- The diagnostics come in the order of the document: the blocks in the order of
  the contents, the spans in the order of their content, the rows of a table in
  the order of the table, and the modules in the order of their declaration.
- The configuration is passed per call and is never stored in the document. In
  this release it holds the raw size limit only, because the asset root, the
  compiler path, and the timeout belong to the layers that read files and run
  the compiler.
- The raw size limit is a limit per raw node, it is inclusive, and it counts
  the bytes of the UTF-8 encoding of the value. The default is 1 MiB.
- An invalid configuration raises `ConfigError` with `TYPCAST-CONFIG-0004`, the
  phase `config`, and the path `/max_raw_bytes`. The limit must be an integer
  that is finite and not negative.
- The serialization of a built model does not validate again, because ADR-0005
  decided that. `to_json()` and `toJSONString()` write the document as it is.

## Consequences

- A document that the constructors accept can still be rejected by the engine,
  and the caller sees every reason at once.
- The order of the diagnostics is a part of the contract, so a cross-language
  test can compare the results of the two SDKs.
- The configuration of the engine is small, and it grows when the asset layer
  and the compiler adapter arrive.
- The engine is a pure function of the document and of the configuration, so it
  can be tested without a compiler and without a file system.
- The prose of the SDK API that grouped `to_json()` with the raising operations
  was a defect. It is corrected, and ADR-0005 is not superseded.

## Alternatives considered

| Alternative | Reason rejected |
|---|---|
| Checking the rules in the constructors | A constructor sees one node, so it cannot compare a row with the columns of its table or an alias with the other aliases. |
| Raising on the first problem | The caller would have to call the engine again after every fix, and the diagnostics of the two SDKs would depend on the order of the fixes. |
| Keeping the whole configuration from the start | The asset root, the compiler path, and the timeout would be fields that no layer reads, and every SDK would carry a configuration that cannot be used. |
| Counting the raw size in characters | The limit of ADR-0017 is a number of bytes, and two SDKs that count characters count a multi-byte text differently. |
| Validating again when the document is serialized | ADR-0005 decided that the serialization of a built model does not re-validate. |

## References

- `docs/specifications/document-ir.md`
- `docs/specifications/sdk-api.md`
- `docs/specifications/diagnostics.md`
- `IR-006`, `IR-010`, `IR-019`, `API-007`, `NODE-008`
- [ADR-0005](ADR-0005-two-phase-validation-and-diagnostics.md)
- [ADR-0017](ADR-0017-resource-limits.md)
