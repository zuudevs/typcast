/**
 * The fluent builder of a document.
 *
 * The builder collects the state of a document and turns it into an
 * immutable model at `build()`. The builder is mutable, one builder produces
 * one document at a time, and a builder must not be shared across threads.
 * `build()` returns an immutable snapshot, and a later call of the builder
 * does not change a document that was already built.
 */

import {
  normalizeContent,
  normalizeSpans,
  rejectApiArgument,
  requireApiArray,
  requireApiInstance,
  requireApiNumber,
  requireApiOptions,
  requireApiString,
} from "./content.js";
import type { Content, ContentGroup } from "./content.js";
import {
  CODE_REQUIRED_FIELD,
  SEVERITY_ERROR,
  ValidationError,
  throwValidation,
  withPath,
} from "../diagnostics.js";
import type { Diagnostic } from "../diagnostics.js";
import {
  Heading,
  Image,
  ListBlock,
  PageBreak,
  Paragraph,
  RawBlock,
  Table,
  TableColumn,
} from "../models/blocks.js";
import type { Block } from "../models/blocks.js";
import { Document } from "../models/document.js";
import { Metadata } from "../models/metadata.js";
import { Module } from "../models/module.js";
import { Length, Margin, Page } from "../models/page.js";
import type { Orientation } from "../models/page.js";
import type { RawFormat, Span } from "../models/spans.js";

/** The page of a document. */
export interface PageOptions {
  readonly paper?: string;
  readonly orientation?: Orientation;
  readonly margin?: Length | Margin;
}

/** The image of a document. */
export interface ImageOptions {
  readonly alt: string;
  readonly caption?: Content | readonly Content[];
  readonly width?: Length;
}

/** The table of a document. */
export interface TableOptions {
  readonly columns: readonly TableColumn[];
  readonly rows: readonly (readonly ContentGroup[])[];
}

/** The module declaration of a document. */
export interface ModuleOptions {
  readonly alias?: string;
  readonly items?: readonly string[];
}

// The defaults of the builder. The node catalog names them, and the builder
// applies them before the immutable model is created.
const DEFAULT_PAPER = "a4";
const DEFAULT_ORIENTATION: Orientation = "portrait";
const DEFAULT_MARGIN_CM = 2.5;

/** Returns the default margin of a page. */
function defaultMargin(): Margin {
  const length = Length.cm(DEFAULT_MARGIN_CM);
  return new Margin(length, length, length, length);
}

/**
 * Builds a model and prefixes the paths of its diagnostics.
 *
 * The constructors of the model name the fields of their own model, so the
 * path of a diagnostic points at the field of the model. The builder knows
 * where the model belongs in the document, so it prefixes the path with the
 * place of the model.
 */
function construct<T>(factory: () => T, prefix: string): T {
  try {
    return factory();
  } catch (error) {
    if (error instanceof ValidationError) {
      throw new ValidationError(
        error.message,
        withPath(error.diagnostics, prefix),
      );
    }
    throw error;
  }
}

/**
 * Returns the margin of a page.
 *
 * A single length is the margin of every side of the page, and a margin
 * names every side itself.
 */
function marginOf(
  margin: Length | Margin | undefined,
  path: string,
): Margin {
  if (margin === undefined) {
    return defaultMargin();
  }
  if (margin instanceof Length) {
    return new Margin(margin, margin, margin, margin);
  }
  if (margin instanceof Margin) {
    return margin;
  }
  rejectApiArgument(path, "a Length or a Margin");
}

/** The fluent builder of a document. */
export class DocumentBuilder {
  private titleValue: string | null = null;
  private authorValue: string | null = null;
  private dateValue: string | null = null;
  private paperValue: string = DEFAULT_PAPER;
  private orientationValue: Orientation = DEFAULT_ORIENTATION;
  private marginValue: Margin = defaultMargin();
  private readonly contents: Block[] = [];
  private readonly modules: Module[] = [];

  /** Sets the title of the document. */
  title(value: string): this {
    this.titleValue = requireApiString(value, "/metadata/title");
    return this;
  }

