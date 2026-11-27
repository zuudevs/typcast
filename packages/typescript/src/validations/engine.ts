/**
 * The semantic validation engine of the document IR.
 *
 * The engine checks the rules that the model constructors and the reader
 * cannot check, because a rule of the IR spans more than one node. ADR-0005
 * names the engine the second layer of the validation, and ADR-0017 places
 * the raw size limit in it.
 *
 * The engine reports every problem it finds and never throws for a semantic
 * error. The diagnostics come in the order of the document: the blocks in the
 * order of the contents, the spans in the order of their content, the rows of
 * a table in the order of the table, and the modules in the order of their
 * declaration. The Python SDK applies the same rules in
 * `src/typcast/validations/engine.py`, so that both SDKs report the same
 * diagnostics in the same order.
 */

import {
  CODE_INVALID_MODULE_ALIAS,
  CODE_RAW_TOO_LARGE,
  CODE_REQUIRED_FIELD,
  CODE_TABLE_SHAPE,
  throwValidation,
  validationDiagnostic,
} from "../diagnostics.js";
import type { Diagnostic } from "../diagnostics.js";
import {
  Heading,
  Image,
  ListBlock,
  Paragraph,
  RawBlock,
  Table,
} from "../models/blocks.js";
import type { Block } from "../models/blocks.js";
import type { Document } from "../models/document.js";
import type { Module } from "../models/module.js";
import { Bold, Italic, Link, Monospace, RawSpan } from "../models/spans.js";
import type { Span } from "../models/spans.js";
import { resolveOptions } from "./config.js";
import type { TypcastOptions } from "./config.js";
import { utf8Length } from "./encoding.js";

/**
 * Returns the diagnostics of the semantic rules of a document.
 *
 * The function reports every problem it finds and throws no error for a
 * semantic problem. An invalid configuration raises a configuration error,
 * because a limit that the SDK cannot read is not a property of the
 * document.
 */
export function validateDocument(
  document: Document,
  options?: TypcastOptions,
): readonly Diagnostic[] {
  requireDocument(document);
  const settings = resolveOptions(options);
  const diagnostics: Diagnostic[] = [];
  document.contents.forEach((block, index) => {
    diagnostics.push(...validateBlock(block, `/contents/${index}`, settings));
  });
  diagnostics.push(...validateModules(document.modules));
  return Object.freeze(diagnostics);
}

/**
 * Returns the document after checking that it is one.
 *
 * The check is a structural one, because the class of the document and the
 * engine would import each other. The Python SDK checks the type of the
 * value, and both SDKs report the same diagnostic for a value that is not a
 * document.
 */
function requireDocument(document: Document): Document {
  if (
    typeof document !== "object" ||
    document === null ||
    !Array.isArray((document as Document).contents) ||
    !Array.isArray((document as Document).modules)
  ) {
    throwValidation(
      CODE_REQUIRED_FIELD,
      "'/' must be a Document.",
      "/",
      { expected: "Document" },
    );
  }
  return document;
}

/** Returns the diagnostics of a block and of the nodes it holds. */
function validateBlock(
  block: Block,
  path: string,
  options: { readonly maxRawBytes: number },
): Diagnostic[] {
  if (block instanceof Table) {
    return validateTable(block, path, options);
  }
  if (block instanceof RawBlock) {
    return validateRaw(block.value, `${path}/value`, options);
  }
  return validateBlockSpans(block, path, options);
}

/** Returns the diagnostics of the spans a block holds. */
function validateBlockSpans(
  block: Block,
  path: string,
  options: { readonly maxRawBytes: number },
): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
  if (block instanceof Heading || block instanceof Paragraph) {
    diagnostics.push(...validateSpans(block.content, `${path}/content`, options));
  } else if (block instanceof ListBlock) {
    block.items.forEach((item, index) => {
      diagnostics.push(...validateSpans(item, `${path}/items/${index}`, options));
    });
  } else if (block instanceof Image && block.caption !== null) {
    diagnostics.push(...validateSpans(block.caption, `${path}/caption`, options));
  }
  return diagnostics;
}

/**
 * Returns the diagnostics of a table.
 *
 * The columns come before the rows, because the IR holds the columns first.
 * Every row reports its own problem, so that a table with two broken rows
 * reports two diagnostics.
 */
function validateTable(
  table: Table,
  path: string,
  options: { readonly maxRawBytes: number },
): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
  table.columns.forEach((column, index) => {
    diagnostics.push(
      ...validateSpans(column.header, `${path}/columns/${index}/header`, options),
    );
  });
  table.rows.forEach((row, index) => {
    const rowPath = `${path}/rows/${index}`;
    if (row.length !== table.columns.length) {
      diagnostics.push(
        validationDiagnostic(
          CODE_TABLE_SHAPE,
          `'${rowPath}' must hold ${table.columns.length} cells, got ${row.length}.`,
          rowPath,
          { columns: table.columns.length, cells: row.length },
        ),
      );
    }
    row.forEach((cell, cellIndex) => {
      diagnostics.push(
        ...validateSpans(cell, `${rowPath}/${cellIndex}`, options),
      );
    });
  });
  return diagnostics;
}

/** Returns the diagnostics of a collection of spans. */
function validateSpans(
  spans: readonly Span[],
  path: string,
  options: { readonly maxRawBytes: number },
): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
  spans.forEach((span, index) => {
    const spanPath = `${path}/${index}`;
    if (span instanceof RawSpan) {
      diagnostics.push(
        ...validateRaw(span.value, `${spanPath}/value`, options),
      );
    } else if (
      span instanceof Bold ||
      span instanceof Italic ||
      span instanceof Monospace ||
      span instanceof Link
    ) {
      diagnostics.push(
        ...validateSpans(span.content, `${spanPath}/content`, options),
      );
    }
  });
  return diagnostics;
}

/**
 * Returns the diagnostic of a raw value that is too large.
 *
 * ADR-0017 limits every raw node on its own, and the limit holds the number
 * of bytes of the UTF-8 encoding of the value. A value of exactly the limit
 * is valid.
 */
function validateRaw(
  value: string,
  path: string,
  options: { readonly maxRawBytes: number },
): Diagnostic[] {
  const size = utf8Length(value);
  if (size <= options.maxRawBytes) {
    return [];
  }
  return [
    validationDiagnostic(
      CODE_RAW_TOO_LARGE,
      `'${path}' must not hold more than ${options.maxRawBytes} bytes, got ${size}.`,
      path,
      { maxBytes: options.maxRawBytes, bytes: size },
    ),
  ];
}

/**
 * Returns the diagnostics of the module declarations of a document.
 *
 * Only a module that names an alias takes part in the check. A module that
 * imports items names no alias, and a module that names no alias takes the
 * name of its file, which the asset layer resolves.
 */
function validateModules(modules: readonly Module[]): Diagnostic[] {
  const diagnostics: Diagnostic[] = [];
  const firstUse = new Map<string, string>();
  modules.forEach((module, index) => {
    const alias = module.alias;
    if (alias === null) {
      return;
    }
    const path = `/modules/${index}/alias`;
    const previous = firstUse.get(alias);
    if (previous === undefined) {
      firstUse.set(alias, path);
      return;
    }
    diagnostics.push(
      validationDiagnostic(
        CODE_INVALID_MODULE_ALIAS,
        `'${path}' is already used by the module at '${previous}'.`,
        path,
        { alias, duplicateOf: previous },
      ),
    );
  });
  return diagnostics;
}
