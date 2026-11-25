"""Module imports of the document IR."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Sequence

from typcast.diagnostics import (
    CODE_INVALID_MODULE_ALIAS,
    CODE_MODULE_ALIAS_AND_ITEMS,
    raise_validation,
    safe_value,
)
from typcast.models.base import require_sequence, require_string

__all__ = ["Module"]

# The pattern has no anchor at the end, and the match covers the whole text.
# A `$` of Python matches before a final newline, so an identifier that ends
# with a newline would pass here and would be rejected by the TypeScript SDK.
_IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


@dataclass(frozen=True)
class Module:
    """A module import declaration.

    The path must be relative and traversal-safe. That rule belongs to the
    asset layer, so the model checks the type of the value only.
    """

    path: str
    alias: str | None = None
    items: Sequence[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", require_string(self.path, "/path"))
        if self.alias is not None:
            self._check_identifier(self.alias, "/alias")
        if self.items is not None:
            # The elements are checked as identifiers, so that an element of
            # another type reports the same diagnostic as the TypeScript SDK.
            items = require_sequence(self.items, "/items", allow_empty=False)
            for index, item in enumerate(items):
                self._check_identifier(item, f"/items/{index}")
            object.__setattr__(self, "items", items)
        if self.alias is not None and self.items is not None:
            raise_validation(
                CODE_MODULE_ALIAS_AND_ITEMS,
                "'/alias' and '/items' must not both be set.",
                "/alias",
            )

    @staticmethod
    def _check_identifier(value: str, path: str) -> None:
        if (
            not isinstance(value, str)
            or _IDENTIFIER_PATTERN.fullmatch(value) is None
        ):
            raise_validation(
                CODE_INVALID_MODULE_ALIAS,
                f"'{path}' must match [A-Za-z_][A-Za-z0-9_]*, got {value!r}.",
                path,
                # The details of a diagnostic must be JSON-serializable, so a
                # value of an unknown type is represented by its type name.
                {"value": safe_value(value)},
            )

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"path": self.path}
        if self.alias is not None:
            value["alias"] = self.alias
        if self.items is not None:
            value["items"] = list(self.items)
        return value
