"""Shared helpers and base classes of the immutable document model.

The helpers implement the model-level invariants of the IR: argument types,
allowed enum values, and the element types of collections. The rules that
belong to the document validation layer, such as the table shape, the asset
paths, and the raw size limit, are deliberately not implemented here.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Iterable, Sequence, TypeVar

from typcast.diagnostics import (
    CODE_EMPTY_CONTENT,
    CODE_INVALID_ENUM,
    CODE_REQUIRED_FIELD,
    raise_validation,
)

__all__ = [
    "Block",
    "Span",
    "require_bool",
    "require_enum",
    "require_instance",
    "require_int",
    "require_number",
    "require_string",
    "require_tuple",
]

T = TypeVar("T")


def require_string(
    value: Any,
    path: str,
    *,
    allow_empty: bool = False,
) -> str:
    """Returns a string argument after checking its type and length."""
    if not isinstance(value, str):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a string.",
            path,
        )
    if not allow_empty and not value:
        raise_validation(
            CODE_EMPTY_CONTENT,
            f"'{path}' must not be empty.",
            path,
        )
    return value


def require_enum(
    value: Any,
    allowed: Iterable[str],
    path: str,
) -> str:
    """Returns an enum argument after checking that it is a known literal."""
    if not isinstance(value, str):
        raise_validation(
            CODE_INVALID_ENUM,
            f"'{path}' must be one of {', '.join(sorted(allowed))}.",
            path,
            {"allowed": sorted(allowed)},
        )
    if value not in allowed:
        raise_validation(
            CODE_INVALID_ENUM,
            f"'{path}' must be one of {', '.join(sorted(allowed))}, got {value!r}.",
            path,
            {"allowed": sorted(allowed), "value": value},
        )
    return value


def require_instance(value: Any, expected: type[T], path: str) -> T:
    """Returns a model argument after checking its type."""
    if not isinstance(value, expected):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a {expected.__name__}.",
            path,
            {"expected": expected.__name__},
        )
    return value


def require_bool(value: Any, path: str) -> bool:
    """Returns a boolean argument after checking its type."""
    if not isinstance(value, bool):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a boolean.",
            path,
        )
    return value


def require_int(value: Any, path: str) -> int:
    """Returns an integer argument after checking its type."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be an integer.",
            path,
        )
    return value


def require_number(value: Any, path: str) -> float | int:
    """Returns a numeric argument after checking its type."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a number.",
            path,
        )
    if isinstance(value, float) and not math.isfinite(value):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a finite number.",
            path,
        )
    return value


def require_tuple(
    value: Any,
    expected: type[T],
    path: str,
    *,
    allow_empty: bool = True,
) -> tuple[T, ...]:
    """Returns a copied tuple after checking the type of every element."""
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a sequence of {expected.__name__} values.",
            path,
            {"expected": expected.__name__},
        )
    items = tuple(value)
    for index, item in enumerate(items):
        if not isinstance(item, expected):
            raise_validation(
                CODE_REQUIRED_FIELD,
                f"'{path}/{index}' must be a {expected.__name__}.",
                f"{path}/{index}",
                {"expected": expected.__name__},
            )
    if not allow_empty and not items:
        raise_validation(
            CODE_EMPTY_CONTENT,
            f"'{path}' must not be empty.",
            path,
        )
    return items


@dataclass(frozen=True)
class Span(ABC):
    """The base class of every inline span."""

    type: ClassVar[str] = ""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Returns the JSON value of the span."""


@dataclass(frozen=True)
class Block(ABC):
    """The base class of every block."""

    type: ClassVar[str] = ""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Returns the JSON value of the block."""
