"""The instance validation of the document IR against the JSON Schema contract.

The package holds a validator for the subset of JSON Schema 2020-12 that the
schema contract of the document IR uses. The contract itself is embedded in
the SDK as a generated source file, so an instance is checked against the
same documents that the release publishes, and the SDK needs no file of the
repository at run time.
"""

from typcast.schema.schemas_generated import SCHEMAS
from typcast.schema.validator import (
    ANNOTATION_KEYWORDS,
    ASSERTION_KEYWORDS,
    SCHEMA_ROOT,
    schema_keywords,
    validate_schema,
)

__all__ = [
    "ANNOTATION_KEYWORDS",
    "ASSERTION_KEYWORDS",
    "SCHEMAS",
    "SCHEMA_ROOT",
    "schema_keywords",
    "validate_schema",
]
