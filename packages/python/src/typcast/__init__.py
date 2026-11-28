"""Typcast: the Python SDK for generating Typst documents.

The package exposes the immutable document model of the IR. The model
serializes to the language-neutral document IR and reads it back, and the
validation engine checks the semantic rules of a document. The fluent
builder is the primary API of the SDK. The emitter and the compiler adapter
are not part of this release.
"""

from typcast.builder import (
    DocumentBuilder,
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
from typcast.diagnostics import (
    ApiUsageError,
    CODE_SCHEMA_UNSUPPORTED_KEYWORD,
    CODE_SCHEMA_VIOLATION,
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
from typcast.schema import validate_schema
from typcast.validations import (
    DEFAULT_MAX_RAW_BYTES,
    TypcastConfig,
    validate_document,
)
from typcast.version import SCHEMA_VERSION, __version__

__all__ = [
    "ApiUsageError",
    "Block",
    "Bold",
    "CODE_SCHEMA_UNSUPPORTED_KEYWORD",
    "CODE_SCHEMA_VIOLATION",
    "ConfigError",
    "DEFAULT_MAX_RAW_BYTES",
    "Diagnostic",
    "Document",
    "DocumentBuilder",
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
    "bold",
    "cell",
    "column",
    "italic",
    "line_break",
    "link",
    "monospace",
    "raw_inline",
    "text",
    "validate_document",
    "validate_schema",
]
