/**
 * Structured diagnostics and the Typcast error hierarchy.
 *
 * The shapes follow `docs/specifications/diagnostics.md`. Every error raised
 * by the SDK inherits from `TypcastError` and exposes a `diagnostics`
 * collection. The first diagnostic is the primary cause.
 */

/** The severity of a diagnostic. */
export type Severity = "error" | "warning" | "info";

/** The phase that produced a diagnostic. */
export type Phase =
  | "api"
  | "validation"
  | "serialization"
  | "emit"
  | "compiler"
  | "io"
  | "config";

/** The source location of a compiler diagnostic. */
export interface SourceLocation {
  readonly file: string;
  readonly line: number;
  readonly column: number;
}

/** A single machine-readable problem report. */
export interface Diagnostic {
  readonly code: string;
  readonly severity: Severity;
  readonly phase: Phase;
  readonly message: string;
  readonly path: string | null;
  readonly location: SourceLocation | null;
  readonly details: Readonly<Record<string, unknown>>;
  readonly cause: string | null;
}

export const SEVERITY_ERROR: Severity = "error";
export const SEVERITY_WARNING: Severity = "warning";
export const SEVERITY_INFO: Severity = "info";

export const PHASE_API: Phase = "api";
export const PHASE_VALIDATION: Phase = "validation";
export const PHASE_SERIALIZATION: Phase = "serialization";
export const PHASE_EMIT: Phase = "emit";
export const PHASE_COMPILER: Phase = "compiler";
export const PHASE_IO: Phase = "io";
export const PHASE_CONFIG: Phase = "config";

// Public API codes. The catalog lives in `docs/specifications/diagnostics.md`.
export const CODE_INVALID_ARGUMENT = "TYPCAST-API-0001";
export const CODE_INVALID_STATE = "TYPCAST-API-0002";

// Validation codes. The catalog lives in `docs/specifications/diagnostics.md`.
export const CODE_REQUIRED_FIELD = "TYPCAST-VAL-0001";
export const CODE_UNKNOWN_FIELD = "TYPCAST-VAL-0002";
export const CODE_INVALID_ENUM = "TYPCAST-VAL-0003";
export const CODE_INVALID_LENGTH = "TYPCAST-VAL-0004";
export const CODE_INVALID_HEADING_LEVEL = "TYPCAST-VAL-0005";
export const CODE_EMPTY_CONTENT = "TYPCAST-VAL-0006";
export const CODE_TABLE_SHAPE = "TYPCAST-VAL-0007";
// The catalog assigns one code to a module alias that is invalid and to a
// module alias that is duplicated, so the constant covers both cases.
export const CODE_INVALID_MODULE_ALIAS = "TYPCAST-VAL-0008";
export const CODE_MODULE_ALIAS_AND_ITEMS = "TYPCAST-VAL-0009";
export const CODE_RAW_TOO_LARGE = "TYPCAST-VAL-0010";
export const CODE_INVALID_DATE = "TYPCAST-VAL-0011";
export const CODE_STRING_TOO_LONG = "TYPCAST-VAL-0013";

// Serialization codes.
export const CODE_MALFORMED_JSON = "TYPCAST-IR-0001";
export const CODE_UNSUPPORTED_VERSION = "TYPCAST-IR-0002";
export const CODE_NOT_SERIALIZABLE = "TYPCAST-IR-0003";
export const CODE_ROOT_SHAPE = "TYPCAST-IR-0004";

// Configuration codes.
export const CODE_INVALID_RAW_LIMIT = "TYPCAST-CONFIG-0004";

// Schema codes. The family names the validation of an instance against the
// JSON Schema contract of the project.
export const CODE_SCHEMA_VIOLATION = "TYPCAST-SCH-0001";
export const CODE_SCHEMA_UNSUPPORTED_KEYWORD = "TYPCAST-SCH-0002";

/** The number of characters of a value that the message of a diagnostic shows. */
export const MAX_DIAGNOSTIC_VALUE_LENGTH = 64;

/**
 * Returns a JSON-serializable representation of a value.
 *
 * The details of a diagnostic must be JSON-serializable, so a value of an
 * unknown type is represented by the name of its type, and a number that is
 * not finite is represented by its spelling in the form of ECMAScript. The
 * Python SDK applies the same rule.
 */
export function safeValue(value: unknown): unknown {
  if (value === null) {
    return null;
  }
  const kind = typeof value;
  if (kind === "string" || kind === "boolean") {
    return value;
  }
  if (kind === "number") {
    return Number.isFinite(value) ? value : String(value);
  }
  if (Array.isArray(value)) {
    return "array";
  }
  if (kind === "object") {
    return "object";
  }
  return kind;
}

/**
 * Returns the canonical text of a rejected value.
 *
 * The text holds at most 64 code points of the value, followed by an ellipsis
 * when the value is longer. Every character that could break the text of a
 * message is escaped, so that a quote, a backslash, a newline, a carriage
 * return, a tab, and any other control character appear as an escape
 * sequence. Every other character is shown as it is.
 *
 * The rule is the one of `docs/specifications/diagnostics.md`, and the Python
 * SDK applies the same rule, so that the message of a diagnostic is the same
 * in both SDKs.
 */
