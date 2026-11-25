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
    CODE_STRING_TOO_LONG,
    raise_validation,
)

__all__ = [
    "Block",
    "Span",
    "require_bool",
    "require_bounded_string",
    "require_enum",
    "require_instance",
    "require_int",
    "require_number",
    "require_sequence",
    "require_string",
    "require_tuple",
    "to_binary64",
]

T = TypeVar("T")


def to_binary64(value: int) -> float:
    """Returns an integer in the number domain of the document IR.

    The canonical JSON text of the IR follows the number format of
    ECMAScript, so the numbers of a document live in the binary64 domain.
    An integer that the domain cannot hold exactly is rounded to the nearest
    representable value, exactly as TypeScript and `JSON.parse` do, and an
    integer that overflows the domain becomes an infinity.
    """
    try:
        return float(value)
    except OverflowError:
        return math.inf


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


def require_bounded_string(
    value: Any,
    path: str,
    max_length: int,
    *,
    allow_empty: bool = False,
) -> str:
    """Returns a string argument after checking its type and its length.

    The length is counted in Unicode code points, as the contract counts it.
    A Python string counts code points, while a JavaScript string counts
    code units, so the TypeScript SDK counts the code points itself.
    """
    text = require_string(value, path, allow_empty=allow_empty)
    if len(text) > max_length:
        raise_validation(
            CODE_STRING_TOO_LONG,
            f"'{path}' must not hold more than {max_length} code points.",
            path,
            {"maxLength": max_length, "length": len(text)},
        )
    return text


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
    """Returns an integer argument after checking its type.

    An integer of the document IR is a number without a fractional part, as
    the `Number.isInteger` function of JavaScript defines it, so a value of
    `1.0` is an integer. A Python integer is narrowed to the number domain of
    the IR first, because that domain holds the numbers of a document.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be an integer.",
            path,
        )
    number = to_binary64(value) if isinstance(value, int) else value
    if not math.isfinite(number) or not number.is_integer():
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be an integer.",
            path,
        )
    return int(number)


def require_number(value: Any, path: str) -> float:
    """Returns a numeric argument after checking its type.

    The value is narrowed to the number domain of the IR, so that the number
    in the model is the number that the canonical text holds.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a number.",
            path,
        )
    number = to_binary64(value) if isinstance(value, int) else value
    if not math.isfinite(number):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a finite number.",
            path,
        )
    return number


def require_sequence(
    value: Any,
    path: str,
    *,
    allow_empty: bool = True,
) -> tuple[Any, ...]:
    """Returns a copied tuple after checking that the value is a sequence.

    The elements are not checked. A caller that accepts more than one kind of
    element checks every element itself.
    """
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise_validation(
            CODE_REQUIRED_FIELD,
            f"'{path}' must be a sequence.",
            path,
        )
    items = tuple(value)
    if not allow_empty and not items:
        raise_validation(
            CODE_EMPTY_CONTENT,
            f"'{path}' must not be empty.",
            path,
        )
    return items


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
