# Diagnostics

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-27

## Purpose

Typcast reports failures through structured diagnostics rather than free-form
strings. The same diagnostic shape is used in Python and TypeScript so that
cross-language tests can compare behavior and applications can handle specific
failures programmatically.

## Diagnostic shape

```json
{
  "code": "TYPCAST-VAL-0001",
  "severity": "error",
  "phase": "validation",
  "message": "Field 'paper' is required.",
  "path": "/page",
  "location": null,
  "details": {},
  "cause": null
}
```

| Field | Type | Required | Meaning |
|---|---|---|---|
| `code` | string | Yes | Stable identifier in the `TYPCAST-<FAMILY>-<NUMBER>` format. |
| `severity` | string | Yes | `error`, `warning`, or `info`. |
| `phase` | string | Yes | `api`, `validation`, `serialization`, `emit`, `compiler`, `io`, or `config`. |
| `message` | string | Yes | Human-readable English message. |
| `path` | string or null | Yes | JSON Pointer to the affected document location, when known. The tokens of the pointer are escaped as RFC 6901 defines them, so a property named `bad/name` is reported as `/bad~1name`. |
| `location` | object or null | Yes | Compiler source location, when known. |
| `details` | object | Yes | Machine-readable context. |
| `cause` | string or null | Yes | Stable cause identifier, not a stack trace. |

`location` has the shape:

```json
{ "file": "document.typ", "line": 12, "column": 8 }
```

`details` must be JSON-serializable. It may contain raw compiler output, exit
codes, field names, or supported version ranges. A value of a type that JSON
cannot represent is replaced by the name of its type, and a number that is not
finite is spelled in the form of ECMAScript.

The `message` of a diagnostic is human-readable text. When it shows a rejected
value, it shows it in the canonical form of the next section, so that the
message stays readable.

## Rejected values

A message that shows a rejected value shows it in one canonical form. The two
SDKs apply the same rule, so that the message of a diagnostic is the same in
both SDKs.

| Step | Rule |
|---|---|
| Text | The value is reduced to its text. A value of a type that JSON cannot represent is the name of its type, and a number that is not finite is spelled in the form of ECMAScript. |
| Length | The text holds at most 64 Unicode code points. A longer text is cut after the 64th code point, and an ellipsis (`…`) follows the cut. |
| Escaping | A backslash becomes `\\`, a single quote becomes `\'`, a double quote becomes `\"`, a newline becomes `\n`, a carriage return becomes `\r`, a tab becomes `\t`, and every other control character (U+0000 to U+001F and U+007F) becomes a `\u00xx` escape with lower-case hexadecimal digits. Every other character is shown as it is. |

The length is counted in Unicode code points, and the cut never splits a
character that lies outside the basic multilingual plane.

The `details` of a diagnostic hold the rejected value under `value` in the
JSON-safe form: the value itself for a string, a number, a boolean, or `null`,
and the name of its type for a value of another type. The details are
machine-readable, and the message holds the canonical text of the value.

## Message wording

The two SDKs report an invalid input in the same words. The wording follows
these rules:

- A message names the path of the failing node, the rule that the value broke,
  and the rejected value when the value helps the reader.
- A collection is an array, because the IR is a JSON IR. A message names the
  elements of the collection, such as `an array of Span values`.
- An element of a collection names its type, such as `must be a Span`.
- A rejected enum value is shown in single quotes after `got`, and a rejected
  value of another type is not shown at all.
- A rejected value is shown in the canonical form of the section above, so
  that a quote, a backslash, and a control character never break the text of
  a message.
- The reason of a parser of the runtime belongs to `details`, not to the
  message, because the parsers of the two runtimes word their reason
  differently. The message of a malformed JSON text is the same in both SDKs.

The `details` of a diagnostic follow the same rules in both SDKs:

- The details name the rejected value under `value`, the allowed literals
  under `allowed`, the name of the expected element under `expected`, the name
  of the missing or unknown field under `field`, and the length of a string
  under `length` and `maxLength`.
- The details hold no text of the runtime, because the two runtimes word their
  own errors differently. The reason of the parser of a malformed JSON text is
  the only such text, and it belongs to the details under `reason`.

## Code families

| Prefix | Family | Raised by |
|---|---|---|
| `TYPCAST-API-*` | Public API misuse | Builder and public methods. |
| `TYPCAST-VAL-*` | Document validation | Schema and semantic validation. |
| `TYPCAST-IR-*` | Serialization and deserialization | JSON and schema version handling. |
| `TYPCAST-EMIT-*` | Typst emission | Emitter invariants and unsupported nodes. |
| `TYPCAST-COMPILER-*` | Compiler lifecycle | Discovery, version, execution, timeout, output. |
| `TYPCAST-IO-*` | Filesystem and assets | Asset resolution, reads, and writes. |
| `TYPCAST-CONFIG-*` | Configuration | Invalid config values. |

