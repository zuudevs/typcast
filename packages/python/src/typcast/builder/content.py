"""The checks and the normalization of the content of the builder.

A content argument of the builder is a string or a span. A string becomes a
`Text` span, and a span is kept as it is. Two strings are never merged,
because a merge would change the structure of the content.

The checks of the arguments of the public API live in `typcast.api`, because
the emitter uses them too. The rules of a node, such as the range of a heading
level, the emptiness of a content, and the syntax of a module alias, stay
with the constructors of the model.
"""

from __future__ import annotations

from typing import Any, Sequence

from typcast.api import reject_api_argument
from typcast.models.spans import Span, Text

__all__ = [
    "normalize_content",
    "normalize_span",
    "normalize_spans",
]


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
