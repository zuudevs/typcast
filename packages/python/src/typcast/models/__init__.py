"""The immutable document model of Typcast.

The model mirrors the document IR of `docs/specifications/document-ir.md`. Every
type is immutable: the Python implementation uses frozen dataclasses and
tuples, and the constructors copy the collections they receive.
"""

from typcast.models.base import Block, Span
from typcast.models.blocks import (
    Heading,
    Image,
    ListBlock,
    PageBreak,
    Paragraph,
    RawBlock,
    Table,
    TableColumn,
)
from typcast.models.document import Document
from typcast.models.metadata import Metadata
from typcast.models.module import Module
from typcast.models.page import PAPER_VARIANTS, Length, Margin, Page
from typcast.models.spans import (
    Bold,
    Italic,
    LineBreak,
    Link,
    Monospace,
    RawSpan,
    Text,
)

__all__ = [
    "Block",
    "Span",
    "Bold",
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
    "PAPER_VARIANTS",
    "Page",
    "PageBreak",
    "Paragraph",
    "RawBlock",
    "RawSpan",
    "Table",
    "TableColumn",
    "Text",
]
