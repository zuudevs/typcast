"""The semantic validation engine of the Python SDK.

The engine checks the rules of the document IR that span more than one node:
the shape of a table, the uniqueness of a module alias, and the size of a raw
node. It reports every problem it finds and raises no error for a semantic
problem.
"""

from typcast.validations.config import (
    DEFAULT_MAX_RAW_BYTES,
    TypcastConfig,
)
from typcast.validations.engine import validate_document

__all__ = [
    "DEFAULT_MAX_RAW_BYTES",
    "TypcastConfig",
    "validate_document",
]
