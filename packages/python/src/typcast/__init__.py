"""Typcast: the Python SDK for generating Typst documents.

The package exposes the immutable document model of the IR. The model
serializes to the language-neutral document IR and reads it back, and the
validation engine checks the semantic rules of a document. The builder, the
emitter, and the compiler adapter are not part of this release.
"""

from typcast.diagnostics import (
    ConfigError,
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
from typcast.validations import (
    DEFAULT_MAX_RAW_BYTES,
    TypcastConfig,
    validate_document,
)
from typcast.version import SCHEMA_VERSION, __version__

__all__ = [
    "Block",
    "Bold",
    "ConfigError",
    "DEFAULT_MAX_RAW_BYTES",
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
    "TypcastConfig",
    "TypcastError",
    "ValidationError",
    "__version__",
    "validate_document",
]
