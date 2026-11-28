/**
 * The span helpers and the table helpers of the builder.
 *
 * The helpers produce the model spans of the document IR. A string that is
 * passed as content is normalized to a `Text` span, and a span is kept as it
 * is. Two strings are never merged, because a merge would change the
 * structure of the content.
 */

import { requireApiString } from "../api.js";
import {
  normalizeContent,
  normalizeSpans,
} from "./content.js";
import type { Content } from "./content.js";
import { freezeArray } from "../models/base.js";
import { TableColumn } from "../models/blocks.js";
import type { Alignment } from "../models/blocks.js";
import {
  Bold,
  Italic,
  LineBreak,
  Link,
  Monospace,
  RawSpan,
  Text,
} from "../models/spans.js";
import type { RawFormat, Span } from "../models/spans.js";

/** Returns a text span. */
export function text(value: string): Text {
  return new Text(requireApiString(value, "/value"));
}

/** Returns a bold span that holds the content. */
export function bold(...content: Content[]): Bold {
  return new Bold(normalizeSpans(content, "/content"));
}

/** Returns an italic span that holds the content. */
export function italic(...content: Content[]): Italic {
  return new Italic(normalizeSpans(content, "/content"));
}

/** Returns a monospace span that holds the content. */
export function monospace(...content: Content[]): Monospace {
  return new Monospace(normalizeSpans(content, "/content"));
}

/** Returns a link span with a target and display content. */
export function link(href: string, ...content: Content[]): Link {
  return new Link(
    requireApiString(href, "/href"),
    normalizeSpans(content, "/content"),
  );
}

/** Returns a line break span. */
export function lineBreak(): LineBreak {
  return new LineBreak();
}

/** Returns a verbatim inline span. */
export function rawInline(value: string, format: RawFormat): RawSpan {
  return new RawSpan(
    requireApiString(format, "/format") as RawFormat,
    requireApiString(value, "/value"),
  );
}

/**
 * Returns a table column with a header and an alignment.
 *
 * The header is content, so a string becomes a text span.
 */
export function column(
  header: Content | readonly Content[],
  align: Alignment = "left",
): TableColumn {
  return new TableColumn(
    normalizeContent(header, "/header"),
    requireApiString(align, "/align") as Alignment,
  );
}

/**
 * Returns a table cell that holds the content.
 *
 * A cell of the IR is an array of spans, so the helper returns that array.
 */
export function cell(...content: Content[]): readonly Span[] {
  return freezeArray(normalizeSpans(content, "/content"));
}
