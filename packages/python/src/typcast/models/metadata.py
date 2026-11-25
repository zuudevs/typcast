"""The metadata of the document IR."""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass
from typing import Any

from typcast.diagnostics import CODE_INVALID_DATE, raise_validation
from typcast.models.base import require_string

__all__ = ["Metadata"]

_DATE_PATTERN = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


@dataclass(frozen=True)
class Metadata:
    """The title, the author, and the date of a document."""

    title: str
    author: str | None = None
    date: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", require_string(self.title, "/title"))
        if self.author is not None:
            object.__setattr__(
                self,
                "author",
                require_string(self.author, "/author", allow_empty=True),
            )
        if self.date is not None:
            self._check_date(self.date)

    @staticmethod
    def _check_date(value: str) -> None:
        if not isinstance(value, str):
            raise_validation(
                CODE_INVALID_DATE,
                "'/date' must be a string.",
                "/date",
            )
        match = _DATE_PATTERN.match(value)
        if match is None:
            raise_validation(
                CODE_INVALID_DATE,
                f"'/date' must be a calendar date in YYYY-MM-DD form, got {value!r}.",
                "/date",
                {"value": value},
            )
        year, month, day = (int(part) for part in match.groups())
        try:
            datetime.date(year, month, day)
        except ValueError as error:
            raise_validation(
                CODE_INVALID_DATE,
                f"'/date' is not a calendar date: {value!r}.",
                "/date",
                {"value": value, "cause": str(error)},
            )

    def to_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"title": self.title}
        if self.author is not None:
            value["author"] = self.author
        if self.date is not None:
            value["date"] = self.date
        return value