## Initial code catalog

The catalog is `PROPOSED` until the first stable release. Codes become stable
when `1.0.0` is released. New codes may be added in a minor release; existing
codes must not be renumbered or reused.

### API

| Code | Severity | Phase | Meaning |
|---|---|---|---|
| `TYPCAST-API-0001` | error | api | Invalid argument type or value passed to a public method. |
| `TYPCAST-API-0002` | error | api | Method called in an invalid state. |

The builder raises `TYPCAST-API-0001` when an argument has a type that the
method cannot use. The fluent builder of this release has no path that calls a
method in an invalid state, so no call raises `TYPCAST-API-0002`: `build()`
may be called more than once, and every metadata method may be called more than
once.

### Validation

| Code | Severity | Phase | Meaning |
|---|---|---|---|
| `TYPCAST-VAL-0001` | error | validation | Required field is missing. |
| `TYPCAST-VAL-0002` | error | validation | Unknown field is present. |
| `TYPCAST-VAL-0003` | error | validation | Enum or discriminator value is invalid. |
| `TYPCAST-VAL-0004` | error | validation | Length value or unit is invalid. |
| `TYPCAST-VAL-0005` | error | validation | Heading level is outside 1 to 6. |
| `TYPCAST-VAL-0006` | error | validation | Required content is empty. |
| `TYPCAST-VAL-0007` | error | validation | Table row and column counts differ. |
| `TYPCAST-VAL-0008` | error | validation | Module alias is duplicated or invalid. |
| `TYPCAST-VAL-0009` | error | validation | Module alias and items are both set. |
| `TYPCAST-VAL-0010` | error | validation | Raw content exceeds the size limit. |
| `TYPCAST-VAL-0011` | error | validation | Date is not a valid `YYYY-MM-DD` value. |
| `TYPCAST-VAL-0012` | error | validation | Image or module path is absolute or unsafe. |
| `TYPCAST-VAL-0013` | error | validation | Text holds more code points than the contract allows. |

### Serialization

| Code | Severity | Phase | Meaning |
|---|---|---|---|
| `TYPCAST-IR-0001` | error | serialization | JSON is malformed. |
| `TYPCAST-IR-0002` | error | serialization | Schema version is unsupported. |
| `TYPCAST-IR-0003` | error | serialization | Document cannot be serialized. |
| `TYPCAST-IR-0004` | error | serialization | JSON value does not match the expected root shape. |

### Emitter

| Code | Severity | Phase | Meaning |
|---|---|---|---|
| `TYPCAST-EMIT-0001` | error | emit | Emitter invariant failed. |
| `TYPCAST-EMIT-0002` | error | emit | Unknown block or span type. |
| `TYPCAST-EMIT-0003` | error | emit | Value cannot be escaped safely. |

### Compiler

| Code | Severity | Phase | Meaning |
|---|---|---|---|
| `TYPCAST-COMPILER-0001` | error | compiler | Typst executable was not found. |
| `TYPCAST-COMPILER-0002` | error | compiler | Typst version is outside the supported range. |
| `TYPCAST-COMPILER-0003` | error | compiler | Compilation timed out. |
| `TYPCAST-COMPILER-0004` | error | compiler | Typst exited with a non-zero status. |
| `TYPCAST-COMPILER-0005` | error | compiler | PDF output is missing, empty, or invalid. |
| `TYPCAST-COMPILER-0006` | error | compiler | Typst version output could not be parsed. |

### IO

| Code | Severity | Phase | Meaning |
|---|---|---|---|
| `TYPCAST-IO-0001` | error | io | Asset or module was not found. |
| `TYPCAST-IO-0002` | error | io | Path traversal was detected. |
| `TYPCAST-IO-0003` | error | io | Absolute path was rejected. |
| `TYPCAST-IO-0004` | error | io | Asset could not be read. |
| `TYPCAST-IO-0005` | error | io | Output could not be written. |
| `TYPCAST-IO-0006` | error | io | Asset path is a directory or special file. |

### Configuration

