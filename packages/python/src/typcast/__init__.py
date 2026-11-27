"""Typcast: the Python SDK for generating Typst documents.

The package exposes the immutable document model of the IR. The model
serializes to the language-neutral document IR and reads it back. The builder,
the emitter, the compiler adapter, and the validation engine are not part of
this release.
"""

from typcast.diagnostics import (
    Diagnostic,
    SerializationError,
    TypcastError,
    ValidationError,
)
from typcast.models import (
    Block,
    Bold,
    Document,
    Heading,
    Image,
    Italic,
    Length,
    LineBreak,
    Link,
    ListBlock,
    Margin,
    Metadata,
    Module,
    Monospace,
    Page,
    PageBreak,
    Paragraph,
    RawBlock,
    RawSpan,
    Span,
    Table,
    TableColumn,
    Text,
)
from typcast.version import SCHEMA_VERSION, __version__

__all__ = [
    "Block",
    "Bold",
    "Diagnostic",
    "Document",
    "Heading",
    "Image",
    "Italic",
    "Length",
    "LineBreak",
    "Link",
    "ListBlock",
    "Margin",
    "Metadata",
    "Module",
    "Monospace",
    "Page",
    "PageBreak",
    "Paragraph",
    "RawBlock",
    "RawSpan",
    "SCHEMA_VERSION",
    "SerializationError",
    "Span",
    "Table",
    "TableColumn",
    "Text",
    "TypcastError",
    "ValidationError",
    "__version__",
]
