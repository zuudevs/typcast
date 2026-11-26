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

/** Returns the canonical JSON text of a value, without the trailing newline. */
export function canonicalJson(value: unknown): string {
  return JSON.stringify(value, null, 2);
}
