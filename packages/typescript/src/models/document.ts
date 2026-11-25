/**
 * The root document of the document IR and its JSON reader.
 *
 * The module holds the document class and the reader that builds a document
 * from a JSON value. Keeping them together avoids an import cycle: the class
 * needs the reader for its factory methods, and the reader needs the class to
 * build the result.
 */

import {
  CODE_INVALID_ENUM,
  CODE_MALFORMED_JSON,
  CODE_NOT_SERIALIZABLE,
  CODE_REQUIRED_FIELD,
  CODE_ROOT_SHAPE,
  CODE_UNKNOWN_FIELD,
  ValidationError,
  throwSerialization,
  throwValidation,
  withPath,
} from "../diagnostics.js";
import { assertEncodable, canonicalJson } from "../json_writer.js";
import { checkSchemaVersion, SCHEMA_VERSION } from "../version.js";
import { requireInstance } from "./base.js";
import {
  Heading,
  Image,
  ListBlock,
  PageBreak,
  Paragraph,
  RawBlock,
  Table,
  TableColumn,
  requireBlocks,
} from "./blocks.js";
import type { Block } from "./blocks.js";
import { Metadata } from "./metadata.js";
import { Module, requireModules } from "./module.js";
import { Length, Margin, Page } from "./page.js";
import {
  Bold,
  Italic,
  LineBreak,
  Link,
  Monospace,
  RawSpan,
  Text,
} from "./spans.js";
import type { RawFormat, Span } from "./spans.js";

const MISSING = Symbol("missing");

const SPAN_FIELDS: Readonly<Record<string, readonly string[]>> = {
  text: ["type", "value"],
  bold: ["type", "content"],
  italic: ["type", "content"],
  monospace: ["type", "content"],
  link: ["type", "href", "content"],
  lineBreak: ["type"],
  raw: ["type", "format", "value"],
};

const BLOCK_FIELDS: Readonly<Record<string, readonly string[]>> = {
  heading: ["type", "level", "content"],
  paragraph: ["type", "content"],
  list: ["type", "ordered", "items"],
  table: ["type", "columns", "rows"],
  image: ["type", "path", "alt", "caption", "width"],
  pageBreak: ["type"],
  raw: ["type", "format", "value"],
};

/** The immutable root of a Typcast document. */
export class Document {
  readonly metadata: Metadata;
  readonly page: Page;
  readonly contents: readonly Block[];
  readonly modules: readonly Module[];
  readonly schemaVersion: string;

  constructor(
    metadata: Metadata,
    page: Page,
    contents: readonly Block[],
    modules: readonly Module[] = [],
    schemaVersion: string = SCHEMA_VERSION,
  ) {
    this.metadata = requireInstance(metadata, Metadata, "/metadata");
    this.page = requireInstance(page, Page, "/page");
    this.contents = requireBlocks(contents, "/contents", false);
    this.modules = requireModules(modules, "/modules");
    this.schemaVersion = schemaVersion;
    checkSchemaVersion(schemaVersion);
    Object.freeze(this);
  }

  /** Returns the JSON value of the document. */
  toJSON(): Record<string, unknown> {
    return {
      schemaVersion: this.schemaVersion,
      metadata: this.metadata.toJSON(),
      page: this.page.toJSON(),
      contents: this.contents.map((block) => block.toJSON()),
      modules: this.modules.map((module) => module.toJSON()),
    };
  }

  /** Returns the canonical JSON text of the document. */
  toJSONString(): string {
    const value = this.toJSON();
    assertEncodable(value, "");
    return canonicalJson(value) + "\n";
  }

  /** Builds a document from a JSON value. */
  static fromJSON(value: unknown): Document {
    return documentFromJSON(value);
  }

  /** Builds a document from JSON text. */
  static fromJSONString(source: string): Document {
    return documentFromJSONString(source);
  }
}

/** Returns the JSON value of a document. */
export function documentToJSON(document: Document): Record<string, unknown> {
  if (!(document instanceof Document)) {
    throwSerialization(CODE_NOT_SERIALIZABLE, "The value is not a document.");
  }
  return document.toJSON();
}

/** Returns the canonical JSON text of a document. */
export function documentToJSONString(document: Document): string {
  const value = documentToJSON(document);
  assertEncodable(value, "");
  return canonicalJson(value) + "\n";
}