  /** Sets the author of the document. */
  author(value: string): this {
    this.authorValue = requireApiString(value, "/metadata/author");
    return this;
  }

  /** Sets the date of the document. */
  date(value: string): this {
    this.dateValue = requireApiString(value, "/metadata/date");
    return this;
  }

  /**
   * Sets the page of the document.
   *
   * A single length is the margin of every side of the page. A margin names
   * every side itself. The default is a margin of 2.5 centimeters on every
   * side.
   *
   * The method reads no field of the options before it checks the options
   * themselves, and it changes no state of the builder before every value of
   * the options is known to be valid.
   */
  page(options: PageOptions = {}): this {
    const values = requireApiOptions<PageOptions>(
      options,
      "/page",
      "a PageOptions object",
    );
    const paper = requireApiString(values.paper ?? DEFAULT_PAPER, "/page/paper");
    const orientation = requireApiString(
      values.orientation ?? DEFAULT_ORIENTATION,
      "/page/orientation",
    ) as Orientation;
    const margin = marginOf(values.margin, "/page/margin");
    this.paperValue = paper;
    this.orientationValue = orientation;
    this.marginValue = margin;
    return this;
  }

  /** Adds a heading with a level from 1 to 6. */
  heading(level: number, ...content: Content[]): this {
    const path = `/contents/${this.contents.length}`;
    const value = requireApiNumber(level, `${path}/level`);
    const spans = normalizeSpans(content, `${path}/content`);
    this.contents.push(construct(() => new Heading(value, spans), path));
    return this;
  }

  /** Adds a paragraph that holds the content. */
  paragraph(...content: Content[]): this {
    const path = `/contents/${this.contents.length}`;
    const spans = normalizeSpans(content, `${path}/content`);
    this.contents.push(construct(() => new Paragraph(spans), path));
    return this;
  }

  /** Adds an unordered list of items. */
  bulletList(items: readonly ContentGroup[]): this {
    return this.list(items, false);
  }

  /** Adds an ordered list of items. */
  numberedList(items: readonly ContentGroup[]): this {
    return this.list(items, true);
  }

  /** Adds a list of items. */
  private list(items: readonly ContentGroup[], ordered: boolean): this {
    const path = `/contents/${this.contents.length}`;
    const values = requireApiArray(
      items,
      `${path}/items`,
      "an array of content values",
    );
    const entries = values.map((item, index) =>
      normalizeContent(item, `${path}/items/${index}`),
    );
    this.contents.push(
      construct(() => new ListBlock(ordered, entries), path),
    );
    return this;
  }

  /**
   * Adds a table with columns and rows.
   *
   * A row is an array of cells, and a cell is an array of content. The
   * number of the cells of a row must match the number of the columns, and
   * the validation engine reports the row that breaks the rule.
   */
  table(options: TableOptions): this {
    const path = `/contents/${this.contents.length}`;
    const values = requireApiOptions<TableOptions>(
      options,
      path,
      "a TableOptions object",
    );
    const columnValues = requireApiArray(
      values.columns,
      `${path}/columns`,
      "an array of TableColumn values",
    );
    columnValues.forEach((value, index) => {
      requireApiInstance(
        value,
        TableColumn,
        `${path}/columns/${index}`,
        "TableColumn",
      );
    });
    const rowValues = requireApiArray(
      values.rows,
      `${path}/rows`,
      "an array of rows",
    );
    const tableRows = rowValues.map((row, index) => this.row(row, `${path}/rows/${index}`));
    this.contents.push(
      construct(
        () =>
          new Table(
            columnValues as readonly TableColumn[],
            tableRows,
          ),
        path,
      ),
    );
    return this;
  }

  /** Returns the cells of a row of a table. */
  private row(row: unknown, path: string): readonly (readonly Span[])[] {
    const cells = requireApiArray(row, path, "an array of cells");
    return cells.map((cell, index) =>
      normalizeContent(cell, `${path}/${index}`),
    );
  }

