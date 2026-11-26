/**
 * Inline spans of the document IR.
 *
 * Every span is immutable. The constructors copy the collections they
 * receive, so a later mutation of a caller-owned array cannot change a span.
 */

import {
  freezeArray,
  requireArray,
  requireEnum,
  requireInstance,
  requireString,
} from "./base.js";

/** The raw formats of the IR. */
export const RAW_FORMATS = ["markup", "code", "math"] as const;

/** The format of a raw block or a raw span. */
export type RawFormat = (typeof RAW_FORMATS)[number];

/** The base class of every inline span. */
export abstract class SpanBase {
  /** The discriminator of the span. */
  abstract readonly type: string;

  /** Returns the JSON value of the span. */
  abstract toJSON(): Record<string, unknown>;
}

/** A plain text span. */
export class Text extends SpanBase {
  readonly type: "text" = "text";
  readonly value: string;

  constructor(value: string) {
    super();
    this.value = requireString(value, "/value");
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { type: this.type, value: this.value };
  }
}

/** A bold span. */
export class Bold extends SpanBase {
  readonly type: "bold" = "bold";
  readonly content: readonly Span[];

  constructor(content: readonly Span[]) {
    super();
    this.content = requireSpans(content, "/content", false);
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { type: this.type, content: toJSONArray(this.content) };
  }
}

/** An italic span. */
export class Italic extends SpanBase {
  readonly type: "italic" = "italic";
  readonly content: readonly Span[];

  constructor(content: readonly Span[]) {
    super();
    this.content = requireSpans(content, "/content", false);
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { type: this.type, content: toJSONArray(this.content) };
  }
}

/** A monospace span. */
export class Monospace extends SpanBase {
  readonly type: "monospace" = "monospace";
  readonly content: readonly Span[];

  constructor(content: readonly Span[]) {
    super();
    this.content = requireSpans(content, "/content", false);
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { type: this.type, content: toJSONArray(this.content) };
  }
}

/** A link span with display text and a target. */
export class Link extends SpanBase {
  readonly type: "link" = "link";
  readonly href: string;
  readonly content: readonly Span[];

  constructor(href: string, content: readonly Span[]) {
    super();
    this.href = requireString(href, "/href");
    this.content = requireSpans(content, "/content", false);
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return {
      type: this.type,
      href: this.href,
      content: toJSONArray(this.content),
    };
  }
}

/** An explicit line break. */
export class LineBreak extends SpanBase {
  readonly type: "lineBreak" = "lineBreak";

  constructor() {
    super();
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { type: this.type };
  }
}

/** A verbatim inline Typst span. */
export class RawSpan extends SpanBase {
  readonly type: "raw" = "raw";
  readonly format: RawFormat;
  readonly value: string;

  constructor(format: RawFormat, value: string) {
    super();
    this.format = requireEnum(format, RAW_FORMATS, "/format");
    this.value = requireString(value, "/value");
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { type: this.type, format: this.format, value: this.value };
  }
}

/** Every inline span of the IR. */
export type Span =
  | Text
  | Bold
  | Italic
  | Monospace
  | Link
  | LineBreak
  | RawSpan;

/** Returns the JSON values of a span collection. */
export function toJSONArray(spans: readonly Span[]): Record<string, unknown>[] {
  return spans.map((span) => span.toJSON());
}

/** Returns a frozen copy of a span collection after checking its elements. */
export function requireSpans(
  value: unknown,
  path: string,
  allowEmpty = true,
): readonly Span[] {
  const items = requireArray(value, path, allowEmpty, "Span");
  const spans = items.map((item, index) =>
    requireInstance(item, SpanBase, `${path}/${index}`, "Span"),
  );
  return freezeArray(spans as readonly Span[]);
}
