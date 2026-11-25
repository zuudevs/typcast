"""JSON serialization and deserialization of the document IR.

The serializer writes the canonical form of the IR: UTF-8 JSON with two-space
indentation, a trailing newline, the field order of
`docs/specifications/document-ir.md`, and deterministic numbers. The
deserializer is driven by the `type` discriminator and rejects unknown fields,
missing required fields, and unsupported schema versions.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence, TypeVar

from typcast.diagnostics import (
    CODE_INVALID_ENUM,
    CODE_MALFORMED_JSON,
    CODE_NOT_SERIALIZABLE,
    CODE_REQUIRED_FIELD,
    CODE_ROOT_SHAPE,
    CODE_UNKNOWN_FIELD,
    ValidationError,
    raise_serialization,
    raise_validation,
    with_path,
)
from typcast.models.base import Block, Span, to_binary64
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
from typcast.models.page import Length, Margin, Page
from typcast.models.spans import (
    Bold,
    Italic,
    LineBreak,
    Link,
    Monospace,
    RawSpan,
    Text,
)
from typcast.version import check_schema_version

__all__ = [
    "document_to_dict",
    "document_from_dict",
    "document_to_json",
    "document_from_json",
]

T = TypeVar("T")

_MISSING = object()

_SPAN_FIELDS: Mapping[str, frozenset[str]] = {
    "text": frozenset({"type", "value"}),
    "bold": frozenset({"type", "content"}),
    "italic": frozenset({"type", "content"}),
    "monospace": frozenset({"type", "content"}),
    "link": frozenset({"type", "href", "content"}),
    "lineBreak": frozenset({"type"}),
    "raw": frozenset({"type", "format", "value"}),
}

_BLOCK_FIELDS: Mapping[str, frozenset[str]] = {
    "heading": frozenset({"type", "level", "content"}),
    "paragraph": frozenset({"type", "content"}),
    "list": frozenset({"type", "ordered", "items"}),
    "table": frozenset({"type", "columns", "rows"}),
    "image": frozenset({"type", "path", "alt", "caption", "width"}),
    "pageBreak": frozenset({"type"}),
    "raw": frozenset({"type", "format", "value"}),
}


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def document_to_dict(document: Document) -> dict[str, Any]:
    """Returns the JSON value of a document."""
    if not isinstance(document, Document):
        raise_serialization(
            CODE_NOT_SERIALIZABLE,
            "The value is not a document.",
        )
    return document.to_dict()


def document_from_dict(value: Any) -> Document:
    """Builds a document from a JSON value."""
    root = _as_object(value, "")
    _check_fields(root, frozenset({"schemaVersion", "metadata", "page", "contents", "modules"}), "")
    schema_version = _as_string(
        _require_field(root, "schemaVersion", ""),
        "/schemaVersion",
    )
    check_schema_version(schema_version)
    metadata = _parse_metadata(_require_field(root, "metadata", ""), "/metadata")
    page = _parse_page(_require_field(root, "page", ""), "/page")
    contents = _parse_blocks(_require_field(root, "contents", ""), "/contents")
    modules = _parse_modules(root.get("modules", []), "/modules")
    return Document(
        metadata=metadata,
        page=page,
        contents=contents,
        modules=modules,
        schema_version=schema_version,
    )


def document_to_json(document: Document) -> str:
    """Returns the canonical JSON text of a document."""
    value = document_to_dict(document)
    _assert_encodable(value, "")
    return _dumps(value) + "\n"


def document_from_json(source: str) -> Document:
    """Builds a document from JSON text."""
    if not isinstance(source, str):
        raise_serialization(
            CODE_MALFORMED_JSON,
            "The source must be a JSON string.",
        )
    try:
        value = json.loads(source, parse_constant=_reject_constant)
    except ValueError as error:
        raise_serialization(
            CODE_MALFORMED_JSON,
            f"The source is not valid JSON: {error}.",
        )
    return document_from_dict(value)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _reject_constant(name: str) -> Any:
    raise ValueError(f"{name} is not a valid JSON value")


def _as_object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path or '/'}' must be a JSON object.",
            path or None,
        )
    return value


def _as_array(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path}' must be a JSON array.",
            path,
        )
    return value


def _as_string(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path}' must be a JSON string.",
            path,
        )
    return value


def _as_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path}' must be a JSON boolean.",
            path,
        )
    return value


def _as_int(value: Any, path: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path}' must be a JSON integer.",
            path,
        )
    # A JSON integer is a number without a fractional part, as the
    # `Number.isInteger` function of JavaScript defines it, so a value of
    # `1.0` is an integer. A Python integer is narrowed to the number domain
    # of the IR first, exactly as `JSON.parse` does in JavaScript.
    number = to_binary64(value) if isinstance(value, int) else value
    if not math.isfinite(number) or not number.is_integer():
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path}' must be a JSON integer.",
            path,
        )
    return int(number)


def _as_number(value: Any, path: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path}' must be a JSON number.",
            path,
        )
    # The number domain of the IR is the binary64 domain of ECMAScript, so a
    # Python integer is narrowed to that domain, exactly as `JSON.parse` does
    # in JavaScript.
    number = to_binary64(value) if isinstance(value, int) else value
    if not math.isfinite(number):
        raise_serialization(
            CODE_ROOT_SHAPE,
            f"'{path}' must be a finite JSON number.",
            path,
        )
    return number


def _check_fields(value: Mapping[str, Any], allowed: frozenset[str], path: str) -> None:
    for name in value:
        if name not in allowed:
            location = f"{path}/{name}"
            raise_validation(
                CODE_UNKNOWN_FIELD,
                f"'{location}' is not a known field.",
                location,
                {"field": name},
            )


def _require_field(value: Mapping[str, Any], name: str, path: str) -> Any:
    if name not in value:
        location = f"{path}/{name}"
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{location}' is required.",
            location,
            {"field": name},
        )
    return value[name]


def _optional_field(value: Mapping[str, Any], name: str, path: str) -> Any:
    if name not in value:
        return _MISSING
    return value[name]


def _construct(factory: Callable[..., T], prefix: str, *args: Any, **kwargs: Any) -> T:
    """Builds a model and prefixes the paths of its diagnostics."""
    try:
        return factory(*args, **kwargs)
    except ValidationError as error:
        raise ValidationError(
            str(error),
            with_path(error.diagnostics, prefix),
        ) from None


def _parse_metadata(value: Any, path: str) -> Metadata:
    obj = _as_object(value, path)
    _check_fields(obj, frozenset({"title", "author", "date"}), path)
    title = _as_string(_require_field(obj, "title", path), f"{path}/title")
    author = _optional_field(obj, "author", path)
    if author is not _MISSING:
        author = _as_string(author, f"{path}/author")
    date = _optional_field(obj, "date", path)
    if date is not _MISSING:
        date = _as_string(date, f"{path}/date")
    return _construct(
        Metadata,
        path,
        title=title,
        author=author if author is not _MISSING else None,
        date=date if date is not _MISSING else None,
    )


def _parse_length(value: Any, path: str) -> Length:
    obj = _as_object(value, path)
    _check_fields(obj, frozenset({"value", "unit"}), path)
    number = _as_number(_require_field(obj, "value", path), f"{path}/value")
    unit = _as_string(_require_field(obj, "unit", path), f"{path}/unit")
    return _construct(Length, path, value=number, unit=unit)


def _parse_margin(value: Any, path: str) -> Margin:
    obj = _as_object(value, path)
    _check_fields(obj, frozenset({"top", "right", "bottom", "left"}), path)
    return _construct(
        Margin,
        path,
        top=_parse_length(_require_field(obj, "top", path), f"{path}/top"),
        right=_parse_length(_require_field(obj, "right", path), f"{path}/right"),
        bottom=_parse_length(_require_field(obj, "bottom", path), f"{path}/bottom"),
        left=_parse_length(_require_field(obj, "left", path), f"{path}/left"),
    )


def _parse_page(value: Any, path: str) -> Page:
    obj = _as_object(value, path)
    _check_fields(obj, frozenset({"paper", "orientation", "margin"}), path)
    paper = _as_string(_require_field(obj, "paper", path), f"{path}/paper")
    orientation = _as_string(
        _require_field(obj, "orientation", path),
        f"{path}/orientation",
    )
    margin = _parse_margin(_require_field(obj, "margin", path), f"{path}/margin")
    return _construct(
        Page,
        path,
        paper=paper,
        orientation=orientation,
        margin=margin,
    )


def _parse_module(value: Any, path: str) -> Module:
    obj = _as_object(value, path)
    _check_fields(obj, frozenset({"path", "alias", "items"}), path)
    module_path = _as_string(_require_field(obj, "path", path), f"{path}/path")
    alias = _optional_field(obj, "alias", path)
    if alias is not _MISSING:
        alias = _as_string(alias, f"{path}/alias")
    items = _optional_field(obj, "items", path)
    if items is not _MISSING:
        parsed = _as_array(items, f"{path}/items")
        items = tuple(
            _as_string(item, f"{path}/items/{index}")
            for index, item in enumerate(parsed)
        )
    return _construct(
        Module,
        path,
        path=module_path,
        alias=alias if alias is not _MISSING else None,
        items=items if items is not _MISSING else None,
    )


def _parse_modules(value: Any, path: str) -> tuple[Module, ...]:
    entries = _as_array(value, path)
    return tuple(
        _parse_module(entry, f"{path}/{index}")
        for index, entry in enumerate(entries)
    )


def _parse_span(value: Any, path: str) -> Span:
    obj = _as_object(value, path)
    discriminator = obj.get("type")
    if not isinstance(discriminator, str) or discriminator not in _SPAN_FIELDS:
        raise_validation(
            CODE_INVALID_ENUM,
            f"'{path}/type' must be one of {', '.join(sorted(_SPAN_FIELDS))}.",
            f"{path}/type",
            {"allowed": sorted(_SPAN_FIELDS)},
        )
    _check_fields(obj, _SPAN_FIELDS[discriminator], path)
    if discriminator == "text":
        return _construct(
            Text,
            path,
            value=_as_string(_require_field(obj, "value", path), f"{path}/value"),
        )
    if discriminator == "bold":
        return _construct(
            Bold,
            path,
            content=_parse_spans(_require_field(obj, "content", path), f"{path}/content"),
        )
    if discriminator == "italic":
        return _construct(
            Italic,
            path,
            content=_parse_spans(_require_field(obj, "content", path), f"{path}/content"),
        )
    if discriminator == "monospace":
        return _construct(
            Monospace,
            path,
            content=_parse_spans(_require_field(obj, "content", path), f"{path}/content"),
        )
    if discriminator == "link":
        return _construct(
            Link,
            path,
            href=_as_string(_require_field(obj, "href", path), f"{path}/href"),
            content=_parse_spans(_require_field(obj, "content", path), f"{path}/content"),
        )
    if discriminator == "lineBreak":
        return _construct(LineBreak, path)
    return _construct(
        RawSpan,
        path,
        format=_as_string(_require_field(obj, "format", path), f"{path}/format"),
        value=_as_string(_require_field(obj, "value", path), f"{path}/value"),
    )


def _parse_spans(value: Any, path: str) -> tuple[Span, ...]:
    entries = _as_array(value, path)
    return tuple(
        _parse_span(entry, f"{path}/{index}")
        for index, entry in enumerate(entries)
    )


def _parse_column(value: Any, path: str) -> TableColumn:
    obj = _as_object(value, path)
    _check_fields(obj, frozenset({"header", "align"}), path)
    header = _parse_spans(_require_field(obj, "header", path), f"{path}/header")
    align = _as_string(_require_field(obj, "align", path), f"{path}/align")
    return _construct(TableColumn, path, header=header, align=align)


def _parse_block(value: Any, path: str) -> Block:
    obj = _as_object(value, path)
    discriminator = obj.get("type")
    if not isinstance(discriminator, str) or discriminator not in _BLOCK_FIELDS:
        raise_validation(
            CODE_INVALID_ENUM,
            f"'{path}/type' must be one of {', '.join(sorted(_BLOCK_FIELDS))}.",
            f"{path}/type",
            {"allowed": sorted(_BLOCK_FIELDS)},
        )
    _check_fields(obj, _BLOCK_FIELDS[discriminator], path)
    if discriminator == "heading":
        return _construct(
            Heading,
            path,
            level=_as_int(_require_field(obj, "level", path), f"{path}/level"),
            content=_parse_spans(_require_field(obj, "content", path), f"{path}/content"),
        )
    if discriminator == "paragraph":
        return _construct(
            Paragraph,
            path,
            content=_parse_spans(_require_field(obj, "content", path), f"{path}/content"),
        )
    if discriminator == "list":
        entries = _as_array(_require_field(obj, "items", path), f"{path}/items")
        items = tuple(
            _parse_spans(entry, f"{path}/items/{index}")
            for index, entry in enumerate(entries)
        )
        return _construct(
            ListBlock,
            path,
            ordered=_as_bool(_require_field(obj, "ordered", path), f"{path}/ordered"),
            items=items,
        )
    if discriminator == "table":
        columns = _as_array(_require_field(obj, "columns", path), f"{path}/columns")
        parsed_columns = tuple(
            _parse_column(entry, f"{path}/columns/{index}")
            for index, entry in enumerate(columns)
        )
        rows = _as_array(_require_field(obj, "rows", path), f"{path}/rows")
        parsed_rows = tuple(
            _parse_row(entry, f"{path}/rows/{index}")
            for index, entry in enumerate(rows)
        )
        return _construct(
            Table,
            path,
            columns=parsed_columns,
            rows=parsed_rows,
        )
    if discriminator == "image":
        caption = _optional_field(obj, "caption", path)
        if caption is not _MISSING:
            caption = _parse_spans(caption, f"{path}/caption")
        width = _optional_field(obj, "width", path)
        if width is not _MISSING:
            width = _parse_length(width, f"{path}/width")
        return _construct(
            Image,
            path,
            path=_as_string(_require_field(obj, "path", path), f"{path}/path"),
            alt=_as_string(_require_field(obj, "alt", path), f"{path}/alt"),
            caption=caption if caption is not _MISSING else None,
            width=width if width is not _MISSING else None,
        )
    if discriminator == "pageBreak":
        return _construct(PageBreak, path)
    return _construct(
        RawBlock,
        path,
        format=_as_string(_require_field(obj, "format", path), f"{path}/format"),
        value=_as_string(_require_field(obj, "value", path), f"{path}/value"),
    )


def _parse_row(value: Any, path: str) -> tuple[tuple[Span, ...], ...]:
    cells = _as_array(value, path)
    return tuple(
        _parse_spans(cell, f"{path}/{index}")
        for index, cell in enumerate(cells)
    )


def _parse_blocks(value: Any, path: str) -> tuple[Block, ...]:
    entries = _as_array(value, path)
    return tuple(
        _parse_block(entry, f"{path}/{index}")
        for index, entry in enumerate(entries)
    )


# ---------------------------------------------------------------------------
# Canonical JSON writer
# ---------------------------------------------------------------------------


def _assert_encodable(value: Any, path: str) -> None:
    """Rejects a value that holds a character that UTF-8 cannot encode.

    Python holds a lone surrogate in a string, and the writer writes such a
    character literally because it keeps the text of the document. The result
    would be a JSON text that no UTF-8 encoder can encode. The TypeScript SDK
    rejects the same value, so both SDKs reject it.
    """
    if isinstance(value, str):
        for index, character in enumerate(value):
            code = ord(character)
            if 0xD800 <= code <= 0xDBFF:
                following = ord(value[index + 1]) if index + 1 < len(value) else 0
                if not 0xDC00 <= following <= 0xDFFF:
                    _raise_unencodable(path)
            elif 0xDC00 <= code <= 0xDFFF:
                _raise_unencodable(path)
        return
    if isinstance(value, Mapping):
        for name, item in value.items():
            _assert_encodable(name, path)
            _assert_encodable(item, f"{path}/{name}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_encodable(item, f"{path}/{index}")


def _raise_unencodable(path: str) -> None:
    raise_serialization(
        CODE_NOT_SERIALIZABLE,
        f"'{path}' holds a surrogate that UTF-8 cannot encode.",
        path if path else None,
    )


def _dumps(value: Any) -> str:
    parts: list[str] = []
    _write(value, 0, parts)
    return "".join(parts)


def _write(value: Any, level: int, parts: list[str]) -> None:
    if value is None:
        parts.append("null")
    elif value is True:
        parts.append("true")
    elif value is False:
        parts.append("false")
    elif isinstance(value, str):
        parts.append(json.dumps(value, ensure_ascii=False))
    elif isinstance(value, int):
        parts.append(_format_integer(value))
    elif isinstance(value, float):
        parts.append(_format_float(value))
    elif isinstance(value, dict):
        _write_object(value, level, parts)
    elif isinstance(value, (list, tuple)):
        _write_array(value, level, parts)
    else:
        raise_serialization(
            CODE_NOT_SERIALIZABLE,
            f"A value of type {type(value).__name__} cannot be serialized.",
        )


def _write_object(value: Mapping[str, Any], level: int, parts: list[str]) -> None:
    if not value:
        parts.append("{}")
        return
    indent = "  " * (level + 1)
    parts.append("{\n")
    for index, (name, item) in enumerate(value.items()):
        if index:
            parts.append(",\n")
        parts.append(indent)
        parts.append(json.dumps(name, ensure_ascii=False))
        parts.append(": ")
        _write(item, level + 1, parts)
    parts.append("\n")
    parts.append("  " * level)
    parts.append("}")


def _write_array(value: Sequence[Any], level: int, parts: list[str]) -> None:
    if not value:
        parts.append("[]")
        return
    indent = "  " * (level + 1)
    parts.append("[\n")
    for index, item in enumerate(value):
        if index:
            parts.append(",\n")
        parts.append(indent)
        _write(item, level + 1, parts)
    parts.append("\n")
    parts.append("  " * level)
    parts.append("]")


def _format_integer(value: int) -> str:
    if -(2**53) <= value <= 2**53:
        return str(value)
    return _format_float(float(value))


def _format_float(value: float) -> str:
    """Formats a number the way the JavaScript serializer formats it."""
    if math.isnan(value) or math.isinf(value):
        raise_serialization(
            CODE_NOT_SERIALIZABLE,
            "NaN and Infinity cannot be serialized.",
        )
    if value == 0:
        return "0"
    sign, digits, exponent = Decimal(repr(value)).as_tuple()
    coefficient = list(digits)
    while len(coefficient) > 1 and coefficient[-1] == 0:
        coefficient.pop()
        exponent += 1
    text = "".join(str(digit) for digit in coefficient)
    count = len(text)
    point = exponent + count
    if -6 < point <= 21:
        if point <= 0:
            body = "0." + "0" * (-point) + text
        elif point >= count:
            body = text + "0" * (point - count)
        else:
            body = text[:point] + "." + text[point:]
    else:
        mantissa = text[0] if count == 1 else text[0] + "." + text[1:]
        power = point - 1
        body = mantissa + "e" + ("+" if power >= 0 else "-") + str(abs(power))
    return ("-" if sign else "") + body
