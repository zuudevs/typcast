"""The schema version of the document IR.

The version follows `docs/specifications/compatibility.md`: a reader supports
the same major version, a minor version less than or equal to its own, and
any patch version of the supported minor.
"""

from __future__ import annotations

import math
import re

from typcast.diagnostics import (
    CODE_UNSUPPORTED_VERSION,
    raise_serialization,
)

__all__ = [
    "SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_MAJOR",
    "SUPPORTED_SCHEMA_MINOR",
    "__version__",
    "parse_schema_version",
    "check_schema_version",
]

# The version of the Python package. It matches the version of the package
# manifest, and the repository gate checks that the two agree.
__version__ = "0.1.0"

SCHEMA_VERSION = "1.0.0"
SUPPORTED_SCHEMA_MAJOR = 1
SUPPORTED_SCHEMA_MINOR = 0

# The pattern holds the ASCII digits only, and the match covers the whole
# text. The `\d` of Python matches every Unicode decimal digit, and a `$`
# matches before a final newline, so a version that the TypeScript SDK
# rejects would pass here.
_VERSION_PATTERN = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")


def _version_component(digits: str) -> float:
    """Returns a version component in the number domain of the IR.

    A component is a number of the IR, so it lives in the binary64 domain of
    ECMAScript. The conversion of a long digit string to an integer is
    limited by the interpreter, while the conversion to a float is not, and
    such a number is an infinity in that domain. The TypeScript SDK reads the
    same value, so both SDKs accept and reject the same versions.
    """
    try:
        return float(digits)
    except OverflowError:
        return math.inf


def parse_schema_version(value: str) -> tuple[float, float, float]:
    """Returns the major, minor, and patch numbers of a version string."""
    match = _VERSION_PATTERN.fullmatch(value)
    if match is None:
        raise_serialization(
            CODE_UNSUPPORTED_VERSION,
            f"'schemaVersion' must be a semantic version, got {value!r}.",
            "/schemaVersion",
            {"value": value},
        )
    major, minor, patch = match.groups()
    return (
        _version_component(major),
        _version_component(minor),
        _version_component(patch),
    )


def check_schema_version(value: str) -> tuple[float, float, float]:
    """Returns the version numbers of a supported version string."""
    if not isinstance(value, str):
        raise_serialization(
            CODE_UNSUPPORTED_VERSION,
            "'schemaVersion' must be a string.",
            "/schemaVersion",
        )
    major, minor, _patch = parse_schema_version(value)
    if major != SUPPORTED_SCHEMA_MAJOR or minor > SUPPORTED_SCHEMA_MINOR:
        raise_serialization(
            CODE_UNSUPPORTED_VERSION,
            f"'schemaVersion' {value!r} is not supported; this SDK reads "
            f"{SUPPORTED_SCHEMA_MAJOR}.{SUPPORTED_SCHEMA_MINOR}.x.",
            "/schemaVersion",
            {
                "value": value,
                "supportedMajor": SUPPORTED_SCHEMA_MAJOR,
                "supportedMinor": SUPPORTED_SCHEMA_MINOR,
            },
        )
    return major, minor, _patch
