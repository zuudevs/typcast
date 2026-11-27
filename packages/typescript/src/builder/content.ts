/**
 * The checks and the normalization of the content of the builder.
 *
 * A content argument of the builder is a string or a span. A string becomes a
 * `Text` span, and a span is kept as it is. Two strings are never merged,
 * because a merge would change the structure of the content.
 *
 * The checks of this module report a misuse of the public API with
 * `TYPCAST-API-0001`. The rules of a node, such as the range of a heading
 * level, the emptiness of a content, and the syntax of a module alias, stay
 * with the constructors of the model.
 */

import { CODE_INVALID_ARGUMENT, throwApi } from "../diagnostics.js";
import { SpanBase, Text } from "../models/spans.js";
import type { Span } from "../models/spans.js";

/** A value that the builder accepts as content. */
export type Content = string | Span;

/** A value that the builder accepts as the content of a cell or an item. */
export type ContentGroup = Content | readonly Content[];

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

/** Returns the span of a content value. */
export function normalizeSpan(value: unknown, path: string): Span {
  if (typeof value === "string") {
    return new Text(value);
  }
  if (value instanceof SpanBase) {
    return value as Span;
  }
  rejectApiArgument(path, "a string or a Span");
}

/** Returns the spans of a content collection. */
export function normalizeSpans(
  values: readonly unknown[],
  path: string,
): readonly Span[] {
  return values.map((value, index) => normalizeSpan(value, `${path}/${index}`));
}

/**
 * Returns the spans of a content value that may hold more than one span.
 *
 * A string becomes one text span, a span becomes one span, and an array
 * holds the spans of its elements.
 */
export function normalizeContent(
  value: unknown,
  path: string,
): readonly Span[] {
  if (typeof value === "string") {
    return [new Text(value)];
  }
  if (value instanceof SpanBase) {
    return [value as Span];
  }
  if (!Array.isArray(value)) {
    rejectApiArgument(
      path,
      "a string, a Span, or an array of strings and Spans",
    );
  }
  return normalizeSpans(value, path);
}