| Code | Severity | Phase | Meaning |
|---|---|---|---|
| `TYPCAST-CONFIG-0001` | error | config | `assetRoot` is missing, not a directory, or inaccessible. |
| `TYPCAST-CONFIG-0002` | error | config | Timeout is not a positive finite number. |
| `TYPCAST-CONFIG-0003` | error | config | Compiler path is invalid. |
| `TYPCAST-CONFIG-0004` | error | config | Raw size limit is invalid. |

## Semantic diagnostics

The validation engine reports the diagnostics of the rules that span more than
one node. The details of every diagnostic of the engine name the numbers of
the rule, so that a caller can act on them without reading the message.

| Code | Path | Details | Message |
|---|---|---|---|
| `TYPCAST-VAL-0007` | The row of the table. | `columns` is the number of the columns of the table, and `cells` is the number of the cells of the row. | `'/contents/0/rows/1' must hold 2 cells, got 1.` |
| `TYPCAST-VAL-0008` | The alias of the later module. | `alias` is the duplicated alias, and `duplicateOf` is the path of the module that uses the alias first. | `'/modules/1/alias' is already used by the module at '/modules/0/alias'.` |
| `TYPCAST-VAL-0010` | The value of the raw node. | `maxBytes` is the limit of the call, and `bytes` is the number of the bytes of the UTF-8 encoding of the value. | `'/contents/0/value' must not hold more than 8 bytes, got 9.` |
| `TYPCAST-CONFIG-0004` | `/max_raw_bytes`. | `value` is the rejected limit. | `'/max_raw_bytes' must not be negative, got '-1'.` |

The engine reports every problem it finds and raises no error for a semantic
problem. The diagnostics come in the order of the document: the blocks in the
order of the contents, the spans in the order of their content, the rows of a
table in the order of the table, and the modules in the order of their
declaration. Two SDKs report the same diagnostics in the same order for the
same document.

## Error classes

| Python | TypeScript | Base | Typical codes |
|---|---|---|---|
| `TypcastError` | `TypcastError` | `Exception` / `Error` | Any. |
| `ApiUsageError` | `ApiUsageError` | `TypcastError` | `TYPCAST-API-*` |
| `ValidationError` | `ValidationError` | `TypcastError` | `TYPCAST-VAL-*` |
| `SerializationError` | `SerializationError` | `TypcastError` | `TYPCAST-IR-*` |
| `EmitError` | `EmitError` | `TypcastError` | `TYPCAST-EMIT-*` |
| `CompileError` | `CompileError` | `TypcastError` | `TYPCAST-COMPILER-*` |
| `AssetError` | `AssetError` | `TypcastError` | `TYPCAST-IO-*` |
| `ConfigError` | `ConfigError` | `TypcastError` | `TYPCAST-CONFIG-*` |

Every error exposes a `diagnostics` collection. A single error may carry multiple
diagnostics. The first diagnostic is the primary cause; the rest provide
context.

## Paths and locations

- `path` uses JSON Pointer syntax, for example `/page/margin/top`.
- `path` is `null` when the failure is not tied to a document location.
- `location` is used for compiler diagnostics.
- `location.file` is relative to the compiler workspace when possible.
- Windows extended paths are normalized for display.
- `details.raw` preserves the original compiler line.

## Warning policy

Warnings use the same shape and a `warning` severity. The policy is `CONFIRMED`:

| Rule | Decision |
|---|---|
| Warning conditions | Only the conditions listed in this section produce warnings. Everything else is an error. |
| `build()` | Warnings never raise. `build()` raises only for error diagnostics. |
| `validate()` | Returns warnings and errors together, in document order. |
| `to_typst()` and `compile_pdf()` | Raise only for error diagnostics. |
| `CompileResult.diagnostics` | Contains the warnings produced during compilation, including compiler warnings. |
| Release gate | Warnings never fail a build, a test lane, or a release gate in the MVP. CI reports them. |
| Promotion | Warnings cannot be promoted to errors by configuration in the MVP. |
| Parity | Python and TypeScript produce the same warning for the same input. |

The MVP produces warnings in exactly three situations:

1. The compiler adapter used `allow_unsupported_typst`, so the compiler version
   is outside the supported range.
2. The Typst CLI emitted a warning during compilation.
3. A public API that is deprecated in the current release was used.

A warning never changes the exit behavior of an operation. A caller that wants
to treat warnings as errors must inspect `diagnostics` itself.

Warnings are not localized separately from errors; both use English messages in
`1.0.0`.

## Localization

Diagnostic messages are English-only for `1.0.0`. The `code` is the stable
contract; applications must not parse the message. Localization is Post-MVP.

## Parity testing

Python and TypeScript diagnostics are compared on:

