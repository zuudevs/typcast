"""Structured diagnostics and the Typcast error hierarchy.

The shapes follow `docs/specifications/diagnostics.md`. Every error raised by
the SDK inherits from :class:`TypcastError` and exposes a `diagnostics`
collection. The first diagnostic is the primary cause.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

__all__ = [
    "Diagnostic",
    "TypcastError",
    "ApiUsageError",
    "ValidationError",
    "SerializationError",
    "ConfigError",
    "safe_text",
    "safe_value",
    "MAX_DIAGNOSTIC_VALUE_LENGTH",
    "SEVERITY_ERROR",
    "SEVERITY_WARNING",
    "SEVERITY_INFO",
    "PHASE_API",
    "PHASE_VALIDATION",
    "PHASE_SERIALIZATION",
    "PHASE_EMIT",
    "PHASE_COMPILER",
    "PHASE_IO",
    "PHASE_CONFIG",
    "CODE_INVALID_ARGUMENT",
    "CODE_INVALID_STATE",
    "CODE_REQUIRED_FIELD",
    "CODE_UNKNOWN_FIELD",
    "CODE_INVALID_ENUM",
    "CODE_INVALID_LENGTH",
    "CODE_INVALID_HEADING_LEVEL",
    "CODE_EMPTY_CONTENT",
    "CODE_TABLE_SHAPE",
    "CODE_INVALID_MODULE_ALIAS",
    "CODE_MODULE_ALIAS_AND_ITEMS",
    "CODE_RAW_TOO_LARGE",
    "CODE_INVALID_DATE",
    "CODE_STRING_TOO_LONG",
    "CODE_MALFORMED_JSON",
    "CODE_UNSUPPORTED_VERSION",
    "CODE_NOT_SERIALIZABLE",
    "CODE_ROOT_SHAPE",
    "CODE_INVALID_RAW_LIMIT",
    "api_diagnostic",
    "config_diagnostic",
    "raise_api",
    "raise_config",
]


SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"

PHASE_API = "api"
PHASE_VALIDATION = "validation"
PHASE_SERIALIZATION = "serialization"
PHASE_EMIT = "emit"
PHASE_COMPILER = "compiler"
PHASE_IO = "io"
PHASE_CONFIG = "config"

# The number of characters of a value that the message of a diagnostic shows.
MAX_DIAGNOSTIC_VALUE_LENGTH = 64

# Public API codes. The catalog lives in `docs/specifications/diagnostics.md`.
CODE_INVALID_ARGUMENT = "TYPCAST-API-0001"
CODE_INVALID_STATE = "TYPCAST-API-0002"

# Validation codes. The catalog lives in `docs/specifications/diagnostics.md`.
CODE_REQUIRED_FIELD = "TYPCAST-VAL-0001"
CODE_UNKNOWN_FIELD = "TYPCAST-VAL-0002"
CODE_INVALID_ENUM = "TYPCAST-VAL-0003"
CODE_INVALID_LENGTH = "TYPCAST-VAL-0004"
CODE_INVALID_HEADING_LEVEL = "TYPCAST-VAL-0005"
CODE_EMPTY_CONTENT = "TYPCAST-VAL-0006"
CODE_TABLE_SHAPE = "TYPCAST-VAL-0007"
# The catalog assigns one code to a module alias that is invalid and to a
# module alias that is duplicated, so the constant covers both cases.
CODE_INVALID_MODULE_ALIAS = "TYPCAST-VAL-0008"
CODE_MODULE_ALIAS_AND_ITEMS = "TYPCAST-VAL-0009"
CODE_RAW_TOO_LARGE = "TYPCAST-VAL-0010"
CODE_INVALID_DATE = "TYPCAST-VAL-0011"
CODE_STRING_TOO_LONG = "TYPCAST-VAL-0013"

# Serialization codes.
CODE_MALFORMED_JSON = "TYPCAST-IR-0001"
CODE_UNSUPPORTED_VERSION = "TYPCAST-IR-0002"
CODE_NOT_SERIALIZABLE = "TYPCAST-IR-0003"
CODE_ROOT_SHAPE = "TYPCAST-IR-0004"

# Configuration codes.
CODE_INVALID_RAW_LIMIT = "TYPCAST-CONFIG-0004"


def _freeze_mapping(value: Mapping[str, Any] | None) -> Mapping[str, Any] | None:
    """Returns a read-only view of a mapping."""
    if value is None:
        return None
    return MappingProxyType(dict(value))


def _safe_integer(value: int) -> Any:
    """Returns a JSON-serializable representation of an integer.

    The interpreter limits the conversion of a long digit string to a string,
    so the details of a diagnostic must not hold such an integer. A number of
    the IR lives in the binary64 domain of ECMAScript, so an integer that the
    domain cannot hold is represented by the infinity of that domain.
    """
    try:
        str(value)
    except ValueError:
        try:
            return float(value)
        except OverflowError:
            return "Infinity" if value > 0 else "-Infinity"
    return value


def safe_value(value: Any) -> Any:
    """Returns a JSON-serializable representation of a value.

    The details of a diagnostic must be JSON-serializable, so a value of an
    unknown type is represented by the name of its type, and a number that is
    not finite is represented by its spelling in the form of ECMAScript. The
    TypeScript SDK applies the same rule.
    """
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, int):
        return _safe_integer(value)
    if isinstance(value, float):
        if math.isfinite(value):
            return value
        if math.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, Mapping):
        return "object"
    if isinstance(value, (list, tuple)):
        return "array"
    return type(value).__name__


# The escape sequences of a rejected value. A control character that has no
# sequence of its own is written as a `\u00xx` escape. The TypeScript SDK
# applies the same rule.
_ESCAPE_SEQUENCES: Mapping[str, str] = {
    "\\": "\\\\",
    "'": "\\'",
    '"': '\\"',
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def _escape_text(text: str) -> str:
    """Returns the text of a value with every breakable character escaped."""
    parts: list[str] = []
    for character in text:
        sequence = _ESCAPE_SEQUENCES.get(character)
        if sequence is not None:
            parts.append(sequence)
            continue
        code = ord(character)
        if code < 0x20 or code == 0x7F:
            parts.append(f"\\u{code:04x}")
            continue
        parts.append(character)
    return "".join(parts)


def safe_text(value: Any) -> str:
    """Returns the canonical text of a rejected value.

    The text holds at most 64 code points of the value, followed by an
    ellipsis when the value is longer. Every character that could break the
    text of a message is escaped, so that a quote, a backslash, a newline, a
    carriage return, a tab, and any other control character appear as an
    escape sequence. Every other character is shown as it is.

    The rule is the one of `docs/specifications/diagnostics.md`, and the
    TypeScript SDK applies the same rule, so that the message of a diagnostic
    is the same in both SDKs.
    """
    text = value if isinstance(value, str) else str(safe_value(value))
    characters = list(text)
    truncated = len(characters) > MAX_DIAGNOSTIC_VALUE_LENGTH
    if truncated:
        characters = characters[:MAX_DIAGNOSTIC_VALUE_LENGTH]
    escaped = _escape_text("".join(characters))
    return escaped + "…" if truncated else escaped


@dataclass(frozen=True)
class Diagnostic:
    """A single machine-readable problem report."""

    code: str
    severity: str
    phase: str
    message: str
    path: str | None = None
    location: Mapping[str, Any] | None = None
    details: Mapping[str, Any] = field(default_factory=dict)
    cause: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "location", _freeze_mapping(self.location))
        object.__setattr__(self, "details", _freeze_mapping(self.details) or {})

    def to_dict(self) -> dict[str, Any]:
        """Returns the JSON value of the diagnostic."""
        return {
            "code": self.code,
            "severity": self.severity,
            "phase": self.phase,
            "message": self.message,
            "path": self.path,
            "location": dict(self.location) if self.location is not None else None,
            "details": dict(self.details),
            "cause": self.cause,
        }


class TypcastError(Exception):
    """The base class of every error raised by Typcast."""

    def __init__(
        self,
        message: str,
        diagnostics: Iterable[Diagnostic] = (),
    ) -> None:
        super().__init__(message)
        self.diagnostics: tuple[Diagnostic, ...] = tuple(diagnostics)


class ApiUsageError(TypcastError):
    """Raised when a public API is used with an invalid argument or state."""


class ValidationError(TypcastError):
    """Raised when a value violates the schema or the semantic rules."""


class SerializationError(TypcastError):
    """Raised when JSON cannot be parsed, serialized, or version-matched."""


class ConfigError(TypcastError):
    """Raised when a configuration value is invalid."""


def api_diagnostic(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> Diagnostic:
    """Builds the diagnostic of a misuse of the public API."""
    return Diagnostic(
        code=code,
        severity=SEVERITY_ERROR,
        phase=PHASE_API,
        message=message,
        path=path,
        details=details or {},
    )


def validation_diagnostic(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> Diagnostic:
    """Builds the diagnostic of a validation failure."""
    return Diagnostic(
        code=code,
        severity=SEVERITY_ERROR,
        phase=PHASE_VALIDATION,
        message=message,
        path=path,
        details=details or {},
    )


def serialization_diagnostic(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> Diagnostic:
    """Builds the diagnostic of a serialization failure."""
    return Diagnostic(
        code=code,
        severity=SEVERITY_ERROR,
        phase=PHASE_SERIALIZATION,
        message=message,
        path=path,
        details=details or {},
    )


def config_diagnostic(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> Diagnostic:
    """Builds the diagnostic of an invalid configuration value."""
    return Diagnostic(
        code=code,
        severity=SEVERITY_ERROR,
        phase=PHASE_CONFIG,
        message=message,
        path=path,
        details=details or {},
    )


def raise_api(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    """Raises a public API error that carries a single diagnostic."""
    raise ApiUsageError(
        message,
        (api_diagnostic(code, message, path, details),),
    )


def raise_config(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    """Raises a configuration error that carries a single diagnostic."""
    raise ConfigError(
        message,
        (config_diagnostic(code, message, path, details),),
    )


def raise_validation(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    """Raises a validation error that carries a single diagnostic."""
    raise ValidationError(
        message,
        (validation_diagnostic(code, message, path, details),),
    )


def raise_serialization(
    code: str,
    message: str,
    path: str | None = None,
    details: Mapping[str, Any] | None = None,
) -> None:
    """Raises a serialization error that carries a single diagnostic."""
    raise SerializationError(
        message,
        (serialization_diagnostic(code, message, path, details),),
    )


def with_path(diagnostics: Sequence[Diagnostic], prefix: str) -> tuple[Diagnostic, ...]:
    """Returns the diagnostics with their JSON Pointer paths prefixed."""
    if not prefix:
        return tuple(diagnostics)
    prefixed: list[Diagnostic] = []
    for diagnostic in diagnostics:
        path = diagnostic.path
        if path:
            path = prefix + path
        else:
            path = prefix
        prefixed.append(
            Diagnostic(
                code=diagnostic.code,
                severity=diagnostic.severity,
                phase=diagnostic.phase,
                message=diagnostic.message,
                path=path,
                location=diagnostic.location,
                details=diagnostic.details,
                cause=diagnostic.cause,
            )
        )
    return tuple(prefixed)
