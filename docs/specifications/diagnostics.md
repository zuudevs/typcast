# Diagnostics

Status: CONFIRMED
Scope: Normative
Last updated: 2026-11-25

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
cannot represent is replaced by the name of its type.

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
- `details` after removing raw compiler output
- `message`

Raw compiler output is excluded because it may contain absolute paths or
platform-specific formatting.

## Requirements

| ID | Requirement | Status | Verification |
|---|---|---|---|
| DIAG-001 | Every diagnostic MUST have the documented shape. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the `Diagnostic` type of `typcast.diagnostics` and of `packages/typescript/src/diagnostics.ts`. |
| DIAG-002 | Codes MUST follow `TYPCAST-<FAMILY>-<NUMBER>`. | CONFIRMED | Lint. |
| DIAG-003 | Existing codes MUST NOT be renumbered or reused. | CONFIRMED | Release review. |
| DIAG-004 | Python and TypeScript MUST expose the same diagnostic fields. | IMPLEMENTED | The `Diagnostic` shape of both SDKs; `//tests/contract:contract_py` and `//tests/contract:contract_ts_test` compare the code of every negative fixture. |
| DIAG-005 | Errors MUST inherit from `TypcastError`. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the error cases. |
| DIAG-006 | Validation errors MUST include a JSON Pointer when known. | IMPLEMENTED | `//tests/contract:contract_py` and `//tests/contract:contract_ts_test`; the diagnostic path points at the failing node. |
| DIAG-013 | The tokens of a JSON Pointer MUST be escaped as RFC 6901 defines them. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the escaped-pointer cases. |
| DIAG-014 | The details of a diagnostic MUST stay JSON-serializable. | IMPLEMENTED | `//packages/python/tests:model_tests` and `//packages/typescript:model_test_run`; the details cases. |
| DIAG-007 | Compiler diagnostics MUST preserve raw output in `details.raw`. | CONFIRMED | Compiler test. |
| DIAG-008 | Compiler diagnostics MUST include location when parseable. | CONFIRMED | Compiler test. |
| DIAG-009 | Messages MUST be English-only for `1.0.0`. | IMPLEMENTED | Every diagnostic message of both SDKs is English. |
| DIAG-010 | Applications MUST be able to handle errors by code. | IMPLEMENTED | The `TYPCAST-*` code constants of both SDKs; the manifest of the shared fixtures names the expected code of every negative fixture. |
| DIAG-011 | Warnings MUST follow the policy in this document: only the listed conditions warn, warnings never raise, and warnings never fail a release gate. | CONFIRMED | Warning-policy tests and release review. |
| DIAG-012 | Diagnostic codes MUST be documented in a catalog. | CONFIRMED | This document. |

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
