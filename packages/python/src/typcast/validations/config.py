"""The configuration of the validation engine.

The configuration holds the limits that the semantic rules use. ADR-0017 makes
the raw size limit the only configurable limit, and the TypeScript SDK applies
the same rule in `src/validations/config.ts`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typcast.diagnostics import (
    CODE_INVALID_RAW_LIMIT,
    raise_config,
    safe_text,
    safe_value,
)
from typcast.numbers import to_binary64

__all__ = [
    "DEFAULT_MAX_RAW_BYTES",
    "TypcastConfig",
]

# The default maximum number of bytes of a raw node. The value is the one
# MiB of ADR-0017, written as the number of bytes.
DEFAULT_MAX_RAW_BYTES = 1_048_576


@dataclass(frozen=True)
class TypcastConfig:
    """The configuration of the validation engine.

    The compilation fields of the documented configuration arrive with the
    asset layer and the compiler adapter, because they belong to the layers
    that read files and run the Typst compiler.
    """

    max_raw_bytes: int = DEFAULT_MAX_RAW_BYTES

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_raw_bytes",
            _checked_limit(self.max_raw_bytes),
        )


def _checked_limit(value: Any) -> int:
    """Returns the raw size limit after checking that it is a valid one.

    The limit is a number of bytes, so it must be an integer that the number
    domain of the IR holds and that is not negative. The TypeScript SDK
    applies the same rules, so that both SDKs reject the same value with the
    same diagnostic.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _raise_invalid_limit(value, "must be an integer")
    number = to_binary64(value) if isinstance(value, int) else value
    if not math.isfinite(number) or not number.is_integer():
        _raise_invalid_limit(value, "must be an integer")
    if number < 0:
        _raise_invalid_limit(value, "must not be negative")
    return int(number)


def _raise_invalid_limit(value: Any, rule: str) -> None:
    """Raises the diagnostic of an invalid raw size limit."""
    raise_config(
        CODE_INVALID_RAW_LIMIT,
        f"'/max_raw_bytes' {rule}, got '{safe_text(value)}'.",
        "/max_raw_bytes",
        {"value": safe_value(value)},
    )
