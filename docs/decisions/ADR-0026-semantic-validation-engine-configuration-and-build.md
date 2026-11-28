# ADR-0026: Semantic validation engine, its configuration, and the build

Status: Accepted
Date: 2026-11-28
Supersedes: ADR-0024
Superseded by: none

## Context

The model constructors and the reader of the document IR check the rules that
one node carries: a required field, a closed object, a discriminator, a
length, a number domain, and a text length. Three rules of the IR span more
than one node, and no constructor can check them: the shape of a table, the
uniqueness of a module alias, and the size of a raw node.

ADR-0005 names the engine the second layer of the validation and keeps the
serialization of a built model free of a second validation. ADR-0017 places the
raw size limit in the engine, makes it the only configurable limit, and
requires it to be enforced during the validation at `build()`. The contract of
the SDK API named one configuration that holds the asset root, the compiler
path, the timeout, and the raw limit together, but the first three belong to
the asset layer and the compiler adapter, which do not exist yet.

The engine also needed a contract of its own: which problems it reports, in
which order, and whether it raises.

ADR-0024 fixed that contract and named `Document.validate(config=None)` and
`Document.validate(options?)` as the place where a caller passes the
configuration. The builder arrived afterwards, and it runs the engine again
before it returns a document. ADR-0024 gave the builder no way to pass the
configuration, so the raw limit of a build was always the default of one MiB,
and the SDK API specification stated that `build()` takes no configuration. A
caller that needed a different limit at build time had to build the document
with the default limit and to call `validate()` a second time with the limit
it wanted, which contradicts ADR-0017, because the oversized raw node was
already accepted by the build.

## Decision

Implement a semantic validation engine as a separate layer of both SDKs, and
let the builder pass the configuration of the engine to the validation run of
the build.

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
- `build(config=None)` and `build(options?)` take the same configuration and
  apply it to the validation run of the build. The raw limit of a build is the
  limit of the call, and it is the default limit when the call names no
  configuration.
- The builder checks the type of the configuration itself, because the
  configuration is an argument of a public method. An argument that is not a
  configuration raises `ApiUsageError` with `TYPCAST-API-0001`, the phase
  `api`, and the path `/build`.
- The builder reads the configuration before it does any work, so an invalid
  configuration is reported before a problem of the document.
- The serialization of a built model does not validate again, because ADR-0005
  decided that. `to_json()` and `toJSONString()` write the document as it is.

The two SDKs report the same diagnostics for the same configuration, but the
moment of the check of the limit differs, because the types differ. The
configuration of Python is a frozen dataclass that checks its value when it is
built, so `TypcastConfig(max_raw_bytes=-1)` raises the configuration error at
that call. The configuration of TypeScript is a plain object, so the limit is
checked when the call resolves it. Both report `TYPCAST-CONFIG-0004`, the
phase `config`, and the path `/max_raw_bytes`.

## Consequences

- A document that the constructors accept can still be rejected by the engine,
  and the caller sees every reason at once.
- The order of the diagnostics is a part of the contract, so a cross-language
  test can compare the results of the two SDKs.
- The configuration of the engine is small, and it grows when the asset layer
  and the compiler adapter arrive.
- The engine is a pure function of the document and of the configuration, so it
  can be tested without a compiler and without a file system.
- A caller that needs a raw limit other than the default applies it to the
  build itself, and the document that the build rejects never reaches the
  caller.
- The builder holds one more argument, and the argument is checked before the
  builder does any work, so a wrong argument changes no state of the builder.
- The configuration of the build is not stored in the document, so a later
  `validate()` of the document uses the default limit again.
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
| A separate configuration for the builder | The limits of the builder and the limits of the engine are the same limits, and two configurations of the same limit would drift. |
| A raw limit as a plain number in `build()` | The configuration of the engine grows when the asset layer arrives, and a plain number would change the signature of the call a second time. |
| Keeping the limit of a build at the default | ADR-0017 requires the limit to be enforced at `build()`, and a caller that cannot choose the limit cannot enforce it there. |

## References

- `docs/specifications/document-ir.md`
- `docs/specifications/sdk-api.md`
- `docs/specifications/diagnostics.md`
- `IR-006`, `IR-010`, `IR-019`, `API-007`, `API-028`, `NODE-008`, `NODE-023`
- [ADR-0005](ADR-0005-two-phase-validation-and-diagnostics.md)
- [ADR-0017](ADR-0017-resource-limits.md)
