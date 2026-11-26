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
  CODE_STRING_TOO_LONG,
  safeText,
  safeValue,
  throwValidation,
} from "../diagnostics.js";

/** Returns the article that a name of a type needs. */
function article(name: string): string {
  return "aeiou".includes(name.slice(0, 1).toLowerCase()) ? "an" : "a";
}

/**
 * Returns the name of the elements of a collection, in the plural.
 *
 * The Python SDK applies the same rule, so that the message of a diagnostic
 * is the same in both SDKs.
 */
function elementPlural(name: string): string {
  if (name === "array") {
    return "arrays";
  }
  if (name.startsWith("array of ")) {
    return `arrays of ${name.slice("array of ".length)}`;
  }
  return `${name} values`;
}

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

/**
 * Returns a string argument after checking its type and its length.
 *
 * The length is counted in Unicode code points, as the contract counts it.
 * A JavaScript string counts UTF-16 code units, so a character outside the
 * basic multilingual plane counts twice here and once in the Python SDK.
 */
export function requireBoundedString(
  value: unknown,
  path: string,
  maxLength: number,
  allowEmpty = false,
): string {
  const text = requireString(value, path, allowEmpty);
  const length = [...text].length;
  if (length > maxLength) {
    throwValidation(
      CODE_STRING_TOO_LONG,
      `'${path}' must not hold more than ${maxLength} code points.`,
      path,
      { maxLength, length },
    );
  }
  return text;
}

/** Returns an enum argument after checking that it is a known literal. */
export function requireEnum<T extends string>(
  value: unknown,
  allowed: readonly T[],
  path: string,
): T {
  const names = [...allowed].sort();
  if (typeof value !== "string") {
    throwValidation(
      CODE_INVALID_ENUM,
      `'${path}' must be one of ${names.join(", ")}.`,
      path,
      { allowed: names },
    );
  }
  if (!allowed.includes(value as T)) {
    // The rejected value is shown in a bounded form, so that the message of
    // the diagnostic stays readable. The Python SDK applies the same rule.
    throwValidation(
      CODE_INVALID_ENUM,
      `'${path}' must be one of ${names.join(", ")}, got '${safeText(value)}'.`,
      path,
      { allowed: names, value: safeValue(value) },
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

/**
 * Returns a model argument after checking its type.
 *
 * The name of the expected type is the name of the class, unless the caller
 * names another one. The Python SDK applies the same rule.
 */
export function requireInstance<T>(
  value: unknown,
  expected: abstract new (...args: never[]) => T,
  path: string,
  name?: string,
): T {
  const label = name ?? expected.name;
  if (!(value instanceof expected)) {
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${path}' must be ${article(label)} ${label}.`,
      path,
      { expected: label },
    );
  }
  return value;
}

/**
 * Returns a copied array after checking that the value is an array.
 *
 * The name of the elements of the array is the name of the type of the
 * elements, unless the caller names another one. The Python SDK applies the
 * same rule.
 */
export function requireArray(
  value: unknown,
  path: string,
  allowEmpty = true,
  elementName?: string,
): readonly unknown[] {
  if (!Array.isArray(value)) {
    const plural =
      elementName === undefined ? "" : ` of ${elementPlural(elementName)}`;
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${path}' must be an array${plural}.`,
      path,
      // The details of a diagnostic must be JSON-serializable, and the
      // Python SDK reports the same failure with the same details.
      elementName === undefined ? {} : { expected: elementName },
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
