/**
 * The checks of the arguments of the public API.
 *
 * The type of an argument of a public method is a rule of the API and not a
 * rule of the document, so the SDK checks it itself. A value of an unexpected
 * type is reported with `TYPCAST-API-0001` and the phase `api`.
 *
 * The module is shared by the builder and by the emitter, so that both report
 * the same diagnostic for the same value. The Python SDK applies the same
 * rules in `src/typcast/api.py`.
 */

import { CODE_INVALID_ARGUMENT, throwApi } from "./diagnostics.js";

/** Raises a public API error for a value of an unexpected type. */
export function rejectApiArgument(path: string, expected: string): never {
  throwApi(
    CODE_INVALID_ARGUMENT,
    `'${path}' must be ${expected}.`,
    path,
    { expected },
  );
}

/** Returns a string argument after checking its type. */
export function requireApiString(value: unknown, path: string): string {
  if (typeof value !== "string") {
    rejectApiArgument(path, "a string");
  }
  return value;
}

/**
 * Returns a numeric argument after checking its type.
 *
 * A boolean is not a number of the IR, so it is rejected here.
 */
export function requireApiNumber(value: unknown, path: string): number {
  if (typeof value !== "number") {
    rejectApiArgument(path, "a number");
  }
  return value;
}

/** Returns a model argument after checking its type. */
export function requireApiInstance<T>(
  value: unknown,
  expected: abstract new (...args: never[]) => T,
  path: string,
  name: string,
): T {
  if (!(value instanceof expected)) {
    rejectApiArgument(path, `a ${name}`);
  }
  return value;
}

/**
 * Returns an array argument after checking its type.
 *
 * A string is an array of characters and not an array of elements, so it is
 * rejected here, exactly as the model rejects it.
 */
export function requireApiArray(
  value: unknown,
  path: string,
  expected: string,
): readonly unknown[] {
  if (!Array.isArray(value)) {
    rejectApiArgument(path, expected);
  }
  return value;
}

/**
 * Returns an options object after checking its type.
 *
 * An options argument is a container that the builder reads its fields from,
 * so the check runs before the builder reads a field of it. A missing value,
 * a null value, a primitive, an array, and a function are not options
 * objects. The check names no prototype and no class, because the contract
 * requires an options object and nothing more.
 */
export function requireApiOptions<T extends object>(
  value: unknown,
  path: string,
  expected: string,
): T {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    rejectApiArgument(path, expected);
  }
  return value as T;
}
