"""Inline spans of the document IR.

Every span is immutable. The constructors copy the collections they receive,
so a later mutation of a caller-owned list cannot change a span.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Sequence

from typcast.diagnostics import CODE_INVALID_ENUM, raise_validation
from typcast.models.base import Span, require_enum, require_string, require_tuple

__all__ = [
    "Text",
    "Bold",
    "Italic",
    "Monospace",
    "Link",
    "LineBreak",
    "RawSpan",
    "RAW_FORMATS",
]

RAW_FORMATS = ("markup", "code", "math")


@dataclass(frozen=True)
class Text(Span):
    """A plain text span."""

    value: str

    type: ClassVar[str] = "text"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "value",
            require_string(self.value, "/value"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type, "value": self.value}


@dataclass(frozen=True)
class Bold(Span):
    """A bold span."""

    content: Sequence[Span]

    type: ClassVar[str] = "bold"

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
class Italic(Span):
    """An italic span."""

    content: Sequence[Span]

    type: ClassVar[str] = "italic"

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
class Monospace(Span):
    """A monospace span."""

    content: Sequence[Span]

    type: ClassVar[str] = "monospace"

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
class Link(Span):
    """A link span with display text and a target."""

    href: str
    content: Sequence[Span]

    type: ClassVar[str] = "link"

    def __post_init__(self) -> None:
        object.__setattr__(self, "href", require_string(self.href, "/href"))
        object.__setattr__(
            self,
            "content",
            require_tuple(self.content, Span, "/content", allow_empty=False),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "href": self.href,
            "content": [span.to_dict() for span in self.content],
        }


@dataclass(frozen=True)
class LineBreak(Span):
    """An explicit line break."""

    type: ClassVar[str] = "lineBreak"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.type}


@dataclass(frozen=True)
class RawSpan(Span):
    """A verbatim inline Typst span."""

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
