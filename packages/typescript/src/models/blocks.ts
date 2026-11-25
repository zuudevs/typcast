/**
 * Blocks of the document IR.
 *
 * Every block is immutable. The constructors copy the collections they
 * receive, so a later mutation of a caller-owned array cannot change a
 * block.
 */

import {
  CODE_INVALID_HEADING_LEVEL,
  CODE_INVALID_LENGTH,
  throwValidation,
} from "../diagnostics.js";
import {
  freezeArray,
  requireArray,
  requireBoolean,
  requireEnum,
  requireInstance,
  requireInteger,
  requireString,
} from "./base.js";
import { Length } from "./page.js";
import { RAW_FORMATS, requireSpans, toJSONArray } from "./spans.js";
import type { RawFormat, Span } from "./spans.js";

/** The alignments of a table column. */
export const ALIGNMENTS = ["left", "center", "right"] as const;

/** The alignment of a table column. */
export type Alignment = (typeof ALIGNMENTS)[number];

/** The base class of every block. */
export abstract class BlockBase {
  /** The discriminator of the block. */
  abstract readonly type: string;

  /** Returns the JSON value of the block. */
  abstract toJSON(): Record<string, unknown>;
}

/** A section heading with a level from 1 to 6. */
export class Heading extends BlockBase {
  readonly type: "heading" = "heading";
  readonly level: number;
  readonly content: readonly Span[];

  constructor(level: number, content: readonly Span[]) {
    super();
    const checked = requireInteger(level, "/level");
    if (checked < 1 || checked > 6) {
      throwValidation(
        CODE_INVALID_HEADING_LEVEL,
        `'/level' must be between 1 and 6, got ${checked}.`,
        "/level",
        { value: checked },
      );
    }
    this.level = checked;
    this.content = requireSpans(content, "/content", false);
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return {
      type: this.type,
      level: this.level,
      content: toJSONArray(this.content),
    };
  }
}

/** A paragraph that contains inline spans. */
export class Paragraph extends BlockBase {
  readonly type: "paragraph" = "paragraph";
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

/** An ordered or unordered list of inline span arrays. */
export class ListBlock extends BlockBase {
  readonly type: "list" = "list";
  readonly ordered: boolean;
  readonly items: readonly (readonly Span[])[];

  constructor(ordered: boolean, items: readonly (readonly Span[])[]) {
    super();
    this.ordered = requireBoolean(ordered, "/ordered");
    const entries = requireArray(items, "/items", false);
    this.items = freezeArray(
      entries.map((item, index) => requireSpans(item, `/items/${index}`, false)),
    );
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return {
      type: this.type,
      ordered: this.ordered,
      items: this.items.map((item) => toJSONArray(item)),
    };
  }
}

/** A table column with a header and an alignment. */
export class TableColumn {
  readonly header: readonly Span[];
  readonly align: Alignment;

  constructor(header: readonly Span[], align: Alignment) {
    this.header = requireSpans(header, "/header");
    this.align = requireEnum(align, ALIGNMENTS, "/align");
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { header: toJSONArray(this.header), align: this.align };
  }
}

/**
 * A table with columns, header cells, and rows.
 *
 * The number of cells of a row must match the number of columns. That rule
 * belongs to the document validation layer and is not checked here.
 */
export class Table extends BlockBase {
  readonly type: "table" = "table";
  readonly columns: readonly TableColumn[];
  readonly rows: readonly (readonly (readonly Span[])[])[];

  constructor(
    columns: readonly TableColumn[],
    rows: readonly (readonly (readonly Span[])[])[],
  ) {
    super();
    const columnItems = requireArray(columns, "/columns", false);
    this.columns = freezeArray(
      columnItems.map((item, index) =>
        requireInstance(item, TableColumn, `/columns/${index}`),
      ),
    );
    const rowItems = requireArray(rows, "/rows", false);
    this.rows = freezeArray(
      rowItems.map((row, rowIndex) => {
        const cells = requireArray(row, `/rows/${rowIndex}`);
        return freezeArray(
          cells.map((cell, cellIndex) =>
            requireSpans(cell, `/rows/${rowIndex}/${cellIndex}`),
          ),
        );
      }),
    );
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return {
      type: this.type,
      columns: this.columns.map((column) => column.toJSON()),
      rows: this.rows.map((row) => row.map((cell) => toJSONArray(cell))),
    };
  }
}

/** An image with alternative text and an optional caption. */
export class Image extends BlockBase {
  readonly type: "image" = "image";
  readonly path: string;
  readonly alt: string;
  readonly caption: readonly Span[] | null;
  readonly width: Length | null;

  constructor(
    path: string,
    alt: string,
    caption: readonly Span[] | null = null,
    width: Length | null = null,
  ) {
    super();
    this.path = requireString(path, "/path");
    this.alt = requireString(alt, "/alt");
    this.caption = caption === null ? null : requireSpans(caption, "/caption", false);
    this.width = width === null ? null : requireInstance(width, Length, "/width");
    // The IR requires the width of an image to be a positive length, while a
    // length of a margin may be zero.
    if (this.width !== null && !(this.width.value > 0)) {
      throwValidation(
        CODE_INVALID_LENGTH,
        `'/width/value' must be greater than zero, got ${this.width.value}.`,
        "/width/value",
        { value: this.width.value },
      );
    }
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    const value: Record<string, unknown> = {
      type: this.type,
      path: this.path,
      alt: this.alt,
    };
    if (this.caption !== null) {
      value["caption"] = toJSONArray(this.caption);
    }
    if (this.width !== null) {
      value["width"] = this.width.toJSON();
    }
    return value;
  }
}

/** An explicit page break. */
export class PageBreak extends BlockBase {
  readonly type: "pageBreak" = "pageBreak";

  constructor() {
    super();
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    return { type: this.type };
  }
}

/** Verbatim Typst markup, code, or math. */
export class RawBlock extends BlockBase {
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

/** Every block of the IR. */
export type Block =
  | Heading
  | Paragraph
  | ListBlock
  | Table
  | Image
  | PageBreak
  | RawBlock;

/** Returns the JSON values of a block collection. */
export function toJSONBlockArray(
  blocks: readonly Block[],
): Record<string, unknown>[] {
  return blocks.map((block) => block.toJSON());
}

/** Returns a frozen copy of a block collection after checking its elements. */
export function requireBlocks(
  value: unknown,
  path: string,
  allowEmpty = true,
): readonly Block[] {
  const items = requireArray(value, path, allowEmpty);
  const blocks = items.map((item, index) =>
    requireInstance(item, BlockBase, `${path}/${index}`),
  );
  return freezeArray(blocks as readonly Block[]);
}
