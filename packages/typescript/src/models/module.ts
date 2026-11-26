/** Module imports of the document IR. */

import {
  CODE_INVALID_MODULE_ALIAS,
  CODE_MODULE_ALIAS_AND_ITEMS,
  safeText,
  safeValue,
  throwValidation,
} from "../diagnostics.js";
import { freezeArray, requireArray, requireInstance, requireString } from "./base.js";

const IDENTIFIER_PATTERN = /^[A-Za-z_][A-Za-z0-9_]*$/;

/**
 * A module import declaration.
 *
 * The path must be relative and traversal-safe. That rule belongs to the
 * asset layer, so the model checks the type of the value only.
 */
export class Module {
  readonly path: string;
  readonly alias: string | null;
  readonly items: readonly string[] | null;

  constructor(
    path: string,
    alias: string | null = null,
    items: readonly string[] | null = null,
  ) {
    this.path = requireString(path, "/path");
    if (alias !== null) {
      checkIdentifier(alias, "/alias");
    }
    if (items !== null) {
      const entries = requireArray(items, "/items", false);
      entries.forEach((item, index) => {
        checkIdentifier(item as string, `/items/${index}`);
      });
      this.items = freezeArray(entries as readonly string[]);
    } else {
      this.items = null;
    }
    this.alias = alias;
    if (this.alias !== null && this.items !== null) {
      throwValidation(
        CODE_MODULE_ALIAS_AND_ITEMS,
        "'/alias' and '/items' must not both be set.",
        "/alias",
      );
    }
    Object.freeze(this);
  }

  toJSON(): Record<string, unknown> {
    const value: Record<string, unknown> = { path: this.path };
    if (this.alias !== null) {
      value["alias"] = this.alias;
    }
    if (this.items !== null) {
      value["items"] = [...this.items];
    }
    return value;
  }
}

function checkIdentifier(value: string, path: string): void {
  if (typeof value !== "string" || !IDENTIFIER_PATTERN.test(value)) {
    throwValidation(
      CODE_INVALID_MODULE_ALIAS,
      `'${path}' must match [A-Za-z_][A-Za-z0-9_]*, got '${safeText(value)}'.`,
      path,
      // The details of a diagnostic must be JSON-serializable, so a value of
      // an unknown type is represented by its type name.
      { value: safeValue(value) },
    );
  }
}

/** Returns a frozen copy of a module collection after checking its elements. */
export function requireModules(
  value: unknown,
  path: string,
  allowEmpty = true,
): readonly Module[] {
  const items = requireArray(value, path, allowEmpty);
  const modules = items.map((item, index) =>
    requireInstance(item, Module, `${path}/${index}`),
  );
  return freezeArray(modules);
}
