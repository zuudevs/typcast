"""The schema version of the document IR.

The version follows `docs/specifications/compatibility.md`: a reader supports
the same major version, a minor version less than or equal to its own, and
any patch version of the supported minor.
"""

from __future__ import annotations

import re

from typcast.diagnostics import (
    CODE_UNSUPPORTED_VERSION,
    raise_serialization,
)

__all__ = [
    "SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_MAJOR",
    "SUPPORTED_SCHEMA_MINOR",
    "parse_schema_version",
    "check_schema_version",
]

SCHEMA_VERSION = "1.0.0"
SUPPORTED_SCHEMA_MAJOR = 1
SUPPORTED_SCHEMA_MINOR = 0

# The pattern holds the ASCII digits only, and the match covers the whole
# text. The `\d` of Python matches every Unicode decimal digit, and a `$`
# matches before a final newline, so a version that the TypeScript SDK
# rejects would pass here.
_VERSION_PATTERN = re.compile(r"([0-9]+)\.([0-9]+)\.([0-9]+)")


def parse_schema_version(value: str) -> tuple[int, int, int]:
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
    return int(major), int(minor), int(patch)


def check_schema_version(value: str) -> tuple[int, int, int]:
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
