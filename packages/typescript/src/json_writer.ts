/**
 * The canonical JSON writer of the document IR.
 *
 * The writer produces UTF-8 JSON with two-space indentation, a trailing
 * newline, and deterministic numbers. The number format follows the
 * ECMAScript `Number::toString` rules, so the Python and the TypeScript SDK
 * write the same text for the same document.
 *
 * The module depends on the diagnostics only, so every other module can use
 * it without creating an import cycle.
 */

import { CODE_NOT_SERIALIZABLE, throwSerialization } from "./diagnostics.js";

/** Raises when a value holds a character that UTF-8 cannot encode. */
export function assertEncodable(value: unknown, path: string): void {
  if (typeof value === "string") {
    for (let index = 0; index < value.length; index += 1) {
      const code = value.charCodeAt(index);
      if (code >= 0xd800 && code <= 0xdbff) {
        const next = index + 1 < value.length ? value.charCodeAt(index + 1) : 0;
        if (next < 0xdc00 || next > 0xdfff) {
          throwSerialization(
            CODE_NOT_SERIALIZABLE,
            `'${path}' holds a surrogate that UTF-8 cannot encode.`,
            path === "" ? null : path,
          );
        }
        index += 1;
      } else if (code >= 0xdc00 && code <= 0xdfff) {
        throwSerialization(
          CODE_NOT_SERIALIZABLE,
          `'${path}' holds a surrogate that UTF-8 cannot encode.`,
          path === "" ? null : path,
        );
      }
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => {
      assertEncodable(item, `${path}/${index}`);
    });
    return;
  }
  if (value !== null && typeof value === "object") {
    for (const [name, item] of Object.entries(value)) {
      assertEncodable(name, path);
      assertEncodable(item, `${path}/${name}`);
    }
  }
}

/** Returns the canonical JSON text of a value, without the trailing newline. */
export function canonicalJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
