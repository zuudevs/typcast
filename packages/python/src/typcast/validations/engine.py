"""The semantic validation engine of the document IR.

The engine checks the rules that the model constructors and the reader cannot
check, because a rule of the IR spans more than one node. ADR-0005 names the
engine the second layer of the validation, and ADR-0017 places the raw size
limit in it.

The engine reports every problem it finds and never raises for a semantic
error. The diagnostics come in the order of the document: the blocks in the
order of the contents, the spans in the order of their content, the rows of a
table in the order of the table, and the modules in the order of their
declaration. The TypeScript SDK applies the same rules in
`src/validations/engine.ts`, so that both SDKs report the same diagnostics in
the same order.
"""

from __future__ import annotations

from typing import Sequence

from typcast.diagnostics import (
    CODE_INVALID_MODULE_ALIAS,
    CODE_RAW_TOO_LARGE,
    CODE_TABLE_SHAPE,
    Diagnostic,
    validation_diagnostic,
)
from typcast.models.base import Block, Span, require_instance
from typcast.models.blocks import (
    Heading,
    Image,
    ListBlock,
    Paragraph,
    RawBlock,
    Table,
)
from typcast.models.document import Document
from typcast.models.module import Module
from typcast.models.spans import Bold, Italic, Link, Monospace, RawSpan
from typcast.validations.config import TypcastConfig
from typcast.validations.encoding import utf8_length

__all__ = ["validate_document"]


def validate_document(
    document: Document,
    config: TypcastConfig | None = None,
) -> tuple[Diagnostic, ...]:
    """Returns the diagnostics of the semantic rules of a document.

    The function reports every problem it finds and raises no error for a
    semantic problem. An invalid configuration raises a configuration error,
    because a limit that the SDK cannot read is not a property of the
    document.
    """
    require_instance(document, Document, "/")
    settings = config if config is not None else TypcastConfig()
    diagnostics: list[Diagnostic] = []
    for index, block in enumerate(document.contents):
        diagnostics.extend(_validate_block(block, f"/contents/{index}", settings))
    diagnostics.extend(_validate_modules(document.modules))
    return tuple(diagnostics)


def _validate_block(
    block: Block,
    path: str,
    config: TypcastConfig,
) -> list[Diagnostic]:
    """Returns the diagnostics of a block and of the nodes it holds."""
    if isinstance(block, Table):
        return _validate_table(block, path, config)
    if isinstance(block, RawBlock):
        return _validate_raw(block.value, f"{path}/value", config)
    return _validate_block_spans(block, path, config)


def _validate_block_spans(
    block: Block,
    path: str,
    config: TypcastConfig,
) -> list[Diagnostic]:
    """Returns the diagnostics of the spans a block holds."""
    diagnostics: list[Diagnostic] = []
    if isinstance(block, (Heading, Paragraph)):
        diagnostics.extend(_validate_spans(block.content, f"{path}/content", config))
    elif isinstance(block, ListBlock):
        for index, item in enumerate(block.items):
            diagnostics.extend(_validate_spans(item, f"{path}/items/{index}", config))
    elif isinstance(block, Image) and block.caption is not None:
        diagnostics.extend(_validate_spans(block.caption, f"{path}/caption", config))
    return diagnostics


def _validate_table(
    table: Table,
    path: str,
    config: TypcastConfig,
) -> list[Diagnostic]:
    """Returns the diagnostics of a table.

    The columns come before the rows, because the IR holds the columns
    first. Every row reports its own problem, so that a table with two broken
    rows reports two diagnostics.
    """
    diagnostics: list[Diagnostic] = []
    for index, column in enumerate(table.columns):
        diagnostics.extend(
            _validate_spans(column.header, f"{path}/columns/{index}/header", config)
        )
    for index, row in enumerate(table.rows):
        row_path = f"{path}/rows/{index}"
        if len(row) != len(table.columns):
            diagnostics.append(
                validation_diagnostic(
                    CODE_TABLE_SHAPE,
                    f"'{row_path}' must hold {len(table.columns)} cells, "
                    f"got {len(row)}.",
                    row_path,
                    {"columns": len(table.columns), "cells": len(row)},
                )
            )
        for cell_index, cell in enumerate(row):
            diagnostics.extend(
                _validate_spans(cell, f"{row_path}/{cell_index}", config)
            )
    return diagnostics


def _validate_spans(
    spans: Sequence[Span],
    path: str,
    config: TypcastConfig,
) -> list[Diagnostic]:
    """Returns the diagnostics of a collection of spans."""
    diagnostics: list[Diagnostic] = []
    for index, span in enumerate(spans):
        span_path = f"{path}/{index}"
        if isinstance(span, RawSpan):
            diagnostics.extend(_validate_raw(span.value, f"{span_path}/value", config))
        elif isinstance(span, (Bold, Italic, Monospace, Link)):
            diagnostics.extend(
                _validate_spans(span.content, f"{span_path}/content", config)
            )
    return diagnostics


def _validate_raw(
    value: str,
    path: str,
    config: TypcastConfig,
) -> list[Diagnostic]:
    """Returns the diagnostic of a raw value that is too large.

    ADR-0017 limits every raw node on its own, and the limit holds the number
    of bytes of the UTF-8 encoding of the value. A value of exactly the limit
    is valid.
    """
    size = utf8_length(value)
    if size <= config.max_raw_bytes:
        return []
    return [
        validation_diagnostic(
            CODE_RAW_TOO_LARGE,
            f"'{path}' must not hold more than {config.max_raw_bytes} bytes, "
            f"got {size}.",
            path,
            {"maxBytes": config.max_raw_bytes, "bytes": size},
        )
    ]


def _validate_modules(modules: Sequence[Module]) -> list[Diagnostic]:
    """Returns the diagnostics of the module declarations of a document.

    Only a module that names an alias takes part in the check. A module that
    imports items names no alias, and a module that names no alias takes the
    name of its file, which the asset layer resolves.
    """
    diagnostics: list[Diagnostic] = []
    first_use: dict[str, str] = {}
    for index, module in enumerate(modules):
        alias = module.alias
        if alias is None:
            continue
        path = f"/modules/{index}/alias"
        previous = first_use.get(alias)
        if previous is None:
            first_use[alias] = path
            continue
        diagnostics.append(
            validation_diagnostic(
                CODE_INVALID_MODULE_ALIAS,
                f"'{path}' is already used by the module at '{previous}'.",
                path,
                {"alias": alias, "duplicateOf": previous},
            )
        )
    return diagnostics