/** Builds a document from a JSON value. */
export function documentFromJSON(value: unknown): Document {
  const root = asObject(value, "");
  checkFields(
    root,
    ["schemaVersion", "metadata", "page", "contents", "modules"],
    "",
  );
  const schemaVersion = asString(
    requireField(root, "schemaVersion", ""),
    "/schemaVersion",
  );
  checkSchemaVersion(schemaVersion);
  const metadata = parseMetadata(requireField(root, "metadata", ""), "/metadata");
  const page = parsePage(requireField(root, "page", ""), "/page");
  const contents = parseBlocks(requireField(root, "contents", ""), "/contents");
  const modules = parseModules(
    optionalField(root, "modules") === MISSING ? [] : root["modules"],
    "/modules",
  );
  return new Document(metadata, page, contents, modules, schemaVersion);
}

/** Builds a document from JSON text. */
export function documentFromJSONString(source: string): Document {
  if (typeof source !== "string") {
    throwSerialization(
      CODE_MALFORMED_JSON,
      "The source must be a JSON string.",
    );
  }
  let value: unknown;
  try {
    value = JSON.parse(source);
  } catch (error) {
    throwSerialization(
      CODE_MALFORMED_JSON,
      `The source is not valid JSON: ${(error as Error).message}.`,
    );
  }
  return documentFromJSON(value);
}

function asObject(value: unknown, path: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throwSerialization(
      CODE_ROOT_SHAPE,
      `'${path === "" ? "/" : path}' must be a JSON object.`,
      path === "" ? null : path,
    );
  }
  return value as Record<string, unknown>;
}

function asArray(value: unknown, path: string): unknown[] {
  if (!Array.isArray(value)) {
    throwSerialization(
      CODE_ROOT_SHAPE,
      `'${path}' must be a JSON array.`,
      path,
    );
  }
  return value;
}

function asString(value: unknown, path: string): string {
  if (typeof value !== "string") {
    throwSerialization(
      CODE_ROOT_SHAPE,
      `'${path}' must be a JSON string.`,
      path,
    );
  }
  return value;
}

function asBoolean(value: unknown, path: string): boolean {
  if (typeof value !== "boolean") {
    throwSerialization(
      CODE_ROOT_SHAPE,
      `'${path}' must be a JSON boolean.`,
      path,
    );
  }
  return value;
}

function asInteger(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throwSerialization(
      CODE_ROOT_SHAPE,
      `'${path}' must be a JSON integer.`,
      path,
    );
  }
  return value;
}

function asNumber(value: unknown, path: string): number {
  if (typeof value !== "number" || !Number.isFinite(value)) {
    throwSerialization(
      CODE_ROOT_SHAPE,
      `'${path}' must be a JSON number.`,
      path,
    );
  }
  return value;
}

function checkFields(
  value: Record<string, unknown>,
  allowed: readonly string[],
  path: string,
): void {
  for (const name of Object.keys(value)) {
    if (!allowed.includes(name)) {
      const location = `${path}/${name}`;
      throwValidation(
        CODE_UNKNOWN_FIELD,
        `'${location}' is not a known field.`,
        location,
        { field: name },
      );
    }
  }
}

function requireField(
  value: Record<string, unknown>,
  name: string,
  path: string,
): unknown {
  if (!Object.prototype.hasOwnProperty.call(value, name)) {
    const location = `${path}/${name}`;
    throwValidation(
      CODE_REQUIRED_FIELD,
      `'${location}' is required.`,
      location,
      { field: name },
    );
  }
  return value[name];
}

function optionalField(
  value: Record<string, unknown>,
  name: string,
): unknown {
  if (!Object.prototype.hasOwnProperty.call(value, name)) {
    return MISSING;
  }
  return value[name];
}

function construct<T>(factory: () => T, path: string): T {
  try {
    return factory();
  } catch (error) {
    if (error instanceof ValidationError) {
      throw new ValidationError(
        error.message,
        withPath(error.diagnostics, path),
      );
    }
    throw error;
  }
}

