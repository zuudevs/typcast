"""Blocks of the document IR.

Every block is immutable. The constructors copy the collections they receive,
so a later mutation of a caller-owned list cannot change a block.
"""

from __future__ import annotations

from collections.abc import Sequence as SequenceABC
from dataclasses import dataclass
from typing import Any, ClassVar, Sequence

from typcast.diagnostics import (
    CODE_INVALID_HEADING_LEVEL,
    raise_validation,
)
from typcast.models.base import (
    Block,
    require_bool,
    require_enum,
    require_instance,
    require_int,
    require_string,
    require_tuple,
)
from typcast.models.page import Length
from typcast.models.spans import RAW_FORMATS, Span

__all__ = [
    "Heading",
    "Paragraph",
    "ListBlock",
    "Table",
    "TableColumn",
    "Image",
    "PageBreak",
    "RawBlock",
    "ALIGNMENTS",
]

ALIGNMENTS = ("left", "center", "right")


@dataclass(frozen=True)
class Heading(Block):
    """A section heading with a level from 1 to 6."""

    level: int
    content: Sequence[Span]

    type: ClassVar[str] = "heading"

    def __post_init__(self) -> None:
        level = require_int(self.level, "/level")
        if not 1 <= level <= 6:
            raise_validation(
                CODE_INVALID_HEADING_LEVEL,
                f"'/level' must be between 1 and 6, got {level}.",
                "/level",
                {"value": level},
            )
        object.__setattr__(self, "level", level)
        object.__setattr__(
            self,
            "content",
            require_tuple(self.content, Span, "/content", allow_empty=False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "level": self.level,
            "content": [span.to_dict() for span in self.content],
        }


@dataclass(frozen=True)
class Paragraph(Block):
    """A paragraph that contains inline spans."""

    content: Sequence[Span]

    type: ClassVar[str] = "paragraph"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "content",
            require_tuple(self.content, Span, "/content", allow_empty=False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": [span.to_dict() for span in self.content],
        }


@dataclass(frozen=True)
class ListBlock(Block):
    """An ordered or unordered list of inline span arrays."""

    ordered: bool
    items: Sequence[Sequence[Span]]

    type: ClassVar[str] = "list"

    def __post_init__(self) -> None:
        object.__setattr__(self, "ordered", require_bool(self.ordered, "/ordered"))
        items = require_tuple(self.items, SequenceABC, "/items", allow_empty=False)
        cells: list[tuple[Span, ...]] = []
        for index, item in enumerate(items):
            cells.append(
                require_tuple(
                    item,
                    Span,
                    f"/items/{index}",
                    allow_empty=False,
                )
            )
        object.__setattr__(self, "items", tuple(cells))

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "ordered": self.ordered,
            "items": [[span.to_dict() for span in item] for item in self.items],
        }


@dataclass(frozen=True)
class TableColumn:
    """A table column with a header and an alignment."""

    header: Sequence[Span]
    align: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "header",
            require_tuple(self.header, Span, "/header"),
        )
        object.__setattr__(
            self,
            "align",
            require_enum(self.align, ALIGNMENTS, "/align"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "header": [span.to_dict() for span in self.header],
            "align": self.align,
        }


@dataclass(frozen=True)
class Table(Block):
    """A table with columns, header cells, and rows.

    The number of cells of a row must match the number of columns. That rule
    belongs to the document validation layer and is not checked here.
    """

    columns: Sequence[TableColumn]
    rows: Sequence[Sequence[Sequence[Span]]]

    type: ClassVar[str] = "table"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "columns",
            require_tuple(self.columns, TableColumn, "/columns", allow_empty=False),
        )
        rows = require_tuple(self.rows, SequenceABC, "/rows", allow_empty=False)
        table_rows: list[tuple[tuple[Span, ...], ...]] = []
        for row_index, row in enumerate(rows):
            cells = require_tuple(row, SequenceABC, f"/rows/{row_index}")
            table_cells: list[tuple[Span, ...]] = []
            for cell_index, cell in enumerate(cells):
                table_cells.append(
                    require_tuple(
                        cell,
                        Span,
                        f"/rows/{row_index}/{cell_index}",
                    )
                )
            table_rows.append(tuple(table_cells))
        object.__setattr__(self, "rows", tuple(table_rows))

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "columns": [column.to_dict() for column in self.columns],
            "rows": [
                [[span.to_dict() for span in cell] for cell in row]
                for row in self.rows
            ],
        }


@dataclass(frozen=True)
class Image(Block):
    """An image with alternative text and an optional caption."""

    path: str
    alt: str
    caption: Sequence[Span] | None = None
    width: Length | None = None

    type: ClassVar[str] = "image"

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_string(self.path, "/path"))
        object.__setattr__(self, "alt", require_string(self.alt, "/alt"))
        if self.caption is not None:
            object.__setattr__(
                self,
                "caption",
                require_tuple(self.caption, Span, "/caption", allow_empty=False),
            )
        if self.width is not None:
            object.__setattr__(
                self,
                "width",
                require_instance(self.width, Length, "/width"),
            )

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {
            "type": self.type,
            "path": self.path,
            "alt": self.alt,
        }
        if self.caption is not None:
            value["caption"] = [span.to_dict() for span in self.caption]
        if self.width is not None:
            value["width"] = self.width.to_dict()
        return value


@dataclass(frozen=True)
class PageBreak(Block):
    """An explicit page break."""

    type: ClassVar[str] = "pageBreak"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type}


@dataclass(frozen=True)
class RawBlock(Block):
    """Verbatim Typst markup, code, or math."""

    format: str
    value: str

    type: ClassVar[str] = "raw"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "format",
            require_enum(self.format, RAW_FORMATS, "/format"),
        )
        object.__setattr__(
            self,
            "value",
            require_string(self.value, "/value"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "format": self.format, "value": self.value}
