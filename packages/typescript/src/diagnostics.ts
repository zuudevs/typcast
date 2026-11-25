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

// Validation codes. The catalog lives in `docs/specifications/diagnostics.md`.
export const CODE_REQUIRED_FIELD = "TYPCAST-VAL-0001";
export const CODE_UNKNOWN_FIELD = "TYPCAST-VAL-0002";
export const CODE_INVALID_ENUM = "TYPCAST-VAL-0003";
export const CODE_INVALID_LENGTH = "TYPCAST-VAL-0004";
export const CODE_INVALID_HEADING_LEVEL = "TYPCAST-VAL-0005";
export const CODE_EMPTY_CONTENT = "TYPCAST-VAL-0006";
export const CODE_INVALID_MODULE_ALIAS = "TYPCAST-VAL-0008";
export const CODE_MODULE_ALIAS_AND_ITEMS = "TYPCAST-VAL-0009";
export const CODE_INVALID_DATE = "TYPCAST-VAL-0011";

// Serialization codes.
export const CODE_MALFORMED_JSON = "TYPCAST-IR-0001";
export const CODE_UNSUPPORTED_VERSION = "TYPCAST-IR-0002";
export const CODE_NOT_SERIALIZABLE = "TYPCAST-IR-0003";
export const CODE_ROOT_SHAPE = "TYPCAST-IR-0004";

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
