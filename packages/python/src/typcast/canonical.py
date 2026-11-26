"""The canonical form rules of the document IR.

The module holds the two rules that the reader, the writer, and the model
share: the escaping of the tokens of a JSON Pointer, as RFC 6901 defines it,
and the encodability of the text of a document, which the canonical JSON text
requires to be UTF-8.

The TypeScript SDK applies the same rules in `src/canonical.ts`.
"""

from __future__ import annotations

from typing import Any, Mapping

from typcast.diagnostics import CODE_NOT_SERIALIZABLE, raise_serialization

__all__ = [
    "assert_encodable",
    "escape_pointer_token",
]


def escape_pointer_token(token: str) -> str:
    """Returns a JSON Pointer token, as RFC 6901 defines it.

    A `~` becomes `~0` and a `/` becomes `~1`, so that a property name that
    holds one of those characters still points at the property.
    """
    return token.replace("~", "~0").replace("/", "~1")


def assert_encodable(value: Any, path: str) -> None:
    """Rejects a value that holds a character that UTF-8 cannot encode.

    Python holds a lone surrogate in a string, and the writer writes such a
    character literally because it keeps the text of the document. The result
    would be a JSON text that no UTF-8 encoder can encode. The TypeScript SDK
    rejects the same value, so both SDKs reject it.

    The check walks the whole value, so a string that sits in a list or in the
    value of a property is rejected as well. The name of a property is a
    string too, and it is checked as well.
    """
    if isinstance(value, str):
        for index, character in enumerate(value):
            code = ord(character)
            if 0xD800 <= code <= 0xDBFF:
                following = ord(value[index + 1]) if index + 1 < len(value) else 0
                if not 0xDC00 <= following <= 0xDFFF:
                    _raise_unencodable(path)
            elif 0xDC00 <= code <= 0xDFFF:
                _raise_unencodable(path)
        return
    if isinstance(value, Mapping):
        for name, item in value.items():
            assert_encodable(name, path)
            assert_encodable(item, f"{path}/{escape_pointer_token(name)}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            assert_encodable(item, f"{path}/{index}")


def _raise_unencodable(path: str) -> None:
    raise_serialization(
        CODE_NOT_SERIALIZABLE,
        f"'{path}' holds a surrogate that UTF-8 cannot encode.",
        path if path else None,
    )