  /**
   * Adds an image with an alternative text.
   *
   * The caption is optional, and it is content, so a string becomes a text
   * span. The width is optional, and the compiler determines it when the
   * document holds no width.
   */
  image(path: string, options: ImageOptions): this {
    const location = `/contents/${this.contents.length}`;
    const imagePath = requireApiString(path, `${location}/path`);
    const values = requireApiOptions<ImageOptions>(
      options,
      location,
      "an ImageOptions object",
    );
    const imageAlt = requireApiString(values.alt, `${location}/alt`);
    const caption =
      values.caption === undefined
        ? null
        : normalizeContent(values.caption, `${location}/caption`);
    const width =
      values.width === undefined
        ? null
        : requireApiInstance(
            values.width,
            Length,
            `${location}/width`,
            "Length",
          );
    this.contents.push(
      construct(
        () => new Image(imagePath, imageAlt, caption, width),
        location,
      ),
    );
    return this;
  }

  /** Adds an explicit page break. */
  pageBreak(): this {
    this.contents.push(new PageBreak());
    return this;
  }

  /**
   * Adds a verbatim Typst block.
   *
   * The format is `markup`, `code`, or `math`. The raw content is opaque to
   * Typcast, and the validation engine limits its size.
   */
  raw(value: string, options: { readonly format?: RawFormat } = {}): this {
    const path = `/contents/${this.contents.length}`;
    const rawValue = requireApiString(value, `${path}/value`);
    const values = requireApiOptions<{ readonly format?: RawFormat }>(
      options,
      path,
      "an object with an optional 'format' property",
    );
    const rawFormat = requireApiString(
      values.format ?? "markup",
      `${path}/format`,
    );
    this.contents.push(
      construct(() => new RawBlock(rawFormat as RawFormat, rawValue), path),
    );
    return this;
  }

  /**
   * Adds a module import declaration.
   *
   * The declaration keeps the order of the calls. The alias and the items
   * must not both be set, and the alias must be unique in the document. The
   * builder resolves no file and checks no path.
   */
  module(path: string, options: ModuleOptions = {}): this {
    const location = `/modules/${this.modules.length}`;
    const modulePath = requireApiString(path, `${location}/path`);
    const values = requireApiOptions<ModuleOptions>(
      options,
      location,
      "a ModuleOptions object",
    );
    const alias =
      values.alias === undefined
        ? null
        : requireApiString(values.alias, `${location}/alias`);
    const items = this.items(values.items, `${location}/items`);
    this.modules.push(
      construct(() => new Module(modulePath, alias, items), location),
    );
    return this;
  }

  /** Returns the items of a module declaration. */
  private items(
    items: readonly string[] | undefined,
    path: string,
  ): readonly string[] | null {
    if (items === undefined) {
      return null;
    }
    const values = requireApiArray(items, path, "an array of strings");
    return values.map((item, index) =>
      requireApiString(item, `${path}/${index}`),
    );
  }

  /**
   * Returns the immutable document of the current state of the builder.
   *
   * The method runs the semantic validation engine, and it throws a
   * validation error when the engine reports an error. The diagnostics of
   * the error hold every problem of the document, in the order of the
   * document.
   */
  build(): Document {
    if (this.titleValue === null) {
      throwValidation(
        CODE_REQUIRED_FIELD,
        "'/metadata/title' is required.",
        "/metadata/title",
        { field: "title" },
      );
    }
    const document = construct(
      () =>
        new Document(
          construct(
            () =>
              new Metadata(this.titleValue as string, this.authorValue, this.dateValue),
            "/metadata",
          ),
          construct(
            () =>
              new Page(
                this.paperValue,
                this.orientationValue,
                this.marginValue,
              ),
            "/page",
          ),
          [...this.contents],
          [...this.modules],
        ),
      "",
    );
    const diagnostics = document.validate();
    const errors = diagnostics.filter(
      (diagnostic) => diagnostic.severity === SEVERITY_ERROR,
    );
    const [first, ...rest] = errors;
    if (first !== undefined) {
      const all: readonly Diagnostic[] = [first, ...rest];
      throw new ValidationError(first.message, all);
    }
    return document;
  }
}