function parseMetadata(value: unknown, path: string): Metadata {
  const obj = asObject(value, path);
  checkFields(obj, ["title", "author", "date"], path);
  const title = asString(requireField(obj, "title", path), `${path}/title`);
  const author = optionalField(obj, "author");
  const date = optionalField(obj, "date");
  return construct(
    () =>
      new Metadata(
        title,
        author === MISSING ? null : asString(author, `${path}/author`),
        date === MISSING ? null : asString(date, `${path}/date`),
      ),
    path,
  );
}

function parseLength(value: unknown, path: string): Length {
  const obj = asObject(value, path);
  checkFields(obj, ["value", "unit"], path);
  const number = asNumber(requireField(obj, "value", path), `${path}/value`);
  const unit = asString(requireField(obj, "unit", path), `${path}/unit`);
  return construct(
    () => new Length(number, unit as Length["unit"]),
    path,
  );
}

function parseMargin(value: unknown, path: string): Margin {
  const obj = asObject(value, path);
  checkFields(obj, ["top", "right", "bottom", "left"], path);
  return construct(
    () =>
      new Margin(
        parseLength(requireField(obj, "top", path), `${path}/top`),
        parseLength(requireField(obj, "right", path), `${path}/right`),
        parseLength(requireField(obj, "bottom", path), `${path}/bottom`),
        parseLength(requireField(obj, "left", path), `${path}/left`),
      ),
    path,
  );
}

function parsePage(value: unknown, path: string): Page {
  const obj = asObject(value, path);
  checkFields(obj, ["paper", "orientation", "margin"], path);
  const paper = asString(requireField(obj, "paper", path), `${path}/paper`);
  const orientation = asString(
    requireField(obj, "orientation", path),
    `${path}/orientation`,
  );
  const margin = parseMargin(requireField(obj, "margin", path), `${path}/margin`);
  return construct(
    () => new Page(paper, orientation as Page["orientation"], margin),
    path,
  );
}

function parseModule(value: unknown, path: string): Module {
  const obj = asObject(value, path);
  checkFields(obj, ["path", "alias", "items"], path);
  const modulePath = asString(requireField(obj, "path", path), `${path}/path`);
  const alias = optionalField(obj, "alias");
  const items = optionalField(obj, "items");
  let parsedItems: readonly string[] | null = null;
  if (items !== MISSING) {
    const entries = asArray(items, `${path}/items`);
    parsedItems = entries.map((item, index) =>
      asString(item, `${path}/items/${index}`),
    );
  }
  return construct(
    () =>
      new Module(
        modulePath,
        alias === MISSING ? null : asString(alias, `${path}/alias`),
        parsedItems,
      ),
    path,
  );
}

function parseModules(value: unknown, path: string): readonly Module[] {
  const entries = asArray(value, path);
  return entries.map((entry, index) => parseModule(entry, `${path}/${index}`));
}

function parseSpan(value: unknown, path: string): Span {
  const obj = asObject(value, path);
  const discriminator = obj["type"];
  if (typeof discriminator !== "string" || !(discriminator in SPAN_FIELDS)) {
    throwValidation(
      CODE_INVALID_ENUM,
      `'${path}/type' must be one of ${Object.keys(SPAN_FIELDS).sort().join(", ")}.`,
      `${path}/type`,
      { allowed: Object.keys(SPAN_FIELDS).sort() },
    );
  }
  const fields = SPAN_FIELDS[discriminator] ?? [];
  checkFields(obj, fields, path);
  if (discriminator === "text") {
    const text = asString(requireField(obj, "value", path), `${path}/value`);
    return construct(() => new Text(text), path);
  }
  if (discriminator === "bold") {
    const content = parseSpans(
      requireField(obj, "content", path),
      `${path}/content`,
    );
    return construct(() => new Bold(content), path);
  }
  if (discriminator === "italic") {
    const content = parseSpans(
      requireField(obj, "content", path),
      `${path}/content`,
    );
    return construct(() => new Italic(content), path);
  }
  if (discriminator === "monospace") {
    const content = parseSpans(
      requireField(obj, "content", path),
      `${path}/content`,
    );
    return construct(() => new Monospace(content), path);
  }
  if (discriminator === "link") {
    const href = asString(requireField(obj, "href", path), `${path}/href`);
    const content = parseSpans(
      requireField(obj, "content", path),
      `${path}/content`,
    );
    return construct(() => new Link(href, content), path);
  }
  if (discriminator === "lineBreak") {
    return construct(() => new LineBreak(), path);
  }
  const format = asString(
    requireField(obj, "format", path),
    `${path}/format`,
  );
  const raw = asString(requireField(obj, "value", path), `${path}/value`);
  return construct(() => new RawSpan(format as RawFormat, raw), path);
}

