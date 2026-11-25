/**
 * Shared helpers of the immutable document model.
 *
 * The helpers implement the model-level invariants of the IR: argument types,
 * allowed enum values, and the element types of collections. The rules that
 * belong to the document validation layer, such as the table shape, the asset
 * paths, and the raw size limit, are deliberately not implemented here.
 */

import {
  CODE_EMPTY_CONTENT,
  CODE_INVALID_ENUM,
  CODE_REQUIRED_FIELD,
  throwValidation,
} from "../diagnostics.js";

/** Returns a string argument after checking its type and length. */
export function requireString(
  value: unknown,
  path: string,
  allowEmpty = false,
): string {
  if (typeof value !== "string") {
    throwValidation(CODE_REQUIRED_FIELD, `'${path}' must be a string.`, path);
  }
  if (!allowEmpty && value.length === 0) {
    throwValidation(
      CODE_EMPTY_CONTENT,
      `'${path}' must not be empty.`,
      path,
    );
  }
  return value;
}

/** Returns an enum argument after checking that it is a known literal. */
export function requireEnum<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): T {
  const names = [...allowed].sort();
  if (typeof value !== "string" || !allowed.includes(value as T)) {
    throwValidation(
      CODE_INVALID_ENUM,
      `'${path}' must be one of ${names.join(", ")}.`,
      path,
      { allowed: names },
    );
  }
  return value as T;
}

/** Returns a boolean argument after checking its type. */
export function requireBoolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${path}' must be a boolean.`,
      path,
    );
  }
  return value;
}

/** Returns an integer argument after checking its type. */
export function requireInteger(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${path}' must be an integer.`,
      path,
    );
  }
  return value;
}

/** Returns a numeric argument after checking its type. */
export function requireNumber(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${path}' must be a finite number.`,
      path,
    );
  }
  return value;
}

/** Returns a model argument after checking its type. */
export function requireInstance<T>(
  value: unknown,
  expected: abstract new (...args: never[]) => T,
  path: string,
): T {
  if (!(value instanceof expected)) {
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${path}' must be a ${expected.name}.`,
      path,
      { expected: expected.name },
    );
  }
  return value;
}

/** Returns a copied array after checking that the value is an array. */
export function requireArray(
  value: unknown,
  path: string,
  allowEmpty = true,
): readonly unknown[] {
  if (!Array.isArray(value)) {
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${path}' must be an array.`,
      path,
    );
  }
  if (!allowEmpty && value.length === 0) {
    throwValidation(
      CODE_EMPTY_CONTENT,
      `'${path}' must not be empty.`,
      path,
    );
  }
  return [...value];
}

/** Returns a frozen copy of an array. */
export function freezeArray<T>(items: readonly T[]): readonly T[] {
  return Object.freeze([...items]);
}