- `code`
- `severity`
- `phase`
- `path`
- `location` when deterministic
- `details` after removing raw compiler output and the reason of the parser of
  the runtime
- `message`

Raw compiler output is excluded because it may contain absolute paths or
platform-specific formatting. The reason of the parser is excluded because the
parsers of the two runtimes word their reason differently.

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| DIAG-001 | Every diagnostic MUST have the documented shape. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the `Diagnostic` type of `typcast.diagnostics` and of `packages/typescript/src/diagnostics.ts`. |
| DIAG-002 | Codes MUST follow `TYPCAST-<FAMILY>-<NUMBER>`. | CONFIRMED | Lint. |
| DIAG-003 | Existing codes MUST NOT be renumbered or reused. | CONFIRMED | Release review. |
| DIAG-004 | Python and TypeScript MUST expose the same diagnostic fields. | IMPLEMENTED | The `Diagnostic` shape of both SDKs; `//tests/contract:contract_py` and `//tests/contract:contract_ts_test` compare the code of every negative fixture. |
| DIAG-005 | Errors MUST inherit from `TypcastError`. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the error cases, and `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run`; the `ApiUsageError` cases of both SDKs. |
| DIAG-006 | Validation errors MUST include a JSON Pointer when known. | IMPLEMENTED | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the diagnostic path points at the failing node. |
| DIAG-013 | The tokens of a JSON Pointer MUST be escaped as RFC 6901 defines them. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the escaped-pointer cases. |
| DIAG-014 | The details of a diagnostic MUST stay JSON-serializable. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the details cases. |
| DIAG-015 | The message of a diagnostic MUST be the same in both SDKs, and MUST show at most 64 code points of a rejected value. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the message cases, and `//tests/contract:contract_py` and `//tests/contract:contract_ts_test` compare the message of every negative fixture that the manifest names. |
| DIAG-016 | The details of a diagnostic MUST be the same in both SDKs, except the reason of the parser of the runtime. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the details cases, and `//tests/contract:contract_py` and `//tests/contract:contract_ts_test` compare the details of every negative fixture that the manifest names. |
| DIAG-017 | A rejected value MUST be shown in one canonical form in both SDKs: the same escaping of the quotes, the backslash, and the control characters, and the same limit of 64 Unicode code points. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the rejected-value cases, and the shared fixtures `date-quoted.json`, `date-control-chars.json`, `date-long.json`, `date-unicode.json`, `version-quoted.json`, `version-control-chars.json`, `version-long.json`, `enum-quoted.json`, `enum-control-chars.json`, and `enum-long.json` of `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`. |
| DIAG-007 | Compiler diagnostics MUST preserve raw output in `details.raw`. | CONFIRMED | Compiler test. |
| DIAG-008 | Compiler diagnostics MUST include location when parseable. | CONFIRMED | Compiler test. |
| DIAG-009 | Messages MUST be English-only for `1.0.0`. | IMPLEMENTED | Every diagnostic message of both SDKs is English. |
| DIAG-010 | Applications MUST be able to handle errors by code. | IMPLEMENTED | The `TYPCAST-*` code constants of both SDKs; the manifest of the shared fixtures names the expected code of every negative fixture, and the builder cases of `//packages/python/tests:builder_tests` and `//packages/typescript:builder_test_run` name the code of every error of the builder. |
| DIAG-011 | Warnings MUST follow the policy in this document: only the listed conditions warn, warnings never raise, and warnings never fail a release gate. | CONFIRMED | Warning-policy tests and release review. |
| DIAG-012 | Diagnostic codes MUST be documented in a catalog. | CONFIRMED | This document. |
| DIAG-018 | The semantic validation engine MUST report every problem it finds and MUST report the diagnostics in the order of the document. | IMPLEMENTED | `//packages/python/tests:validation_tests` and `//packages/typescript:validation_test_run`; the order cases of both SDKs, and the fixtures of `//tests/contract:validation_py` and `//tests/contract:validation_ts_test`. |

## Open questions

- Should diagnostics be localized after `1.0.0`?
- Should codes be exposed as constants in the SDKs?
- Should warning promotion to errors be configurable in a later version?

## Related documents

- [SDK API](sdk-api.md)
- [Compiler adapter](compiler.md)
- [Testing](../development/testing.md)
- [ADR-0005](../decisions/ADR-0005-two-phase-validation-and-diagnostics.md)
- [ADR-0014](../decisions/ADR-0014-diagnostic-warning-policy.md)
- [ADR-0024](../decisions/ADR-0024-semantic-validation-engine-and-configuration.md)
