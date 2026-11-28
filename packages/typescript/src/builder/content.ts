/**
 * The checks and the normalization of the content of the builder.
 *
 * A content argument of the builder is a string or a span. A string becomes a
 * `Text` span, and a span is kept as it is. Two strings are never merged,
 * because a merge would change the structure of the content.
 *
 * The checks of the arguments of the public API live in `src/api.ts`,
 * because the emitter uses them too. The rules of a node, such as the range
 * of a heading level, the emptiness of a content, and the syntax of a module
 * alias, stay with the constructors of the model.
 */

import { rejectApiArgument } from "../api.js";
import { SpanBase, Text } from "../models/spans.js";
import type { Span } from "../models/spans.js";

/** A value that the builder accepts as content. */
export type Content = string | Span;

/** A value that the builder accepts as the content of a cell or an item. */
export type ContentGroup = Content | readonly Content[];

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
