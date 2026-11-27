"""The checks and the normalization of the content of the builder.

A content argument of the builder is a string or a span. A string becomes a
`Text` span, and a span is kept as it is. Two strings are never merged,
because a merge would change the structure of the content.

The checks of this module report a misuse of the public API with
`TYPCAST-API-0001`. The rules of a node, such as the range of a heading
level, the emptiness of a content, and the syntax of a module alias, stay
with the constructors of the model.
"""

from __future__ import annotations

from typing import Any, NoReturn, Sequence

from typcast.diagnostics import CODE_INVALID_ARGUMENT, raise_api
from typcast.models.spans import Span, Text

__all__ = [
    "normalize_content",
    "normalize_span",
    "normalize_spans",
    "reject_api_argument",
    "require_api_instance",
    "require_api_number",
    "require_api_sequence",
    "require_api_string",
]


def reject_api_argument(path: str, expected: str) -> NoReturn:
    """Raises a public API error for a value of an unexpected type."""
    raise_api(
        CODE_INVALID_ARGUMENT,
        f"'{path}' must be {expected}.",
        path,
        {"expected": expected},
    )


def require_api_string(value: Any, path: str) -> str:
    """Returns a string argument after checking its type."""
    if not isinstance(value, str):
        reject_api_argument(path, "a string")
    return value


def require_api_number(value: Any, path: str) -> float:
    """Returns a numeric argument after checking its type.

    A boolean is not a number of the IR, so it is rejected here.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        reject_api_argument(path, "a number")
    return value


def require_api_instance(
    value: Any,
    expected: type,
    path: str,
    name: str,
) -> Any:
    """Returns a model argument after checking its type."""
    if not isinstance(value, expected):
        reject_api_argument(path, f"a {name}")
    return value


def require_api_sequence(value: Any, path: str, expected: str) -> Sequence[Any]:
    """Returns a sequence argument after checking its type.

    A string is a sequence of characters and not a sequence of elements, so it
    is rejected here, exactly as the model rejects it.
    """
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        reject_api_argument(path, expected)
    return value


def normalize_span(value: Any, path: str) -> Span:
    """Returns the span of a content value."""
    if isinstance(value, str):
        return Text(value)
    if isinstance(value, Span):
        return value
    reject_api_argument(path, "a string or a Span")


def normalize_spans(values: Sequence[Any], path: str) -> tuple[Span, ...]:
    """Returns the spans of a content collection."""
    return tuple(
        normalize_span(value, f"{path}/{index}")
        for index, value in enumerate(values)
    )


def normalize_content(value: Any, path: str) -> tuple[Span, ...]:
    """Returns the spans of a content value that may hold more than one span.

    A string becomes one text span, a span becomes one span, and an array
    holds the spans of its elements.
    """
    if isinstance(value, str):
        return (Text(value),)
    if isinstance(value, Span):
        return (value,)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        reject_api_argument(
            path,
            "a string, a Span, or an array of strings and Spans",
        )
    return normalize_spans(value, path)
