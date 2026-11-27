"""The fluent builder of a document.

The builder collects the state of a document and turns it into an immutable
model at `build()`. The builder is mutable, one builder produces one document
at a time, and a builder must not be shared across threads. `build()` returns
an immutable snapshot, and a later call of the builder does not change a
document that was already built.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence, TypeVar

from typcast.builder.content import (
    normalize_content,
    normalize_spans,
    reject_api_argument,
    require_api_instance,
    require_api_number,
    require_api_sequence,
    require_api_string,
)
from typcast.diagnostics import (
    CODE_REQUIRED_FIELD,
    SEVERITY_ERROR,
    ValidationError,
    raise_validation,
    with_path,
)
from typcast.models.blocks import (
    Block,
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
from typcast.models.page import Length, Margin, Page

__all__ = ["DocumentBuilder"]

T = TypeVar("T")

# The defaults of the builder. The node catalog names them, and the builder
# applies them before the immutable model is created.
DEFAULT_PAPER = "a4"
DEFAULT_ORIENTATION = "portrait"
DEFAULT_MARGIN_CM = 2.5


def _default_margin() -> Margin:
    """Returns the default margin of a page."""
    length = Length.cm(DEFAULT_MARGIN_CM)
    return Margin(top=length, right=length, bottom=length, left=length)


def _construct(factory: Callable[[], T], prefix: str) -> T:
    """Builds a model and prefixes the paths of its diagnostics.

    The constructors of the model name the fields of their own model, so the
    path of a diagnostic points at the field of the model. The builder knows
    where the model belongs in the document, so it prefixes the path with the
    place of the model.
    """
    try:
        return factory()
    except ValidationError as error:
        raise ValidationError(
            str(error),
            with_path(error.diagnostics, prefix),
        ) from None


def _margin_of(margin: Length | Margin | None, path: str) -> Margin:
    """Returns the margin of a page.

    A single length is the margin of every side of the page, and a margin
    names every side itself.
    """
    if margin is None:
        return _default_margin()
    if isinstance(margin, Length):
        return Margin(top=margin, right=margin, bottom=margin, left=margin)
    if isinstance(margin, Margin):
        return margin
    reject_api_argument(path, "a Length or a Margin")


class DocumentBuilder:
    """The fluent builder of a document.

    The builder is mutable and is not thread-safe. One builder produces one
    document at a time, and `build()` returns an immutable snapshot that a
    later call of the builder does not change.
    """

    def __init__(self) -> None:
        self._title: str | None = None
        self._author: str | None = None
        self._date: str | None = None
        self._paper: str = DEFAULT_PAPER
        self._orientation: str = DEFAULT_ORIENTATION
        self._margin: Margin = _default_margin()
        self._contents: list[Block] = []
        self._modules: list[Module] = []

    def title(self, value: str) -> "DocumentBuilder":
        """Sets the title of the document."""
        self._title = require_api_string(value, "/metadata/title")
        return self

    def author(self, value: str) -> "DocumentBuilder":
        """Sets the author of the document."""
        self._author = require_api_string(value, "/metadata/author")
        return self

    def date(self, value: str) -> "DocumentBuilder":
        """Sets the date of the document."""
        self._date = require_api_string(value, "/metadata/date")
        return self

    def page(
        self,
        paper: str = DEFAULT_PAPER,
        orientation: str = DEFAULT_ORIENTATION,
        margin: Length | Margin | None = None,
    ) -> "DocumentBuilder":
        """Sets the page of the document.

        A single length is the margin of every side of the page. A margin
        names every side itself. The default is a margin of 2.5 centimeters
        on every side.
        """
        self._paper = require_api_string(paper, "/page/paper")
        self._orientation = require_api_string(orientation, "/page/orientation")
        self._margin = _margin_of(margin, "/page/margin")
        return self

    def heading(self, level: int, *content: Any) -> "DocumentBuilder":
        """Adds a heading with a level from 1 to 6."""
        path = f"/contents/{len(self._contents)}"
        value = require_api_number(level, f"{path}/level")
        spans = normalize_spans(content, f"{path}/content")
        self._contents.append(_construct(lambda: Heading(value, spans), path))
        return self

    def paragraph(self, *content: Any) -> "DocumentBuilder":
        """Adds a paragraph that holds the content."""
        path = f"/contents/{len(self._contents)}"
        spans = normalize_spans(content, f"{path}/content")
        self._contents.append(_construct(lambda: Paragraph(spans), path))
        return self

    def bullet_list(self, items: Any) -> "DocumentBuilder":
        """Adds an unordered list of items."""
        return self._list(items, ordered=False)

    def numbered_list(self, items: Any) -> "DocumentBuilder":
        """Adds an ordered list of items."""
        return self._list(items, ordered=True)

    def _list(self, items: Any, ordered: bool) -> "DocumentBuilder":
        """Adds a list of items."""
        path = f"/contents/{len(self._contents)}"
        values = require_api_sequence(
            items,
            f"{path}/items",
            "an array of content values",
        )
        entries = tuple(
            normalize_content(item, f"{path}/items/{index}")
            for index, item in enumerate(values)
        )
        self._contents.append(
            _construct(lambda: ListBlock(ordered, entries), path),
        )
        return self

    def table(self, columns: Any, rows: Any) -> "DocumentBuilder":
        """Adds a table with columns and rows.

        A row is an array of cells, and a cell is an array of content. The
        number of the cells of a row must match the number of the columns,
        and the validation engine reports the row that breaks the rule.
        """
        path = f"/contents/{len(self._contents)}"
        column_values = require_api_sequence(
            columns,
            f"{path}/columns",
            "an array of TableColumn values",
        )
        for index, value in enumerate(column_values):
            require_api_instance(
                value,
                TableColumn,
                f"{path}/columns/{index}",
                "TableColumn",
            )
        row_values = require_api_sequence(
            rows,
            f"{path}/rows",
            "an array of rows",
        )
        table_rows = tuple(
            self._row(row, f"{path}/rows/{index}")
            for index, row in enumerate(row_values)
        )
        self._contents.append(
            _construct(
                lambda: Table(tuple(column_values), table_rows),
                path,
            ),
        )
        return self

    def _row(self, row: Any, path: str) -> tuple[tuple[Any, ...], ...]:
        """Returns the cells of a row of a table."""
        cells = require_api_sequence(row, path, "an array of cells")
        return tuple(
            normalize_content(cell, f"{path}/{index}")
            for index, cell in enumerate(cells)
        )

    def image(
        self,
        path: str,
        alt: str,
        caption: Any = None,
        width: Length | None = None,
    ) -> "DocumentBuilder":
        """Adds an image with an alternative text.

        The caption is optional, and it is content, so a string becomes a
        text span. The width is optional, and the compiler determines it when
        the document holds no width.
        """
        location = f"/contents/{len(self._contents)}"
        image_path = require_api_string(path, f"{location}/path")
        image_alt = require_api_string(alt, f"{location}/alt")
        spans = (
            None
            if caption is None
            else normalize_content(caption, f"{location}/caption")
        )
        image_width = (
            None
            if width is None
            else require_api_instance(width, Length, f"{location}/width", "Length")
        )
        self._contents.append(
            _construct(
                lambda: Image(image_path, image_alt, spans, image_width),
                location,
            ),
        )
        return self

    def page_break(self) -> "DocumentBuilder":
        """Adds an explicit page break."""
        self._contents.append(PageBreak())
        return self

    def raw(self, value: str, format: str = "markup") -> "DocumentBuilder":
        """Adds a verbatim Typst block.

        The format is `markup`, `code`, or `math`. The raw content is opaque
        to Typcast, and the validation engine limits its size.
        """
        path = f"/contents/{len(self._contents)}"
        raw_value = require_api_string(value, f"{path}/value")
        raw_format = require_api_string(format, f"{path}/format")
        self._contents.append(
            _construct(lambda: RawBlock(raw_format, raw_value), path),
        )
        return self

    def module(
        self,
        path: str,
        alias: str | None = None,
        items: Sequence[str] | None = None,
    ) -> "DocumentBuilder":
        """Adds a module import declaration.

        The declaration keeps the order of the calls. The alias and the items
        must not both be set, and the alias must be unique in the document.
        The builder resolves no file and checks no path.
        """
        location = f"/modules/{len(self._modules)}"
        module_path = require_api_string(path, f"{location}/path")
        module_alias = (
            None
            if alias is None
            else require_api_string(alias, f"{location}/alias")
        )
        module_items = self._items(items, f"{location}/items")
        self._modules.append(
            _construct(
                lambda: Module(module_path, module_alias, module_items),
                location,
            ),
        )
        return self

    def _items(self, items: Sequence[str] | None, path: str) -> tuple[str, ...] | None:
        """Returns the items of a module declaration."""
        if items is None:
            return None
        values = require_api_sequence(items, path, "an array of strings")
        return tuple(
            require_api_string(item, f"{path}/{index}")
            for index, item in enumerate(values)
        )

    def build(self) -> Document:
        """Returns the immutable document of the current state of the builder.

        The method runs the semantic validation engine, and it raises a
        validation error when the engine reports an error. The diagnostics of
        the error hold every problem of the document, in the order of the
        document.
        """
        if self._title is None:
            raise_validation(
                CODE_REQUIRED_FIELD,
                "'/metadata/title' is required.",
                "/metadata/title",
                {"field": "title"},
            )
        document = _construct(
            lambda: Document(
                metadata=_construct(
                    lambda: Metadata(
                        title=self._title,
                        author=self._author,
                        date=self._date,
                    ),
                    "/metadata",
                ),
                page=_construct(
                    lambda: Page(
                        paper=self._paper,
                        orientation=self._orientation,
                        margin=self._margin,
                    ),
                    "/page",
                ),
                contents=tuple(self._contents),
                modules=tuple(self._modules),
            ),
            "",
        )
        diagnostics = document.validate()
        errors = tuple(
            diagnostic
            for diagnostic in diagnostics
            if diagnostic.severity == SEVERITY_ERROR
        )
        if errors:
            raise ValidationError(errors[0].message, errors)
        return document
