"""The span helpers and the table helpers of the builder.

The helpers produce the model spans of the document IR. A string that is
passed as content is normalized to a `Text` span, and a span is kept as it
is. Two strings are never merged, because a merge would change the structure
of the content.
"""

from __future__ import annotations

from typing import Any

from typcast.builder.content import (
    normalize_content,
    normalize_spans,
    require_api_string,
)
from typcast.models.blocks import TableColumn
from typcast.models.spans import (
    Bold,
    Italic,
    LineBreak,
    Link,
    Monospace,
    RawSpan,
    Span,
    Text,
)

__all__ = [
    "bold",
    "cell",
    "column",
    "italic",
    "line_break",
    "link",
    "monospace",
    "raw_inline",
    "text",
]


def text(value: str) -> Text:
    """Returns a text span."""
    return Text(require_api_string(value, "/value"))


def bold(*content: Any) -> Bold:
    """Returns a bold span that holds the content."""
    return Bold(normalize_spans(content, "/content"))


def italic(*content: Any) -> Italic:
    """Returns an italic span that holds the content."""
    return Italic(normalize_spans(content, "/content"))


def monospace(*content: Any) -> Monospace:
    """Returns a monospace span that holds the content."""
    return Monospace(normalize_spans(content, "/content"))


def link(href: str, *content: Any) -> Link:
    """Returns a link span with a target and display content."""
    return Link(
        require_api_string(href, "/href"),
        normalize_spans(content, "/content"),
    )


def line_break() -> LineBreak:
    """Returns a line break span."""
    return LineBreak()


def raw_inline(value: str, format: str) -> RawSpan:
    """Returns a verbatim inline span."""
    return RawSpan(
        require_api_string(format, "/format"),
        require_api_string(value, "/value"),
    )


def column(header: Any, align: str = "left") -> TableColumn:
    """Returns a table column with a header and an alignment.

    The header is content, so a string becomes a text span.
    """
    return TableColumn(
        header=normalize_content(header, "/header"),
        align=require_api_string(align, "/align"),
    )


def cell(*content: Any) -> tuple[Span, ...]:
    """Returns a table cell that holds the content.

    A cell of the IR is an array of spans, so the helper returns that array.
    """
    return normalize_spans(content, "/content")
