"""The fluent builder of the Python SDK.

The builder is the primary API of the SDK. It collects the state of a
document and turns it into an immutable model at `build()`.
"""

from typcast.builder.builder import DocumentBuilder
from typcast.builder.helpers import (
    bold,
    cell,
    column,
    italic,
    line_break,
    link,
    monospace,
    raw_inline,
    text,
)

__all__ = [
    "DocumentBuilder",
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
