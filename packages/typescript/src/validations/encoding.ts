/**
 * The size of the text of a document.
 *
 * The raw size limit of ADR-0017 is measured in the bytes of the UTF-8
 * encoding of the raw value. The Python SDK applies the same rule in
 * `src/typcast/validations/encoding.py`, so that both SDKs measure the same
 * number of bytes for the same text.
 */

/**
 * Returns the number of bytes of the UTF-8 encoding of a text.
 *
 * A character outside the Basic Multilingual Plane takes four bytes, a
 * character below it takes one, two, or three bytes, and a surrogate that
 * UTF-8 cannot encode takes three bytes, which is the size of the
 * replacement character that the encoder of ECMAScript writes. A surrogate
 * pair is one character of four bytes, and both SDKs count it as such.
 */
export function utf8Length(text: string): number {
  let total = 0;
  for (const character of text) {
    const code = character.codePointAt(0) ?? 0;
    if (code <= 0x7f) {
      total += 1;
    } else if (code <= 0x7ff) {
      total += 2;
    } else if (code <= 0xffff) {
      total += 3;
    } else {
      total += 4;
    }
  }
  return total;
}
