"""The size of the text of a document.

The raw size limit of ADR-0017 is measured in the bytes of the UTF-8 encoding
of the raw value. The TypeScript SDK applies the same rule in
`src/validations/encoding.ts`, so that both SDKs measure the same number of
bytes for the same text.
"""

from __future__ import annotations

__all__ = ["utf8_length"]


def utf8_length(text: str) -> int:
    """Returns the number of bytes of the UTF-8 encoding of a text.

    A character outside the Basic Multilingual Plane takes four bytes, a
    character below it takes one, two, or three bytes, and a surrogate that
    UTF-8 cannot encode takes three bytes, which is the size of the
    replacement character that the encoder of ECMAScript writes. A surrogate
    pair is one character of four bytes, and both SDKs count it as such.
    """
    total = 0
    index = 0
    length = len(text)
    while index < length:
        code = ord(text[index])
        if 0xD800 <= code <= 0xDBFF and index + 1 < length:
            following = ord(text[index + 1])
            if 0xDC00 <= following <= 0xDFFF:
                # A valid pair is one character outside the Basic Multilingual
                # Plane, and its encoding takes four bytes.
                total += 4
                index += 2
                continue
        if code <= 0x7F:
            total += 1
        elif code <= 0x7FF:
            total += 2
        elif code <= 0xFFFF:
            total += 3
        else:
            total += 4
        index += 1
    return total