function parseSpans(value: unknown, path: string): readonly Span[] {
  const entries = asArray(value, path);
  return entries.map((entry, index) => parseSpan(entry, `${path}/${index}`));
}

function parseColumn(value: unknown, path: string): TableColumn {
  const obj = asObject(value, path);
  checkFields(obj, ["header", "align"], path);
  const header = parseSpans(requireField(obj, "header", path), `${path}/header`);
  const align = asString(requireField(obj, "align", path), `${path}/align`);
  return construct(
    () => new TableColumn(header, align as TableColumn["align"]),
    path,
  );
}

function parseRow(value: unknown, path: string): readonly (readonly Span[])[] {
  const cells = asArray(value, path);
  return cells.map((cell, index) => parseSpans(cell, `${path}/${index}`));
}

function parseBlock(value: unknown, path: string): Block {
  const obj = asObject(value, path);
  const discriminator = obj["type"];
  if (typeof discriminator !== "string" || !(discriminator in BLOCK_FIELDS)) {
    throwValidation(
      CODE_INVALID_ENUM,
      `'${path}/type' must be one of ${Object.keys(BLOCK_FIELDS).sort().join(", ")}.`,
      `${path}/type`,
      { allowed: Object.keys(BLOCK_FIELDS).sort() },
    );
  }
  const fields = BLOCK_FIELDS[discriminator] ?? [];
  checkFields(obj, fields, path);
  if (discriminator === "heading") {
    const level = asInteger(
      requireField(obj, "level", path),
      `${path}/level`,
    );
    const content = parseSpans(
      requireField(obj, "content", path),
      `${path}/content`,
    );
    return construct(() => new Heading(level, content), path);
  }
  if (discriminator === "paragraph") {
    const content = parseSpans(
      requireField(obj, "content", path),
      `${path}/content`,
    );
    return construct(() => new Paragraph(content), path);
  }
  if (discriminator === "list") {
    const ordered = asBoolean(
      requireField(obj, "ordered", path),
      `${path}/ordered`,
    );
    const entries = asArray(requireField(obj, "items", path), `${path}/items`);
    const items = entries.map((entry, index) =>
      parseSpans(entry, `${path}/items/${index}`),
    );
    return construct(() => new ListBlock(ordered, items), path);
  }
  if (discriminator === "table") {
    const columnEntries = asArray(
      requireField(obj, "columns", path),
      `${path}/columns`,
    );
    const columns = columnEntries.map((entry, index) =>
      parseColumn(entry, `${path}/columns/${index}`),
    );
    const rowEntries = asArray(requireField(obj, "rows", path), `${path}/rows`);
    const rows = rowEntries.map((entry, index) =>
      parseRow(entry, `${path}/rows/${index}`),
    );
    return construct(() => new Table(columns, rows), path);
  }
  if (discriminator === "image") {
    const imagePath = asString(
      requireField(obj, "path", path),
      `${path}/path`,
    );
    const alt = asString(requireField(obj, "alt", path), `${path}/alt`);
    const caption = optionalField(obj, "caption");
    const width = optionalField(obj, "width");
    return construct(
      () =>
        new Image(
          imagePath,
          alt,
          caption === MISSING
            ? null
            : parseSpans(caption, `${path}/caption`),
          width === MISSING ? null : parseLength(width, `${path}/width`),
        ),
      path,
    );
  }
  if (discriminator === "pageBreak") {
    return construct(() => new PageBreak(), path);
  }
  const format = asString(requireField(obj, "format", path), `${path}/format`);
  const raw = asString(requireField(obj, "value", path), `${path}/value`);
  return construct(() => new RawBlock(format as RawFormat, raw), path);
}

function parseBlocks(value: unknown, path: string): readonly Block[] {
  const entries = asArray(value, path);
  return entries.map((entry, index) => parseBlock(entry, `${path}/${index}`));
}
