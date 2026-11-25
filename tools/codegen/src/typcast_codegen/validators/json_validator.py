import json
from pathlib import Path
from typing import Any

from typcast_codegen.errors import CodegenError


class InvalidJsonConstant(ValueError):
    """Raised when a document holds a constant that JSON does not define."""

    def __init__(self, name: str) -> None:
        super().__init__(f"{name} is not a valid JSON value")
        self.name = name


def reject_json_constant(name: str) -> Any:
    """Reject the constants that `json.loads` accepts by default.

    Python accepts `NaN`, `Infinity`, and `-Infinity`, but the JSON
    specification does not. A file that holds such a value is rejected by
    every standard JSON parser, so the generator must not write one.
    """
    raise InvalidJsonConstant(name)


def parse_json_document(content: str, source: Path) -> Any:
    """Parse generated JSON and report syntax errors with source location."""
    try:
        return json.loads(content, parse_constant=reject_json_constant)
    except json.JSONDecodeError as error:
        raise CodegenError(
            f"{source}: invalid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    except InvalidJsonConstant as error:
        raise CodegenError(f"{source}: invalid JSON: {error}") from error
