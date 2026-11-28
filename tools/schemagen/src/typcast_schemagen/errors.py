"""The errors of the schema generator."""

from __future__ import annotations

__all__ = ["SchemagenError"]


class SchemagenError(Exception):
    """Raised when a schema bundle cannot be read or embedded."""
