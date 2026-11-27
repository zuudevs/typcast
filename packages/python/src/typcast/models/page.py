"""The page description of the document IR."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, ClassVar

from typcast.diagnostics import (
    CODE_INVALID_LENGTH,
    CODE_INVALID_ENUM,
    CODE_REQUIRED_FIELD,
    raise_validation,
    safe_text,
    safe_value,
)
from typcast.models.base import (
    require_enum,
    require_instance,
    require_string,
    to_binary64,
)
from typcast.numbers import format_number

__all__ = [
    "Length",
    "Margin",
    "Page",
    "LENGTH_UNITS",
    "ORIENTATIONS",
]

LENGTH_UNITS = ("pt", "mm", "cm", "in", "em")
ORIENTATIONS = ("portrait", "landscape")


@dataclass(frozen=True)
class Length:
    """A numeric length with a unit.

    The value lives in the number domain of the IR, which is the binary64
    domain of ECMAScript. A Python integer that the domain cannot hold
    exactly is rounded to the nearest representable value, exactly as the
    TypeScript SDK and `JSON.parse` do, so that the number in the model is
    the number that the canonical text holds.
    """

    value: float
    unit: str

    def __post_init__(self) -> None:
        value = self.value
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise_validation(
                CODE_REQUIRED_FIELD,
                "'/value' must be a number.",
                "/value",
            )
        if isinstance(value, int):
            value = to_binary64(value)
        if not math.isfinite(value):
            raise_validation(
                CODE_INVALID_LENGTH,
                "'/value' must be a finite number.",
                "/value",
                # The number is spelled in the form of ECMAScript, so that
                # the details of both SDKs agree.
                {
                    "value": "NaN"
                    if math.isnan(value)
                    else ("Infinity" if value > 0 else "-Infinity")
                },
            )
        if value < 0:
            # The number is shown in the canonical format of the IR, so that
            # the TypeScript SDK shows the same text.
            raise_validation(
                CODE_INVALID_LENGTH,
                f"'/value' must not be negative, got {format_number(value)}.",
                "/value",
                {"value": int(value) if value.is_integer() else value},
            )
        if self.unit not in LENGTH_UNITS:
            raise_validation(
                CODE_INVALID_LENGTH,
                f"'/unit' must be one of {', '.join(LENGTH_UNITS)}, "
                f"got '{safe_text(self.unit)}'.",
                "/unit",
                {"allowed": list(LENGTH_UNITS), "value": safe_value(self.unit)},
            )
        object.__setattr__(self, "value", value)

    def to_dict(self) -> dict[str, Any]:
        value: float = self.value
        if value.is_integer():
            value = int(value)
        return {"value": value, "unit": self.unit}


@dataclass(frozen=True)
class Margin:
    """The four margins of a page."""

    top: Length
    right: Length
    bottom: Length
    left: Length

    def __post_init__(self) -> None:
        object.__setattr__(self, "top", require_instance(self.top, Length, "/top"))
        object.__setattr__(
            self,
            "right",
            require_instance(self.right, Length, "/right"),
        )
        object.__setattr__(
            self,
            "bottom",
            require_instance(self.bottom, Length, "/bottom"),
        )
        object.__setattr__(self, "left", require_instance(self.left, Length, "/left"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "top": self.top.to_dict(),
            "right": self.right.to_dict(),
            "bottom": self.bottom.to_dict(),
            "left": self.left.to_dict(),
        }


@dataclass(frozen=True)
class Page:
    """The paper, the orientation, and the margin of a document.

    The paper value belongs to the catalog in
    `specs/catalogs/enums/paper-variants.csv`. The catalog is owned by the
    contract layer, so the model checks the type of the value and leaves the
    catalog check to the validation layer.
    """

    paper: str
    orientation: str
    margin: Margin

    def __post_init__(self) -> None:
        object.__setattr__(self, "paper", require_string(self.paper, "/paper"))
        object.__setattr__(
            self,
            "orientation",
            require_enum(self.orientation, ORIENTATIONS, "/orientation"),
        )
        object.__setattr__(
            self,
            "margin",
            require_instance(self.margin, Margin, "/margin"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper": self.paper,
            "orientation": self.orientation,
            "margin": self.margin.to_dict(),
        }