export function safeText(value: unknown): string {
  const text = typeof value === "string" ? value : String(safeValue(value));
  const characters = [...text];
  if (characters.length <= MAX_DIAGNOSTIC_VALUE_LENGTH) {
    return escapeText(text);
  }
  const shown = escapeText(
    characters.slice(0, MAX_DIAGNOSTIC_VALUE_LENGTH).join(""),
  );
  return `${shown}…`;
}

// The escape sequences of a rejected value. A control character that has no
// sequence of its own is written as a `\u00xx` escape. The Python SDK applies
// the same rule.
const ESCAPE_SEQUENCES: Readonly<Record<string, string>> = {
  "\\": "\\\\",
  "'": "\\'",
  '"': '\\"',
  "\n": "\\n",
  "\r": "\\r",
  "\t": "\\t",
};

/** Returns the text of a value with every breakable character escaped. */
function escapeText(text: string): string {
  let result = "";
  for (const character of text) {
    const sequence = ESCAPE_SEQUENCES[character];
    if (sequence !== undefined) {
      result += sequence;
      continue;
    }
    const code = character.codePointAt(0) ?? 0;
    if (code < 0x20 || code === 0x7f) {
      result += `\\u${code.toString(16).padStart(4, "0")}`;
      continue;
    }
    result += character;
  }
  return result;
}

/** The base class of every error raised by Typcast. */
export class TypcastError extends Error {
  /** The diagnostics that describe the failure. */
  readonly diagnostics: readonly Diagnostic[];

  constructor(
    message: string,
    diagnostics: readonly Diagnostic[] = [],
    name = "TypcastError",
  ) {
    super(message);
    this.name = name;
    this.diagnostics = Object.freeze([...diagnostics]);
    Object.freeze(this);
  }
}

/** Raised when a public API is used with an invalid argument or state. */
export class ApiUsageError extends TypcastError {
  constructor(message: string, diagnostics: readonly Diagnostic[] = []) {
    super(message, diagnostics, "ApiUsageError");
  }
}

/** Raised when a value violates the schema or the semantic rules. */
export class ValidationError extends TypcastError {
  constructor(message: string, diagnostics: readonly Diagnostic[] = []) {
    super(message, diagnostics, "ValidationError");
  }
}

/** Raised when JSON cannot be parsed, serialized, or version-matched. */
export class SerializationError extends TypcastError {
  constructor(message: string, diagnostics: readonly Diagnostic[] = []) {
    super(message, diagnostics, "SerializationError");
  }
}

/** Raised when a configuration value is invalid. */
export class ConfigError extends TypcastError {
  constructor(message: string, diagnostics: readonly Diagnostic[] = []) {
    super(message, diagnostics, "ConfigError");
  }
}

/** Builds the diagnostic of a misuse of the public API. */
export function apiDiagnostic(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): Diagnostic {
  return Object.freeze({
    code,
    severity: SEVERITY_ERROR,
    phase: PHASE_API,
    message,
    path,
    location: null,
    details: Object.freeze({ ...details }),
    cause: null,
  });
}

/** Builds the diagnostic of a validation failure. */
export function validationDiagnostic(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): Diagnostic {
  return Object.freeze({
    code,
    severity: SEVERITY_ERROR,
    phase: PHASE_VALIDATION,
    message,
    path,
    location: null,
    details: Object.freeze({ ...details }),
    cause: null,
  });
}

/** Builds the diagnostic of a serialization failure. */
export function serializationDiagnostic(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): Diagnostic {
  return Object.freeze({
    code,
    severity: SEVERITY_ERROR,
    phase: PHASE_SERIALIZATION,
    message,
    path,
    location: null,
    details: Object.freeze({ ...details }),
    cause: null,
  });
}

/** Raises a public API error that carries a single diagnostic. */
export function throwApi(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): never {
  throw new ApiUsageError(message, [
    apiDiagnostic(code, message, path, details),
  ]);
}

/** Raises a validation error that carries a single diagnostic. */
export function throwValidation(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): never {
  throw new ValidationError(message, [
    validationDiagnostic(code, message, path, details),
  ]);
}

/** Builds the diagnostic of an invalid configuration value. */
export function configDiagnostic(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): Diagnostic {
  return Object.freeze({
    code,
    severity: SEVERITY_ERROR,
    phase: PHASE_CONFIG,
    message,
    path,
    location: null,
    details: Object.freeze({ ...details }),
    cause: null,
  });
}

/** Raises a configuration error that carries a single diagnostic. */
export function throwConfig(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): never {
  throw new ConfigError(message, [
    configDiagnostic(code, message, path, details),
  ]);
}

/** Raises a serialization error that carries a single diagnostic. */
export function throwSerialization(
  code: string,
  message: string,
  path: string | null = null,
  details: Readonly<Record<string, unknown>> = {},
): never {
  throw new SerializationError(message, [
    serializationDiagnostic(code, message, path, details),
  ]);
}

/** Returns the diagnostics with their JSON Pointer paths prefixed. */
export function withPath(
  diagnostics: readonly Diagnostic[],
  prefix: string,
): readonly Diagnostic[] {
  if (prefix === "") {
    return diagnostics;
  }
  return Object.freeze(
    diagnostics.map((diagnostic) =>
      Object.freeze({
        ...diagnostic,
        path: diagnostic.path === null ? prefix : prefix + diagnostic.path,
      }),
    ),
  );
}
