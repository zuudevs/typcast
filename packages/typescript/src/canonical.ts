/**
 * The canonical form rules of the document IR.
 *
 * The module holds the two rules that the reader, the writer, and the model
 * share: the escaping of the tokens of a JSON Pointer, as RFC 6901 defines
 * it, and the encodability of the text of a document, which the canonical
 * JSON text requires to be UTF-8.
 *
 * The Python SDK applies the same rules in `src/typcast/canonical.py`.
 */

import { CODE_NOT_SERIALIZABLE, throwSerialization } from "./diagnostics.js";

/**
 * Returns a JSON Pointer token, as RFC 6901 defines it.
 *
 * A `~` becomes `~0` and a `/` becomes `~1`, so that a property name that
 * holds one of those characters still points at the property.
 */
export function escapePointerToken(token: string): string {
  return token.replace(/~/g, "~0").replace(/\//g, "~1");
}

/**
 * Rejects a value that holds a character that UTF-8 cannot encode.
 *
 * A JavaScript string holds a lone surrogate, and the writer writes such a
 * character literally because it keeps the text of the document. The result
 * would be a JSON text that no UTF-8 encoder can encode. The Python SDK
 * rejects the same value, so both SDKs reject it.
 *
 * The check walks the whole value, so a string that sits in an array or in
 * the value of a property is rejected as well. The name of a property is a
 * string too, and it is checked as well.
 */
export function assertEncodable(value: unknown, path: string): void {
  if (typeof value === "string") {
    for (let index = 0; index < value.length; index += 1) {
      const code = value.charCodeAt(index);
      if (code >= 0xd800 && code <= 0xdbff) {
        const next = index + 1 < value.length ? value.charCodeAt(index + 1) : 0;
        if (next < 0xdc00 || next > 0xdfff) {
          raiseUnencodable(path);
        }
        index += 1;
      } else if (code >= 0xdc00 && code <= 0xdfff) {
        raiseUnencodable(path);
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
      assertEncodable(item, `${path}/${escapePointerToken(name)}`);
    }
  }
}

/** Raises when a value holds a character that UTF-8 cannot encode. */
function raiseUnencodable(path: string): never {
  throwSerialization(
    CODE_NOT_SERIALIZABLE,
    `'${path}' holds a surrogate that UTF-8 cannot encode.`,
    path === "" ? null : path,
  );
}
